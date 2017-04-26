#!/usr/bin/env python
# -*- coding: utf-8 -*-
#python filter.py -i "u:hoststats-alerts,u:haddrscan-alerts"
import logging
import json
import sys
import os
import pika
#import ssl
import argparse
import cmd
import math
import random
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from os.path import dirname as dirn
import glob
import pytz
import shutil
import threading
import ipaddress
import time
from mapping import Mapping
from time_machine_capture import Capture, Sock
from datetime import datetime, timedelta #, timezone
from math import log

first = lambda h: 2**h - 1      # H stands for level height
last = lambda h: first(h + 1)
level = lambda heap, h: heap[first(h):last(h)]
prepare = lambda e, field: str(e).center(field)


DEBUG = False

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='(%(threadName)-10s) %(message)s',
# )
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class MyJson:
    #MyJson.load_json_file_with_comments('file')
    ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))
    @classmethod
    def load_json_file_with_comments(cls,filename):
        filename = os.path.normpath(cls.ROOT_PATH + "/" + filename)
        try:
            with open(filename) as data_file:
                input_str = re.sub(r'\\\n', '', data_file.read())
                input_str = re.sub(r'#.*\n', '\n', input_str)
                return json.loads(input_str)
        except IOError:
            print("Wrong file or file path",filename)
        except ValueError:
            print "Invalid json",filename
        except Exception as e:
            print e

class FolderDispatcher(threading.Thread):
    # logging.basicConfig(filename="example.log",level=logging.DEBUG)
    ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))
    JSONS_PATH = ROOT_PATH + '/jsons/'
    JSONS_PROCESSED_PATH = ROOT_PATH + '/jsons/processed/'
    JSONS_ERROR_PROCESSED_PATH = ROOT_PATH + '/jsons/error_processed/'


    def __init__(self, shared_array, event, json_path, mapping_cfg):
        threading.Thread.__init__(self)
        self.shared_array = shared_array
        self.shared_thread_event = event
        self.daemon = True
        self.JSONS_PATH = os.path.normpath(self.ROOT_PATH + "/" + json_path)
        self.m = Mapping(mapping_cfg)
        self.mapping_cfg = mapping_cfg
        print("FolderDispatcher JSON PATH: " + self.JSONS_PATH)

    def run(self):
        logging.debug('running FolderDispatcher')
        self.folder_dispatcher()

    def reload_cfg(self):
        self.m = Mapping(self.mapping_cfg)

    def move_to_folder(self, src_path, dst_directory):
        if(DEBUG == False):
            #print("removing {}".format(src_path))
            if os.path.exists(src_path):
                os.remove(src_path)
            return

        if not os.path.exists(dst_directory):
            os.makedirs(dst_directory)

        filename = os.path.basename(src_path)
        dst_path = "{}{}".format(dst_directory, filename)
        shutil.move(src_path, dst_path)

    def move_to_processed_folder(self, path):
        return self.move_to_folder(path, self.JSONS_PROCESSED_PATH)

    def move_to_error_folder(self, path):
        return self.move_to_folder(path, self.JSONS_ERROR_PROCESSED_PATH)

    def folder_dispatcher(self):
        while True:

            #use relative path instad of absolute
            for filename in glob.glob(os.path.join(self.JSONS_PATH, '*.json')):
                #if size == 0, there is no data in file
                #generator only created file .. no dumped data!!!
                statinfo = os.stat(filename)
                if statinfo.st_size == 0: continue
                with open(filename) as data_file:
                    try:
                        data = json.load(data_file)
                        idea_alert = self.m.map_alert_to_hash(data)
                        da_alert = AlertExtractor.parse_alert(idea_alert)
                        self.move_to_processed_folder( filename )
                        if da_alert is None:
                            continue
                        else:
                            self.shared_array.append( da_alert )
                    except Exception as e:
                        logging.error("for file: {} error: {}".format(filename,e))
                        print("for file: {} error: {}".format(filename,e))
                        #self.move_to_error_folder(filename)
                self.shared_thread_event.set()
            time.sleep(1)
class RabbitMqDispatcher(threading.Thread):
    def __init__(self, shared_array, event, dispatcher_options_array, mapping_cfg):
        self.m = Mapping(mapping_cfg)
        self.mapping_cfg = mapping_cfg
        threading.Thread.__init__(self)
        self.shared_array = shared_array
        self.daemon = True
        self.shared_thread_event = event
        self.dispatcher_options_array = dispatcher_options_array
        print("self.dispatcher_options_array: ", self.dispatcher_options_array)

    def reload_cfg(self):
        self.m = Mapping(self.mapping_cfg)

    def run(self):
        self.idea_dispatcher()

    def idea_dispatcher(self):
        # ssl_options = {
        #     "ca_certs":"/Users/adamplansky/Desktop/message_app/testca/cacert.pem",
        #     "certfile": "/Users/adamplansky/Desktop/message_app/client/cert.pem",
        #     "keyfile": "/Users/adamplansky/Desktop/message_app/client/key.pem",
        #     "cert_reqs": ssl.CERT_REQUIRED,
        #     "ssl_version":ssl.PROTOCOL_TLSv1_2
        # }
        xhost, xport, xusername, xpassword = self.dispatcher_options_array
        credentials = pika.PlainCredentials(xusername, xpassword)
        #parameters = pika.ConnectionParameters(host='192.168.2.120', port=5671, virtual_host='/', heartbeat_interval = 0, credentials=credentials, ssl = True, ssl_options = ssl_options)
        parameters = pika.ConnectionParameters(host=xhost, port=xport, virtual_host='/', credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # ''' start subscriber '''

        channel.exchange_declare(exchange='broadcast_idea', exchange_type='fanout') #fanout == type broadcast #exchange == name
        result = channel.queue_declare(exclusive=True) #i want random name of queue, exlusive == true, when we disconnect delete queue
        queue_name = result.method.queue
        channel.queue_bind(exchange='broadcast_idea', queue=queue_name)
        print(' [*] Waiting for ideas. To exit press CTRL+C')

        def callback(ch, method, properties, body):
            data = json.loads(json.loads(body.decode("utf-8")))
            #print("data: ",data,data.__class__)
            idea_alert = self.m.map_alert_to_hash(data)
            #print("idea_alert: ",idea_alert)
            da_alert = AlertExtractor.parse_alert(idea_alert)
            if da_alert is not None:
                self.shared_array.append( da_alert )
                self.shared_thread_event.set()
        channel.basic_consume(callback, queue=queue_name, no_ack=True)
        channel.start_consuming()


class AlertExtractor:
    @classmethod
    def parse_datetime(cls, datetime_string):
        #todo: not nice
        local_tz = pytz.timezone ("UTC")
        return local_tz.localize(datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ'))

    @classmethod
    def append_valid_ips(cls, ary):
        arr = []
        for val in ary:
            try:
                ip = ipaddress.ip_address(val)
                if ip.is_global: arr.append(val)
            except Exception as e:
                logging.error("ip address error: {}".format(e))
        return arr

    @classmethod
    def parse_ips(cls, event):
        #todo: rewrite
        source_ips = []; target_ips = []
        if(event["SourceIP4"]):
            source_ips += cls.append_valid_ips(event["SourceIP4"])
        if(event["SourceIP6"]):
            source_ips += cls.append_valid_ips(event["SourceIP6"])

        if(event["TargetIP6"]):
            target_ips += cls.append_valid_ips(event["TargetIP6"])
        if(event["TargetIP4"]):
            target_ips += cls.append_valid_ips(event["TargetIP4"])

        return [source_ips, target_ips]

    @classmethod
    def parse_category(cls, alert):
        return alert["Category"]

    @classmethod
    def parse_time(cls, alert):
        return cls.parse_datetime(alert["DetectTime"])

    @classmethod
    def parse_node(cls, alert):
        return [x["Name"] for x in alert["Node"]]

    @classmethod
    def dissassemble_alert(cls, alert):
        return {"ips": cls.parse_ips(alert),
                "time": cls.parse_time(alert),
                "node": cls.parse_node(alert),
                "category": cls.parse_category(alert)}

    @classmethod
    def parse_alert(cls, alert):
        if "Test" in alert["Category"]: return None
        return cls.dissassemble_alert(alert)

class AlertDatabase:
    ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))

    def __init__(self, cfg_path, probability_db_file):
        self.database = {}
        self.database_cfg = defaultdict(dict)
        self.alert_probability = defaultdict(float)
        self.CFG_JSON_PATH = os.path.normpath(self.ROOT_PATH + "/" + cfg_path)
        self.PROBABILITY_DB_FILE = os.path.normpath(self.ROOT_PATH + "/" + probability_db_file)
        self.load_cfg()
        self.load_probability()

    #☑️ TESTED
    def load_probability(self):
        filename = self.PROBABILITY_DB_FILE

        if os.path.isfile(filename):
            self.alert_probability = defaultdict(float)
            with open(filename) as data_file:
                json_dict = json.load(data_file)
                for k, v in json_dict.iteritems():
                    self.alert_probability[k] = v

    #☑️ TESTED
    def reload_cfg(self):
        self.database_cfg = defaultdict(dict)
        self.load_cfg()


    def get_most_significant_category_from_array(self, category_ary):
        max_score = 0
        max_category = ""
        for category in category_ary:
            score = self.get_static_price(category)
            if max_score < score:
                max_score = score
                max_category = category
        return max_category


    #☑️ TESTED
    def get_static_price_from_cfg(self, category):
        try:
            return self.database_cfg[category]["Score"]
        except Exception:
            #todo: log this in config / send email with json alert
            return self.database_cfg["Default"]["Score"]

    #☑️ TESTED
    def get_static_price(self, category):
        category_score = 0
        if type(category) is list:
            for cat in category:
                category_score = max(self.get_static_price_from_cfg(cat),category_score)
        else:
            category_score = max(self.get_static_price_from_cfg(category),category_score)
        return category_score

    #☑️ TESTED
    def get_category_with_max_score_from_last_alert(self,ip):
        categories = self.get_last_category_array(ip)
        print categories
        best_category = ""; best_score = 0
        if type(categories) is list:
            for category in categories:
                score = self.get_static_price_from_cfg(category)
                if score > best_score:
                    best_score = score
                    best_category = category
        else:
            best_category = categories
        return best_category

    def load_cfg(self):
        with open(self.CFG_JSON_PATH) as data_file:
            data = json.load(data_file)
            for cfg_line_dict in data:
                self.load_cfg_recursion(cfg_line_dict, self.database_cfg)

    def load_cfg_recursion(self,dict_in, dict_out,key_acc=""):
        for key, val in dict_in.items():
            if not isinstance(val,dict):
                dict_out[key_acc][key] = val
            else:
                k = (key_acc + "." + key if len(key_acc) > 0 else key)
                self.load_cfg_recursion(val, dict_out,k)
    @classmethod
    def get_time_machine_direction(cls,direction):
        #todo predelat to na enum??
        #wtf proc tam je BS a BT a BB
         return {
             'S':"src_ip",
             'T':"dst_ip",
             'BS':"bidir_ip",
             'BT':"bidir_ip",
             'BB':"bidir_ip",
             }.get(direction)

    def get_capture_params(self, ip):
        sources = []; targets = [];
        last_alert = self.get_last_alert_event(ip)
        if last_alert is None: return
        if ip[0] == "S":
            sources.append(ip)
            targets.append(last_alert[3])
        else:
            targets.append(ip)
            sources.append(last_alert[3])
        default_parameters = self.database_cfg["Default"]
        categories = self.get_last_category_array(ip)
        category = self.get_most_significant_category_from_array(categories)
        if len(category) > 0 :
            default_parameters.update(self.database_cfg[category])
        capture_parameters = {
            "direction": AlertDatabase.get_time_machine_direction(default_parameters["Direction"]),
            "packets":  default_parameters["Packets"],
            "timeout":  default_parameters["Timeout"],
            "category":  category
            }
        capture_requests = []
        if default_parameters["Direction"] in ["S","BS","BB"]:
            for source_ip in sources:
                capture_parameters["ip_addr"] = source_ip
                capture_requests.append(capture_parameters)
        if default_parameters["Direction"] in ["T","BT","BB"]:
            for target_ip in targets:
                capture_parameters["ip_addr"] = target_ip
                capture_requests.append(capture_parameters)

        print(capture_requests)
        return capture_requests



    #☑️ TESTED
    def get_ip_prefix(self, ips):
        ip_ary = []
        if(len(ips[0]) > 0):
            ip_ary.append(map((lambda x: "S"+x), ips[0]))
        else:
            ip_ary.append([])
        if(len(ips[1]) > 0):
            ip_ary.append(map((lambda x: "T"+x), ips[1]))
        else:
            ip_ary.append([])
        return ip_ary


    # def get_max_score(self,ip):
    #     if not ip in self.database: return 0
    #     return max([x[1] for x in self.database[ip]])

    #☑️ TESTED
    def get_category_cnt_by_ip(self, ip, category):
        if ip in self.database and category in self.database[ip]:
            return self.database[ip][category]
        return 0

    #☑️ TESTED
    def get_categories_by_alert_index(self,ip,idx):
        if ip in self.database:
            return self.database[ip]["alerts"][idx][1]

    #☑️ TESTED
    def get_last_category_array(self, ip):
        category = []
        if(ip in self.database and len(self.database[ip]["alerts"]) > 0):
            #category = self.database[ip]["alerts"][-1][1]
            category = self.get_categories_by_alert_index(ip, -1)
        return category

    #☑️ TESTED
    def get_last_score(self,ip):
        if(ip in self.database and len(self.database[ip]["alerts"]) > 0):
            return self.get_static_price(self.get_last_category_array(ip))
        return -1

    #☑️ TESTED
    def get_last_alert_event(self, ip):
        if(ip in self.database and len(self.database[ip]["alerts"]) > 0):
            return self.database[ip]["alerts"][-1]
        return None


    def print_database(self):
        print("-----DATABASE-----")
        for key, value in self.database.items() :
            print ("{} -> {}".format(key,value))
        print("-----DATABASE-----")

    #☑️ TESTED
    def add_to_probability_database(self,categories):
        for category in categories:
            self.alert_probability[category] += 1
            self.alert_probability["cnt"] += 1

        print(self.alert_probability["cnt"], self.PROBABILITY_DB_FILE)
        if self.alert_probability["cnt"] % 1000 == 0:
             with open(self.PROBABILITY_DB_FILE, 'w') as data_file:
                 j = json.dumps(self.alert_probability)
                 print >> data_file, j
        return self.alert_probability

    #☑️ TESTED
    def get_probability_by_category(self, category):
        return self.alert_probability[category] / self.alert_probability["cnt"]

    #❌ otestovat
    def recalculate_cnt_hour(self, ip):
        #todo: otestovat
        date_min = datetime.now(pytz.timezone("UTC")) - timedelta(hours=1)
        for idx, da_alert in enumerate(self.database[ip]["alerts"]):
            if(date_min > da_alert[0]):
                categories = self.get_categories_by_alert_index(ip, idx)
                for category in categories:
                    self.database[ip][category] -= 1
                self.database[ip]["cnt"] -= 1
                del self.database[ip]["alerts"][idx]



    def parse_category_to_ip(self, ip, category_ary):
        #globalni citac category -> musim i odebirat
        if ip not in self.database:
            return

        for category in category_ary:
            if category not in self.database[ip]: self.database[ip][category] = 0
            self.database[ip][category] += 1

        return self.database[ip]



    def database(self):
        return self.database

    def add(self,da_alert):
        #print("da_alert: ", da_alert)
        if da_alert is None: return
        ips = self.get_ip_prefix(da_alert["ips"])
        source_ips = ips[0]; target_ips = ips[1]
        ips_to_return = source_ips + target_ips
        print("source_ips: {}, target_ips: {}, category: {}".format(source_ips, target_ips, da_alert["category"]))
        self.add_to_probability_database(da_alert["category"]) #pocita celkovou pravepodoost vyskytu
        for i in range(0,2):
            next_ary = ips[(i + 1) % 2]

            for ip in ips[i]:
                minor_ips_ary = next_ary
                if not ip in self.database: self.database[ip] = {"cnt": 0, "alerts": []}
                self.database[ip]["alerts"].append([
                                          da_alert["time"],
                                          da_alert["category"],
                                          da_alert["node"],
                                          minor_ips_ary
                                         ])
                self.database[ip]["cnt"] += 1
                self.parse_category_to_ip(ip, da_alert["category"]) #pridava citac categorije k prislusnemu alertu

                self.recalculate_cnt_hour(ip)

        #self.print_database()
        return ips_to_return
class Score():
    #ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))
    #☑️ TESTED
    TRESHOLD_SCANS = 2

    #☑️ TESTED
    @classmethod
    def __init__(cls, cfg_path):
        cls.file_path = cfg_path
        cls.modulo = 100;
        cls.p = 95;
        cls.limit = 500
        cls.load_cfg()

    #☑️ TESTED
    @classmethod
    def load_cfg(cls):
        d = MyJson.load_json_file_with_comments(cls.file_path)
        print("d:",d)
        cls.modulo = d["every"]
        cls.p = d["every"] - d["first"]
        cls.limit = d["limit"]

    #☑️ TESTED
    @classmethod
    def scan_params(cls):
        return cls.p, cls.modulo, cls.limit

    #☑️ TESTED
    @classmethod
    def signum(cls,value):
        return math.copysign(1, value)

    #☑️ TESTED
    @classmethod
    def score_func(cls, score, probability):
        return math.pow(2, score - 1) * (1 - probability) + math.pow(2, score - 1)

    #☑️ TESTED
    @classmethod
    def get_score(cls, hour_number, score, probability):
        return cls.signum(-hour_number+3) * cls.score_func(score, probability)

    #☑️ TESTED
    @classmethod
    def scan_is_important(cls,cnt):
        if ( (cnt + cls.p) % cls.modulo) == 0:
            return True
        return False

class Filter(threading.Thread):
    ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))
    def __init__(self,argv_param, dispatcher_options, alert_database_cfg, mapping_cfg, time_machine_params, scan_alg_params_cfg, probability_db_file):
        threading.Thread.__init__(self)
        self.shared_array = list()
        self.shared_thread_event = threading.Event()
        self.argv_param = argv_param
        self.alert_database = AlertDatabase(alert_database_cfg, probability_db_file)
        self.global_filter_cnt = 0
        self.global_capture_filter_cnt = 0
        self.dispatcher_options = dispatcher_options
        self.mapping_cfg = mapping_cfg
        self.time_machine_params = time_machine_params
        self.cfg_scan_alg_params = os.path.normpath(self.ROOT_PATH + "/" + scan_alg_params_cfg)
        Score.__init__(scan_alg_params_cfg)
        CaptureRequest(self.time_machine_params)
        self.fd = None
        self.daemon = True





    def reload_cfg(self):
        if self.fd:
            self.fd.reload_cfg()
        if self.alert_database:
            self.alert_database.reload_cfg()
        Score.load_cfg()

    def run(self):
        self.run_filter()

    def run_filter(self):
        logging.debug('running Filter')
        print("self.argv_param:", self.argv_param)
        if self.argv_param == '-f':
            self.fd = FolderDispatcher(self.shared_array,self.shared_thread_event, self.dispatcher_options[0], self.mapping_cfg)
        elif self.argv_param == '-RMQ':
            self.fd = RabbitMqDispatcher(self.shared_array,self.shared_thread_event, self.dispatcher_options, self.mapping_cfg)
        self.fd.start()
        self.calculate_price()
        #self.fd.join()


    def calculate_price(self):
        while True:
            if len(self.shared_array) == 0:
                self.shared_thread_event.clear()
                self.shared_thread_event.wait() # wait until self.shared_thread_event == True

            else:
                idea_alert = self.shared_array.pop()
                #idea alert obsahuje vice pole ip address
                #pridam to do databaze a vratim jaky adresy to jsou
                print("calculate_price:", idea_alert)
                ips = self.alert_database.add(idea_alert)
#                print("PRINT: ",idea_alert, ips)
                for ip in ips:

                    to_capture = False
                    score = self.alert_database.get_last_score(ip)
                    self.global_filter_cnt += 1
                    category = self.alert_database.get_category_with_max_score_from_last_alert(ip)

                    probability = self.alert_database.get_probability_by_category(category)
                    cnt_hour = self.alert_database.get_category_cnt_by_ip(ip,category)
                    price = self.alert_database.get_static_price(category)
                    score = Score.get_score(cnt_hour, price, probability)
                    #category_hour_number = self.alert_database.get_category_with_max_score_from_last_alert(ip)

                    if price < Score.TRESHOLD_SCANS and (Score.scan_is_important(cnt_hour) or random.randint(1, 250) == 42 ):
                        #score < Score.TRESHOLD_SCANS == port scans
                        score = 1
                        to_capture = True
                    else:
                        to_capture = True


                    if cnt_hour > 500:
                        #pokud se neco zblazni, tak to nezachytavej
                        to_capture = False


                    if(to_capture == True and score >= 1):
                        #posli pozadavek o zachyt
                        CaptureRequest.send(self.alert_database.get_capture_params(ip))
                        self.global_capture_filter_cnt += 1
                        print(bcolors.WARNING +  "{}/{}".format(self.global_capture_filter_cnt,self.global_filter_cnt ) + bcolors.ENDC)
                    #else:
                        #print("Capture requirments: " +bcolors.WARNING +  "Not satisfied" + bcolors.ENDC)


class CaptureRequest():
    init_call = True
    @classmethod
    def __init__(cls, params):
        cls.max_simultaneously_captures = 50
        cls.simultaneously_captures = 0
        cls.capture_database = {}
        cls.init_call = False
        cls.addr_info = params
        print("CaptureRequest INIT: ", cls.addr_info)

    @classmethod
    def send(cls, capture_requests):
        for capture_request in capture_requests:
            print(capture_request["ip_addr"][1:])
        if(cls.init_call != False): cls.__init__()
        if not cls.connection_is_established():
            cls.connect_to_time_manager()

        if cls.connection_is_established():
            for capture_request in capture_requests:
                print(bcolors.HEADER + "Time machine manager: ON" +bcolors.ENDC + "\n" + bcolors.OKGREEN + "{} {} {} {} {}".format(capture_request["direction"], capture_request["ip_addr"][1:], ("{}_{}".format(capture_request["category"],capture_request["ip_addr"])), capture_request["packets"], capture_request["timeout"]) + bcolors.ENDC)
                Capture.do_add("{} {} {} {} {}".format(capture_request["direction"], capture_request["ip_addr"][1:], ("{}_{}".format(capture_request["category"],capture_request["ip_addr"])), capture_request["packets"], capture_request["timeout"]))
        else:
            print(bcolors.HEADER + "Time machine manager: OFF" +bcolors.ENDC + "\n" +bcolors.OKGREEN + "{} {} {} {} {}".format(capture_request["direction"], capture_request["ip_addr"][1:], ("{}_{}".format(capture_request["category"],capture_request["ip_addr"])), capture_request["packets"], capture_request["timeout"]) + bcolors.ENDC)
            #print(bcolors.OKGREEN + "Capture Request => ip: {}, direction: {}. packets: {}, seconds: {}".format(ip, direction, 10000, 300) + bcolors.ENDC)
            #Capture.do_add("{} {} {} {} {}".format(direction, ip, "XYZA", 10000, 500))
            #Capture.do_list("")
            #Capture.do_remove("{} {}".format(direction, ip))
            #Capture.do_list("")

    @classmethod
    def get_list(cls):
        pass

    @classmethod
    def remove_ip_from_capture(cls,ip):
        #do_remove(args) => args[0] = direciton, args[1] = ip
        #Catpure.do_redmove(args)
        pass


    @classmethod
    def connection_is_established(cls):
        return Sock.connect() > 0

    @classmethod
    def connect_to_time_manager(cls):
        Sock.add_probes(cls.addr_info)


class Shell(cmd.Cmd):
    def __init__(self, filter):
        cmd.Cmd.__init__(self)
        self.filter = filter
        self.prompt = 'filter> '
        self.active_t = False

    def do_exit(self,args):
        print("exiting filter")
        return True

    def do_start(self,args):
        if self.active_t == False:
            self.filter.start()
            self.active_t = True

    def do_reload_config(self,args):
        self.filter.reload_cfg()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    #parser.add_argument("num", help="The Fibonacci number you wish to calculate.", type=int)
    parser.add_argument("-v", "--verbose", help="Verbose output.", default="false")
    parser.add_argument("-f", "--folder", help="All input json files are taken from ../jsons/ folder if is not specified with -fp parameter", action="store_true")
    parser.add_argument("-fp", "--folder_path", help="Folder path from where are json files taken", action="store", default="../jsons/")
    parser.add_argument("-RMQ", "--RabbitMQ", help="All input json files sare taken from rabbitmq server", action="store_true")
    parser.add_argument("-RMQhostname", "--RabbitMQ_hostname", help="RabbitMQ hostname", action="store", default="localhost")
    parser.add_argument("-RMQport", "--RabbitMQ_port", help="RabbitMQ port", action="store", default=5672, type=int)
    parser.add_argument("-RMQusername", "--RabbitMQ_username", help="RabbitMQ username", action="store", default='guest')
    parser.add_argument("-RMQpassword", "--RabbitMQ_password", help="RabbitMQ password", action="store", default='guest')
    parser.add_argument("-tmm", "--time_machine_manager", help="All output is sent to time machine manager.", action="store_true")
    parser.add_argument("-tmm_hostname", "--time_machine_manager_hostname", help="Time machine manager hostname.", action="store", default="localhost")
    parser.add_argument("-tmm_port", "--time_machine_manager_port", help="Time machine manager port.", action="store", default=37564, type=int)
    parser.add_argument("-no_tmm", "--no_time_machine_manager", help="Time machine manager is disable, all filter output will be printed only to STDOUT", action="store_true")
    parser.add_argument("-cfg_mapping", help="Path to mapping config", action="store", default="../config/mapping")
    parser.add_argument("-cfg", help="Path to config", action="store", default="../config/static_prices.json")
    parser.add_argument("-cfg_scan_algorithm_parameters", help="Path to scan algorithm parameters", action="store", default="../config/scan_algorithm_parameters")
    parser.add_argument("-probability_db_file", help="Path to database file for probability", action="store", default="../config/probability_db")

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    dispatcher_options = []
    filter = None
    xarg = ""
    if args.RabbitMQ:
        dispatcher_options.append(args.RabbitMQ_hostname)
        dispatcher_options.append(args.RabbitMQ_port)
        dispatcher_options.append(args.RabbitMQ_username)
        dispatcher_options.append(args.RabbitMQ_password)
        xarg = args.RabbitMQ
        xarg = "-RMQ"
    elif args.folder:
        dispatcher_options.append(args.folder_path)
        xarg = "-f"


    if args.time_machine_manager:
        tmm_params = [args.time_machine_manager_hostname, args.time_machine_manager_port]
    else:
        tmm_params = []
    filter = Filter(xarg, dispatcher_options, args.cfg, args.cfg_mapping, tmm_params, args.cfg_scan_algorithm_parameters, args.probability_db_file)
    Shell(filter).cmdloop()
    # filter = Filter(xarg, dispatcher_options, args.cfg, args.cfg_mapping, tmm_params).run_filter()
    exit()

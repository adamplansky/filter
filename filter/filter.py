#!/usr/bin/env python
#python filter.py -i "u:hoststats-alerts,u:haddrscan-alerts"
import logging
import json
import sys
import os
import pika
import ssl
import argparse
import cmd

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
import heapq
from datetime import datetime, timedelta #, timezone
from math import log

first = lambda h: 2**h - 1      # H stands for level height
last = lambda h: first(h + 1)
level = lambda heap, h: heap[first(h):last(h)]
prepare = lambda e, field: str(e).center(field)


DEBUG = False

def hprint(heap, width=None):
    if width is None:
        width = max(len(str(e)) for e in heap)
    height = int(log(len(heap), 2)) + 1
    gap = ' ' * width
    for h in range(height):
        below = 2 ** (height - h - 1)
        field = (2 * below - 1) * width
        print(gap.join(prepare(e, field) for e in level(heap, h)))
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
    def extract_ip_and_direction(cls, dir_and_ip):
        return dir_and_ip[:1], dir_and_ip[1:]

    @classmethod
    def parse_datetime(cls, datetime_string):
        #todo: not nice
        local_tz = pytz.timezone ("UTC")
        return local_tz.localize(datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ'))

    @classmethod
    def get_detect_time(cls, alert):
        return cls.parse_datetime(alert["DetectTime"])

    @classmethod
    def get_cease_time(cls, alert):
        return cls.parse_datetime(alert["CeaseTime"])

    @classmethod
    def append_valid_ips(cls, ary):
        #todo: what if '217.31.192.0/20'
        #'TargetIP4': ['217.31.192.0/20']
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

    # @classmethod
    # def parse_score(cls, alert):
    #     return max(map(Price.get_static_price,alert["Category"]))

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

    def __init__(self, cfg_path):
        self.database = {}
        self.database_cfg = defaultdict(dict)
        self.CFG_JSON_PATH = os.path.normpath(self.ROOT_PATH + "/" + cfg_path)
        self.load_cfg()

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

    def get_static_price(self, category):
        try:
            #print(category, self.database_cfg[category])
            return self.database_cfg[category]["Score"]
        except Exception:
            #todo: log this in config / send email with json alert
            return self.database_cfg["Default"]["Score"]

    def load_cfg_recursion(self,dict_in, dict_out,key_acc=""):
        for key, val in dict_in.items():
            if not isinstance(val,dict):
                dict_out[key_acc][key] = val
            else:
                k = (key_acc + "." + key if len(key_acc) > 0 else key)
                self.load_cfg_recursion(val, dict_out,k)
    @classmethod
    def get_time_machine_direction(cls,direction):
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


    def load_cfg(self):
        with open(self.CFG_JSON_PATH) as data_file:
            data = json.load(data_file)
            for cfg_line_dict in data:
                self.load_cfg_recursion(cfg_line_dict, self.database_cfg)
        #print(self.database_cfg)

    def get_ip_prefix(self, ips):
        print("get ip prefix", ips)
        if(len(ips) == 0 ): return None,[]
        if(len(ips[0]) > 0): return "S", ips[0]
        if(len(ips[1]) > 0): return "T", ips[1]
        return None,[]

    def get_ip_prefix_1(self, ips):
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


    def get_max_score(self,ip):
        #todo: check if it works
        #probably some test is needed
        return max([x[1] for x in self.database[ip]])

    def get_last_category_array(self, ip):
        category = []
        if(len(self.database[ip]["alerts"]) > 0):
            category = self.database[ip]["alerts"][-1][1]
        return category


    def get_last_score(self,ip):
        if(len(self.database[ip]["alerts"]) > 0):
            return self.get_static_price(self.get_last_category_array(ip))
        return -1

    def get_last_alert_event(self, ip):
        if(len(self.database[ip]["alerts"]) > 0):
            return self.database[ip]["alerts"][-1]
        return None



    def print_database(self):
        print("-----DATABASE-----")
        for key, value in self.database.items() :
            print ("{} -> {}/{}".format(key,value["cnt"]))
        print("-----DATABASE-----")

    # def get_cnt_hour(self, ip):
    #     return self.database[ip]["cnt_hour"]

    def get_cnt(self, ip):
        return self.database[ip]["cnt"]

    def recalculate_cnt_hour(self, ip):
        date_min = datetime.now(pytz.timezone("UTC")) - timedelta(hours=1)
        for idx, da_alert in enumerate(self.database[ip]["alerts"]):
            if(date_min > da_alert[0]):
                del self.database[ip]["alerts"][idx]

    def database(self):
        return self.database

    def add(self,da_alert):
        #print("da_alert: ", da_alert)
        if da_alert is None: return
        ips = self.get_ip_prefix_1(da_alert["ips"])
        source_ips = ips[0]; target_ips = ips[1]
        ips_to_return = source_ips + target_ips
        print("source_ips: {}, target_ips: {}, category: {}".format(source_ips, target_ips, da_alert["category"]))
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
                self.recalculate_cnt_hour(ip)

        #self.print_database()
        return ips_to_return

class HeapOutput:
    #how many probes do I have?
    PROBES_CAPACITY = 5
    ROOT_PATH = os.path.realpath(dirn(dirn(os.path.abspath(__file__))))
    JSONS_PROBES_PATH = ROOT_PATH + '/jsons/probes/'
    def __init__(self):
        self.heap = []

    def create_json_threat_file(self, threat):
        json_out = json.dumps(threat)
        if not os.path.exists(self.JSONS_PROBES_PATH):
            os.makedirs(self.JSONS_PROBES_PATH)

        # threat[1] = threat[Ip]
        ip = threat[1]
        threat_file_name = "{}{}.json".format(self.JSONS_PROBES_PATH,ip)
        with open(threat_file_name, 'w') as f:
            f.write(json_out)

    def add(self, threat):
        print("threat:", threat)

        if self.PROBES_CAPACITY > len(self.heap):
            heapq.heappush(self.heap,threat)
            self.create_json_threat_file(threat)
        else:
            pop_val = heapq.heappushpop(self.heap,threat)
            if pop_val != threat:
                self.create_json_threat_file(threat)

        #print('---------------------------------------------------------------')
        #if self.heap: hprint(self.heap)

    def recalculte_price():
        #PRICE.calculate_price
        #

        pass

    def recalculate_all_prices():
        pass
# class Price:
#     ROOT_PATH = os.path.realpath(dirn(dirn(os.path.abspath(__file__))))
#     CFG_JSON_PATH = ROOT_PATH + '/config/static_prices.json'
#
#     MAX_PRICE = 1000
#     # algorithm for price calculation
#     init_call = True
#     cfg_static_prices =  defaultdict(dict)
#     @classmethod
#     def __init__(cls):
#         cls.init_call = False
#         cls.load_cfg()
#
#     @classmethod
#     def load_cfg_recursion(cls,dict_in, dict_out,key_acc=""):
#         for key, val in dict_in.items():
#             if not isinstance(val,dict):
#                 dict_out[key_acc][key] = val
#             else:
#                 k = (key_acc + "." + key if len(key_acc) > 0 else key)
#                 cls.load_cfg_recursion(val, dict_out,k)
#
#     @classmethod
#     def load_cfg(cls):
#         with open(cls.CFG_JSON_PATH) as data_file:
#             data = json.load(data_file)
#             for cfg_line_dict in data:
#                 cls.load_cfg_recursion(cfg_line_dict, cls.cfg_static_prices)
#         print(cls.cfg_static_prices)
#     @classmethod
#     def get_static_price(cls, category):
#         if(cls.init_call != False): cls.__init__()
#         try:
#             print(category, cls.cfg_static_prices[category])
#             return cls.cfg_static_prices[category]["Score"]
#         except Exception:
#             #todo: log this in config / send email with json alert
#             return cls.cfg_static_prices["Default"]["Score"]

    # @classmethod
    # def calculate_price_new(cls, ip_address):
    #     database_row = cls.alert_database.add(ip_address)
    #
    #     return database_row


    # @classmethod
    # def calculate_price(cls, event):
    #     if(cls.init_call != False): cls.__init__()
    #     static_price = 0
    #     for category in event["Category"]:
    #         print("category: {}, price: {}".format(category,cls.get_statis_price(category)))
    #         static_price += cls.cfg_static_prices[category]
    #         print(static_price)


class Filter(cmd.Cmd):
    def __init__(self,argv_param, dispatcher_options, alert_database_cfg, mapping_cfg, time_machine_params):
        cmd.Cmd.__init__(self)
        #threading.Thread.__init__(self)
        self.shared_array = list()
        self.shared_thread_event = threading.Event()
        self.counter = 0
        self.heap_output = HeapOutput()
        self.argv_param = argv_param
        self.alert_database = AlertDatabase(alert_database_cfg)
        self.global_filter_cnt = 0
        self.global_capture_filter_cnt = 0
        self.dispatcher_options = dispatcher_options
        self.mapping_cfg = mapping_cfg
        self.time_machine_params = time_machine_params
        CaptureRequest(self.time_machine_params)
        self.fd = None


    def do_reload_cfg(self, args):
        print("reloading all config files")
        if self.fd:
            self.fd.reload_cfg()
        if self.alert_database:
            self.alert_database.reload_cfg()

    def do_exit(self,args):
        print("exiting!!!")
        return True

    def do_start(self,args):
        self.run_filter()

    def run_filter(self):
        logging.debug('running Filter')
        print("self.argv_param:", self.argv_param)
        if self.argv_param == '-f':
            self.fd = FolderDispatcher(self.shared_array,self.shared_thread_event, self.dispatcher_options[0], self.mapping_cfg)
        elif self.argv_param == '-RMQ':
            self.fd = RabbitMqDispatcher(self.shared_array,self.shared_thread_event, self.dispatcher_options, self.mapping_cfg)
        self.fd.setDaemon(True)  #
        self.fd.start()
        self.calculate_price()
        #self.fd.join()



    def calculate_price(self):
        while True:
            if len(self.shared_array) == 0:
                self.shared_thread_event.clear()
                self.shared_thread_event.wait() # wait until self.shared_thread_event == True

            else:
                self.counter += 1
                idea_alert = self.shared_array.pop()
                #idea alert obsahuje vice pole ip address
                #pridam to do databaze a vratim jaky adresy to jsou
                ips = self.alert_database.add(idea_alert)
#                print("PRINT: ",idea_alert, ips)

                for ip in ips:
                    #todo: cnt_hour pouze pokud add += 1 jinak nic
                    score = self.alert_database.get_last_score(ip)
                    cnt = self.alert_database.get_cnt(ip)
                    #print("get score for ip {} score: {} cnt_hour: {}".format(ip,score, cnt_hour))
                    #print("alert: ", self.alert_database.database[ip])
                    self.global_filter_cnt += 1
                    #print(bcolors.OKBLUE +  "alert_database[{}]: {}".format(ip,self.alert_database.database[ip]) + bcolors.ENDC)
                    #print("posilam pozadavak o zachyt: ", )
                    if(score >= 1 or (score == 1 and (cnt % 100) == 3 ) ):
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
    def connection_is_established(cls):
        return Sock.connect() > 0

    @classmethod
    def connect_to_time_manager(cls):
        Sock.add_probes(cls.addr_info)

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
    filter = Filter(xarg, dispatcher_options, args.cfg, args.cfg_mapping, tmm_params)
    filter.prompt = '> '
    filter.cmdloop('Starting prompt...')
    # filter = Filter(xarg, dispatcher_options, args.cfg, args.cfg_mapping, tmm_params).run_filter()
    exit()

#!/usr/bin/env python
#python filter.py -i "u:hoststats-alerts,u:haddrscan-alerts"

import logging
import json
import sys
import os
import pika
import ssl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from os.path import dirname as dirn
import glob
import pytz
import shutil
import threading
import ipaddress
import time
from filter.mapping import Mapping
from filter.time_machine_capture import Capture, Sock
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
    ROOT_PATH = os.path.realpath(dirn(dirn(os.path.abspath(__file__))))
    JSONS_PATH = ROOT_PATH + '/jsons/'
    JSONS_PROCESSED_PATH = ROOT_PATH + '/jsons/processed/'
    JSONS_ERROR_PROCESSED_PATH = ROOT_PATH + '/jsons/error_processed/'


    def __init__(self, shared_array, event):
        threading.Thread.__init__(self)
        self.shared_array = shared_array
        self.shared_thread_event = event
        self.daemon = True

    def run(self):
        logging.debug('running FolderDispatcher')
        self.folder_dispatcher()



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
        m = Mapping()
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
                        idea_alert = m.map_alert_to_hash(data)
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
    def __init__(self, shared_array, event):
        self.m = Mapping()
        threading.Thread.__init__(self)
        self.shared_array = shared_array
        self.shared_thread_event = event

    def run(self):
        logging.debug('running RabbitMqDispatcher')
        self.idea_dispatcher()

    def idea_dispatcher(self):
        ssl_options = {
            "ca_certs":"/Users/adamplansky/Desktop/message_app/testca/cacert.pem",
            "certfile": "/Users/adamplansky/Desktop/message_app/client/cert.pem",
            "keyfile": "/Users/adamplansky/Desktop/message_app/client/key.pem",
            "cert_reqs": ssl.CERT_REQUIRED,
            "ssl_version":ssl.PROTOCOL_TLSv1_2
        }
        credentials = pika.PlainCredentials(os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])
        parameters = pika.ConnectionParameters(host='192.168.2.120', port=5671, virtual_host='/', heartbeat_interval = 0, credentials=credentials, ssl = True, ssl_options = ssl_options)
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
            print("data: ",data,data.__class__)
            idea_alert = self.m.map_alert_to_hash(data)
            print("idea_alert: ",idea_alert)
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

    @classmethod
    def parse_score(cls, alert):
        return max(map(Price.get_statis_price,alert["Category"]))

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
                "score": cls.parse_score(alert)}

    @classmethod
    def parse_alert(cls, alert):
        if "Test" in alert["Category"]: return None
        return cls.dissassemble_alert(alert)

class AlertDatabase:
    def __init__(self):
        self.database = {}

    def get_ip_prefix(self, ips):
        #print("get_ip_prefix", ips)
        if(len(ips) == 0 ): return None,[]
        if(len(ips[0]) > 0): return "S", ips[0]
        if(len(ips[1]) > 0): return "T", ips[1]
        return None,[]


    def get_max_score(self,ip):
        #todo: check if it works
        #probably some test is needed
        return max([x[1] for x in self.database[ip]])
    def get_last_score(self,ip):
        if(len(self.database[ip]["alerts"]) > 0):
            return self.database[ip]["alerts"][-1][1]
        return -1

    def print_database(self):
        print("-----DATABASE-----")
        for key, value in self.database.items() :
            print ("{} -> {}/{}".format(key, value["cnt_hour"],value["cnt"]))
        print("-----DATABASE-----")

    def get_cnt_hour(self, ip):
        return self.database[ip]["cnt_hour"]

    def get_cnt(self, ip):
        return self.database[ip]["cnt"]

    def recalculate_cnt_hour(self, ip):
        date_min = datetime.now(pytz.timezone("UTC")) - timedelta(hours=1)
        cnt_hour = 0
        for idx, da_alert in enumerate(self.database[ip]["alerts"]):
            if(date_min < da_alert[0]):
                cnt_hour+=1
                #print(da_alert[0])
            else:
                del self.database[ip]["alerts"][idx]
        self.database[ip]["cnt_hour"] = cnt_hour
        #print(date_min < self.database[ip]["alerts"][0])
        #self.database[ip]["cnt_hour"] = cnt_hour
        # print("##############################")
        # print(self.database[ip])
        # print("##############################")


    def database(self):
        return self.database

    def add(self,da_alert):
        #print("da_alert: ", da_alert)
        if da_alert is None: return
        prefix, ips = self.get_ip_prefix(da_alert["ips"])
        #print("add: ",prefix, ips)
        ips_to_return = []
        for ip_ary in ips:
            ip = prefix + ip_ary
            if not ip in self.database: self.database[ip] = {"cnt": 0, "alerts": [], "cnt_hour": 0}
            ips_to_return.append(ip)
            self.database[ip]["alerts"].append([
                                      da_alert["time"],
                                      da_alert["score"],
                                      da_alert["node"]
                                     ])
            self.database[ip]["cnt"] += 1
            self.recalculate_cnt_hour(ip)


        #sself.print_database()
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
class Price:
    ROOT_PATH = os.path.realpath(dirn(dirn(os.path.abspath(__file__))))
    CFG_JSON_PATH = ROOT_PATH + '/config/static_prices.json'

    MAX_PRICE = 1000
    # algorithm for price calculation
    init_call = True
    cfg_static_prices = {}
    @classmethod
    def __init__(cls):
        cls.init_call = False
        cls.load_cfg()


    @classmethod
    def load_cfg(cls):
        with open(cls.CFG_JSON_PATH) as data_file:
            data = json.load(data_file)
            for val in data:
                for k,v in val.items():
                    if(type(v) is int):
                        _category = "{}".format(k)
                        _price = v
                        cls.cfg_static_prices[_category] = int(_price)
                        continue

                    for kk,vv in v.items():
                        _category = "{}.{}".format(k,kk)
                        _price = vv
                        cls.cfg_static_prices[_category] = int(_price)
                        #print(cls.cfg_static_prices)

    @classmethod
    def get_statis_price(cls, category):
        if(cls.init_call != False): cls.__init__()
        try:
            return cls.cfg_static_prices[category]
        except Exception:
            #todo: log this in config / send email with json alert
            return cls.cfg_static_prices["NotInConfig"]

    @classmethod
    def calculate_price_new(cls, ip_address):
        database_row = cls.alert_database.add(ip_address)

        return database_row


    @classmethod
    def calculate_price(cls, event):
        if(cls.init_call != False): cls.__init__()
        static_price = 0
        for category in event["Category"]:
            print("category: {}, price: {}".format(category,cls.get_statis_price(category)))
            static_price += cls.cfg_static_prices[category]


class Filter():
    def __init__(self,argv_param):
        #threading.Thread.__init__(self)
        self.shared_array = list()
        self.shared_thread_event = threading.Event()
        self.counter = 0
        self.heap_output = HeapOutput()
        self.argv_param = argv_param
        self.alert_database = AlertDatabase()
        self.global_filter_cnt = 0
        self.global_capture_filter_cnt = 0


    def run_filter(self):
        logging.debug('running Filter')

        if self.argv_param == '-f':
            fd = FolderDispatcher(self.shared_array,self.shared_thread_event)
        elif self.argv_param == '-RMQ':
            fd = RabbitMqDispatcher(self.shared_array,self.shared_thread_event)
        #elif self.argv_param == '-i':
            #fd = UnixSocketDispatcher(self,self.shared_thread_event)
        fd.setDaemon(True)  #
        fd.start()
        self.calculate_price()
        fd.join()



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
                for ip in ips:
                    #todo: cnt_hour pouze pokud add += 1 jinak nic
                    score = self.alert_database.get_last_score(ip)
                    #cnt_hour = self.alert_database.get_cnt_hour(ip)
                    cnt = self.alert_database.get_cnt(ip)
                    #print("get score for ip {} score: {} cnt_hour: {}".format(ip,score, cnt_hour))
                    #print("alert: ", self.alert_database.database[ip])
                    self.global_filter_cnt += 1
                    if(score > 1 or (score == 1 and (cnt == 2 or cnt % 100 == 0))):
                        #posli pozadavek o zachyt
                        CaptureRequest.send(ip)
                        self.global_capture_filter_cnt += 1
                        print(bcolors.WARNING +  "{}/{}".format(self.global_capture_filter_cnt,self.global_filter_cnt ) + bcolors.ENDC)
                    #else:
                        #print("Capture requirments: " +bcolors.WARNING +  "Not satisfied" + bcolors.ENDC)


class CaptureRequest():
    init_call = True
    @classmethod
    def __init__(cls):
        cls.init_call = False
        cls.addr_info = [['localhost', 37564]]

    @classmethod
    def send(cls, dir_and_ip):
        if(cls.init_call != False): cls.__init__()
        if not cls.connection_is_established():
            cls.connect_to_time_manager()

        if cls.connection_is_established():
            ip = "8.8.8.1"
            direction = "src_ip"
            direction, ip = AlertExtractor.extract_ip_and_direction(dir_and_ip)
            print(bcolors.OKGREEN + "Capture Request => ip: {}, direction: {}. packets: {}, seconds: {}".format(ip, direction, 10000, 300) + bcolors.ENDC)
            Capture.do_add("{} {} {} {} {}".format(direction, ip, "XYZA", 10000, 500))
            Capture.do_list("")
            #Capture.do_remove("{} {}".format(direction, ip))
            #Capture.do_list("")



    @classmethod
    def connection_is_established(cls):
        return Sock.connect() > 0

    @classmethod
    def connect_to_time_manager(cls):
        Sock.add_probes(cls.addr_info)


def help():
    return """
    Options:
          -i "u:socket1,u:socket2" - to use filter with NEMEA unixsockets. Number of sockets is variable."
          -f - filter reads IDEA jsons from /jsons folder
          -RMQ - rabbitmq - hardcoded parameters
          """
if __name__ == '__main__':
    try:
        print(sys.argv)
        if(len(sys.argv) == 1 or sys.argv[1] in ["-h","--help"]):
            print(help())
        elif(sys.argv[1] == "-RMQ"):
            Filter(sys.argv[1]).run_filter()
        elif(sys.argv[1] == "-f"):
            Filter(sys.argv[1]).run_filter()
        elif(sys.argv[1] == "-i"):
            Filter(sys.argv[1]).run_filter()
        else:
            print(help)
    except KeyboardInterrupt:
        print("interrupting")
    # for t in threads:
    #     t.join()
    #
    # print "Exiting Main Thread"

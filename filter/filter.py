#!/usr/bin/env python3
#python filter.py -i "u:hoststats-alerts,u:haddrscan-alerts"
import logging
import json
import sys
import os
from os.path import dirname as dirn
import glob
import shutil
import threading
#import random
import time
#from jq import jq
#https://github.com/mwilliamson/jq.py

#from random import randint
import heapq
from datetime import datetime
#from pprint import pprint
from math import log

first = lambda h: 2**h - 1      # H stands for level height
last = lambda h: first(h + 1)
level = lambda heap, h: heap[first(h):last(h)]
prepare = lambda e, field: str(e).center(field)


def hprint(heap, width=None):
    if width is None:
        width = max(len(str(e)) for e in heap)
    height = int(log(len(heap), 2)) + 1
    gap = ' ' * width
    for h in range(height):
        below = 2 ** (height - h - 1)
        field = (2 * below - 1) * width
        print(gap.join(prepare(e, field) for e in level(heap, h)))
logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-10s) %(message)s',
)
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

    def run(self):
        logging.debug('running FolderDispatcher')
        self.folder_dispatcher()


    def move_to_folder(self, src_path, dst_directory):
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
        # todo: blocking calling is required in future instead of infinity loop
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
                        # todo: some preprocess of data
                        # todo: aggregate data many same errors
                        # differents system can have different JSONs structure (IDEA, IDMEF)
                        self.shared_array.append( data )
                        self.move_to_processed_folder( filename )
                    except Exception as e:
                        logging.error("for file: {} error: {}".format(filename,e))
                        self.move_to_error_folder(filename)
                self.shared_thread_event.set()
            time.sleep(1)


class AlertExtractor:

    @classmethod
    def parse_datetime(cls, datetime_string):
        return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')

    @classmethod
    def get_crated_at(cls, alert):
        return cls.parse_datetime(alert["CreateTime"])

    @classmethod
    def get_detect_time(cls, alert):
        return cls.parse_datetime(alert["DetectTime"])

    @classmethod
    def get_cease_time(cls, alert):
        return cls.parse_datetime(alert["CeaseTime"])

    @classmethod
    def get_ips(cls, alert):
        ips = []
        if("Source" in alert):
            ips += cls.parse_ips(alert["Source"])
        return ips

    @classmethod
    def parse_array(cls, ary):
        arr = []
        for val in ary:
            arr.append(val)
        return arr

    @classmethod
    def parse_ips(cls, event):
        ary_ips = []
        for ev in event:
            if("IP4" in ev):
                ary_ips += cls.parse_array(ev["IP4"])
            if("IP6" in ev):
                ary_ips += cls.parse_array(ev["IP6"])
        return ary_ips
        #if(ip["IP6"]):
        # muze bejt ip4 nebo ip6
        # ip4 : [pole]
        # viz: https://idea.cesnet.cz/en/index


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
        #ips += AlertExtractor.get_ips(event)
        #print("report IPS: ", ips)
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
                print(val.items())
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
    def calculate_price(cls, event):
        if(cls.init_call != False): cls.__init__()
        static_price = 0
        for category in event["Category"]:
            print("category: {}, price: {}".format(category,cls.cfg_static_prices[category]))
            static_price += cls.cfg_static_prices[category]
        cr_time = AlertExtractor.get_crated_at(event)
        detect_time = AlertExtractor.get_detect_time(event)
        print("cr_time: ",cr_time)
        print("detect_time: ", detect_time)
        ips = AlertExtractor.get_ips(event)
        return (static_price, ips )
        #ips += AlertExtractor.get_ips(event)
        #print("report IPS: ", ips)
        # print("CENA: ", static_price)

        #return (random.randint(1, cls.MAX_PRICE), event["ID"] )



class Trimmer:
    def __init__(self):
        pass

    def preprocess(self, input):
        #""" parse xml / json and take only mandatory items""
        #TODO: implement!
        return input




class Filter(threading.Thread):
    def __init__(self,argv_param):
        threading.Thread.__init__(self)
        self.shared_array = list()
        self.shared_thread_event = threading.Event()
        self.counter = 0
        self.heap_output = HeapOutput()
        self.argv_param = argv_param

    def run(self):
        logging.debug('running Filter')
        if self.argv_param == '-f':
            fd = FolderDispatcher(self.shared_array,self.shared_thread_event)
        #elif self.argv_param == '-i':
            #fd = UnixSocketDispatcher(self,self.shared_thread_event)

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
                # print("processed files: ", self.counter)

                #vemu si IDEA alert
                threat_event = self.shared_array.pop()
                print("threat_event: {}".format(threat_event))
                #rozparsuju IDEA alert
                threat = Price.calculate_price(threat_event)
                self.heap_output.add(threat)

class FilterMain():
    def __init__(self, argv_param):
        filter = Filter(argv_param)
        filter.start()
        filter.join()

def help():
    return """
    Options:
          -i "u:socket1,u:socket2" - to use filter with NEMEA unixsockets. Number of sockets is variable."
          -f - filter reads IDEA jsons from /jsons folder
          """
if __name__ == '__main__':
    print(sys.argv)
    if(len(sys.argv) == 1 or sys.argv[1] in ["-h","--help"]):
        print(help())
    elif(sys.argv[1] == "-f"):
        FilterMain(sys.argv[1])
    elif(sys.argv[1] == "-i"):
        FilterMain(sys.argv[1])
    else:
        print(help)

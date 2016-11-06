#!/usr/bin/env python3

import logging
import json
import os
import glob
import shutil
import threading
import random
import heapq
from pprint import pprint

logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-10s) %(message)s',
)

class FolderDispatcher(threading.Thread):
    # logging.basicConfig(filename="example.log",level=logging.DEBUG)
    JSONS_PATH = '../jsons/'
    JSONS_PROCESSED_PATH = '../jsons/processed/'
    JSONS_ERROR_PROCESSED_PATH = '../jsons/error_processed/'

    def __init__(self, folder_dispatcher, event):
        threading.Thread.__init__(self)
        self.shared_array = folder_dispatcher.shared_array
        self.shared_thread_event = event

    def run(self):
        logging.debug('running FolderDispatcher')
        self.folder_dispatcher()


    def move_folder(self, src_path, dst_directory):
        if not os.path.exists(dst_directory):
            os.makedirs(dst_directory)

        filename = os.path.basename(src_path)
        dst_path = "{}{}".format(dst_directory, filename)
        shutil.move(src_path, dst_path)

    def move_to_processed_folder(self, path):
        return self.move_folder(path, self.JSONS_PROCESSED_PATH)

    def move_to_error_folder(self, path):
        return self.move_folder(path, self.JSONS_ERROR_PROCESSED_PATH)


    def folder_dispatcher(self):
        # todo: blocking calling is required in future instead of infinity loop
        while True:

            for filename in glob.glob(os.path.join(self.JSONS_PATH, '*.json')):
                print(filename)
                with open(filename) as data_file:
                    try:
                        data = json.load(data_file)
                        print(data)
                        # todo: some preprocess of data
                        # differents system can have different JSONs structure
                        self.shared_array.append( data )
                        self.move_to_processed_folder(filename)
                    except Exception as e:
                        logging.error("for file: {} error: {}".format(filename,e))
                        self.move_to_error_folder(filename)
                self.shared_thread_event.set()

class HeapOutput:
    #how many probes do I have?
    PROBES_CAPACITY = 5
    JSONS_PROBES_PATH = '../jsons/probes/'
    def __init__(self):
        self.heap = []

    def create_json_threat_file(self, threat):
        json_out = json.dumps(threat)
        if not os.path.exists(self.JSONS_PROBES_PATH):
            os.makedirs(self.JSONS_PROBES_PATH)

        # threat[1] = threat[ID]
        threat_file_name = "{}{}.json".format(self.JSONS_PROBES_PATH,threat[1])
        with open(threat_file_name, 'w') as f:
            f.write(json_out)

    def add(self, threat):
        if self.PROBES_CAPACITY > len(self.heap):
            print("push")
            heapq.heappush(self.heap,threat)
            self.create_json_threat_file(threat)
        else:
            pop_val = heapq.heappushpop(self.heap,threat)
            if pop_val != threat:
                self.create_json_threat_file(threat)

class Price:

    MAX_PRICE = 1000
    # algorithm for price calculation
    @classmethod
    def calculate_price(cls, event):
        return (random.randint(1, cls.MAX_PRICE), event["ID"] )

class Filter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.shared_array = list()
        self.shared_thread_event = threading.Event()
        self.counter = 0
        self.heap_output = HeapOutput()

    def run(self):
        logging.debug('running Filter')
        fd = FolderDispatcher(self,self.shared_thread_event)
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
                print("processed files: ", self.counter)
                threat_event = self.shared_array.pop()
                _tuple = Price.calculate_price(threat_event)
                self.heap_output.add(_tuple)


filter = Filter()
filter.start()
filter.join()
#logging.debug(filter.shared_array)

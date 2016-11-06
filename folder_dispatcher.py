#!/usr/bin/env python3

import logging
import json
import os
import glob
import shutil
import threading
from pprint import pprint

logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-10s) %(message)s',
)



class FolderDispatcher(threading.Thread):
    # logging.basicConfig(filename="example.log",level=logging.DEBUG)
    JSONS_PATH = 'jsons/'
    JSONS_PROCESSED_PATH = 'jsons/processed/'
    JSONS_ERROR_PROCESSED_PATH = 'jsons/error_processed/'



    def __init__(self, folder_dispatcher):
        self.shared_array = folder_dispatcher.shared_array

    def run(self):
        logging.debug('running')
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
        i = 0
        while True:

            i += 1
            if(i == 10):
                return

            #for filename in glob.glob(os.path.join(self.JSONS_PATH, '*.json')):
            for filename in glob.glob(os.path.join(self.JSONS_PROCESSED_PATH, '*.json')):
                with open(filename) as data_file:
                    i += 1
                    if(i == 10):
                        return
                    try:
                        data = json.load(data_file)
                        self.shared_array.append( data )
                        # send to filter dictionary
                        self.move_to_processed_folder(filename)

                    except Exception as e:
                        logging.error("for file: {} error: {}".format(filename,e))
                        self.move_to_error_folder(filename)

class Filter(threading.Thread):
    def __init__(self):
        self.shared_array = list()

    def run(self):
        logging.debug('running Filter')
        fd = FolderDispatcher(self)
        fd.run()

filter = Filter()
filter.run()
print(filter.shared_array)

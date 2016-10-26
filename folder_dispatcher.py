#!/usr/bin/env python3

import logging
import json
import os
import glob
from pprint import pprint

logging.basicConfig(filename='example.log',level=logging.DEBUG)

def folder_dispatcher():
    for filename in glob.glob(os.path.join('jsons/', '*.json')):
        with open(filename) as data_file:
            try:
                logging.debug(filename)
                data = json.load(data_file)
                # todo: move to dispatched directory
            except Exception as e:
                logging.error("for file: {} error: {}".format(filename,e))
                # todo: move to other directory

            logging.info(data)

folder_dispatcher()

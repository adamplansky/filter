import logging
import json
import os
import glob
import shutil
import threading
import random
import heapq
from pprint import pprint

CFG = '../config/static_prices.json'


def load_cfg():
    filename = CFG
    print(filename)
    with open(filename) as data_file:
        data = json.load(data_file)
        for val in data:
            for k,v in val.items():
                if(type(v) is int):
                    _category = "{}".format(k)
                    _price = v
                    print(_category, _price)
                    continue

                for kk,vv in v.items():
                    _category = "{}.{}".format(k,kk)
                    _price = vv
                    print(_category, _price)


load_cfg()

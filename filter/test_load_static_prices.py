import os
import json
from os.path import dirname as dirn
from collections import defaultdict


def pretty(d, indent=0):
    for key, value in d.iteritems():
        print '\t' * indent + str(key)
        if isinstance(value, dict):
            pretty(value, indent+1)
        else:
            print '\t' * (indent+1) + str(value)


class Price:
    ROOT_PATH = os.path.realpath(dirn(dirn(os.path.abspath(__file__))))
    CFG_JSON_PATH = ROOT_PATH + '/config/static_prices.json'
    init_call = True
    cfg_static_prices = {}
    @classmethod
    def __init__(cls):
        cls.init_call = False
        cls.load_cfg()

    @classmethod
    def load_cfg_recursion(cls,dict_in, dict_out,key_acc=""):
        for key, val in dict_in.items():
            if not isinstance(val,dict):
                dict_out[key_acc][key] = val
            else:
                k = (key_acc + "." + key if len(key_acc) > 0 else key)
                cls.load_cfg_recursion(val, dict_out,k)

    @classmethod
    def load_cfg(cls):
        with open(cls.CFG_JSON_PATH) as data_file:
            data = json.load(data_file)
            cfg_dict = defaultdict(dict)
            for cfg_line_dict in data:
                cls.load_cfg_recursion(cfg_line_dict, cfg_dict)
            pretty(cfg_dict)




Price.load_cfg()

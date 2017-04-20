#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from os.path import dirname as dirn
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))





class Score:
    ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))
    @classmethod
    def __init__(cls, cfg_path ):
        cls.file_path = os.path.normpath(cls.ROOT_PATH + "/" + cfg_path)
        cls.modulo = cls.p = 0
        cls.load_cfg()

    @classmethod
    def load_cfg(cls):
        with open(cls.file_path) as data_file:
            for line in data_file:
                try:
                    if(line.strip()[0] == "#"): continue
                    cls.p, cls.modulo = map(int, line.split(" "))
                    print(cls.p, cls.modulo)
                    break
                except Exception as e:
                    print e, "in file: {}".format(cls.file_path)


    @classmethod
    def scan_params(cls):
        return cls.p, cls.modulo

Score.__init__("../config/scan_algorithm_parameters")
print Score.scan_params()
#Score.reload_cfg()

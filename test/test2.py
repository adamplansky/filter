#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import sys
import logging
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/filter" )


from filter import AlertDatabase, AlertExtractor, Filter, Score, MyJson, CaptureHeap,IdeaMapping
from mapping import Mapping
#import datetime
from datetime import datetime, timedelta
import pytz
import random

def get_random_valid_time():
    random_int = random.randint(1, 55)
    return datetime.now(pytz.utc) - timedelta(minutes=random_int)


class MyTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
    # def __init__(self):
        self.ad = AlertDatabase("../config/static_prices.json", "../test/probability_db")
        self.first_alert = {'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Scanning'],'time':get_random_valid_time()}
        self.ad.add(self.first_alert)

    def test_get_static_price_from_cfg(self):
        self.assertEqual(self.ad.get_static_price('Recon.Scanning'), 1)
        self.assertEqual(self.ad.get_static_price("UNDEFINEDCATEGORY"), 5)

    def test_get_static_price(self):
        self.assertEqual(self.ad.get_static_price(u'Recon.Scanning'), 1)
        self.assertEqual(self.ad.get_static_price([u'Recon.Scanning']), 1)
        self.assertEqual(self.ad.get_static_price(['Recon.Scanning','Abusive.Spam']), 6)

    def test_extract_ip_and_direction(self):
        self.assertEqual(self.ad.get_static_price(u'Recon.Scanning'), 1)

    def test_get_ip_prefix(self):
        self.assertEqual(self.ad.get_ip_prefix([[],[]]),[[],[]])
        self.assertEqual(
            self.ad.get_ip_prefix([["1.2.3.4","1.2.3.5"],["6.5.7.8","6.5.7.6"]]),
            [["S1.2.3.4","S1.2.3.5"],["T6.5.7.8","T6.5.7.6"]])

        self.assertEqual(self.ad.get_ip_prefix([["1.2.3.4"],[]]),[["S1.2.3.4"],[]])
        self.assertEqual(self.ad.get_ip_prefix([[],["1.2.3.4"]]),[[],["T1.2.3.4"]])

    def test_get_last_category_array(self):
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Searching'],'time':datetime.now(pytz.utc)})
        self.assertEqual(self.ad.get_last_category_array(u'S201.214.56.9'),[u'Recon.Searching'])
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Searching',u'Recon.Scanning'],'time':datetime.now(pytz.utc)})
        self.assertEqual(self.ad.get_last_category_array(u'S201.214.56.9'),[u'Recon.Searching',u'Recon.Scanning'])

    def test_get_categories_by_alert_index(self):
        self.assertEqual(self.ad.get_categories_by_alert_index('S201.214.56.9', 0),[u'Recon.Scanning'])


    def test_parse_category_to_ip(self):
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Searching'],'time':datetime.now(pytz.utc)})
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Searching'],'time':datetime.now(pytz.utc)})
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Searching',u'Recon.Scanning'],'time':datetime.now(pytz.utc)})
        #2x Recon.Scanning
        #3x Recon.Searching
        self.assertEqual(self.ad.database[u'S201.214.56.9'][u'Recon.Searching'], 3)
        self.assertEqual(self.ad.database[u'S201.214.56.9'][u'Recon.Scanning'], 2)

    def test_get_last_score(self):
        self.assertEqual(self.ad.get_last_score(u'S201.214.56.9'),1)
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Searching',u'Recon.Scanning'],'time':datetime.now(pytz.utc)})
        self.assertEqual(self.ad.get_last_score(u'S201.214.56.9'),10)

    def test_get_category_cnt_by_ip(self):
        self.assertEqual(self.ad.get_category_cnt_by_ip("S201.214.56.9", 'Recon.Scanning'), 1)
        self.assertEqual(self.ad.get_category_cnt_by_ip("T195.113.253.123", 'Recon.Scanning'), 1)
        self.assertEqual(self.ad.get_category_cnt_by_ip("T195.113.253.2", 'Recon.Scanning'), 0)
        self.assertEqual(self.ad.get_category_cnt_by_ip("T195.113.253.123", 'Recon.Scanning1'), 0)
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Scanning'],'time':datetime.now(pytz.utc) - timedelta(minutes=70) })
        self.assertEqual(self.ad.get_category_cnt_by_ip("S201.214.56.9", 'Recon.Scanning'), 1)
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Scanning'],'time':datetime.now(pytz.utc) - timedelta(minutes=55) })
        self.assertEqual(self.ad.get_category_cnt_by_ip("S201.214.56.9", 'Recon.Scanning'), 2)

    def test_get_last_alert_event(self):
        #log= logging.getLogger( "MyTest.test_get_last_alert_event" )
        a = self.first_alert
        self.assertEqual(self.ad.get_last_alert_event(u'S201.214.56.9'),[a["time"],a["category"],a["node"], ["T195.113.253.123"]])

    def test_load_probability_db(self):
        dd = defaultdict(float)
        dd["Recon.Scanning"] = 1000
        dd["cnt"] = 1001
        dd["Abusive.Spam"] =  1.0
        self.assertEqual(self.ad.alert_probability, dd)

    def xtest_save_probability_db(self):
        filename = "../test/probability_db1"
        if os.path.exists(filename):
            os.remove(filename)

        ad = AlertDatabase("../config/static_prices.json", filename)
        for i in range(1005):
            ad.add(self.first_alert)
        dd = defaultdict(float);dd["Recon.Scanning"] = 1005;dd["cnt"] = 1005
        self.assertEqual(ad.alert_probability, dd)


    def test_add_to_probability_database(self):
        d = defaultdict(float)
        d["Recon.Scanning"] = 1000;d["Abusive.Spam"] = 1;d["Recon.Sniffing"] = 1;d["Recon.Searching"] = 1;d["cnt"] = 1003
        self.assertEqual(self.ad.add_to_probability_database(['Recon.Sniffing','Recon.Searching']), d)

    def test_get_category_probability(self):
        self.ad.add_to_probability_database(['Recon.Sniffing','Recon.Searching'])
        self.assertEqual(self.ad.get_probability_by_category("Recon.Sniffing"),1.0/1003)

    def test_get_category_with_max_score_from_last_alert(self):
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Scanning', 'Availability.DDoS'],'time':get_random_valid_time()})
        self.assertEqual(self.ad.get_category_with_max_score_from_last_alert("S201.214.56.9"),"Availability.DDoS")

    def test_signum(self):
        self.assertEqual(Score.signum(5),1)
        self.assertEqual(Score.signum(0),1)
        self.assertEqual(Score.signum(-1),-1)

    def test_score_func(self):
        self.assertEqual(Score.score_func(10,0.5),768.0)
        self.assertEqual(Score.score_func(9,0.5),384)
        self.assertEqual(Score.score_func(2,0.5),3)

    def test_get_score(self):
        #self.assertEqual(Score.signum(-1+4),1)
        self.assertEqual(Score.get_score(1,10,0.5),768.0)

    def test_scan_price(self):
        self.assertEqual(Score.SCAN_PRICE, 1)

    def test_is_important(self):
        Score.__init__("../test/scan_algorithm_parameters.json")
        self.assertEqual(Score.scan_is_important(2),False)
        self.assertEqual(Score.scan_is_important(5),True)
        self.assertEqual(Score.scan_is_important(105),True)

    def test_score_scan_alg_params(self):
        Score.__init__("../test/scan_algorithm_parameters.json")
        self.assertEqual(Score.scan_params(), (95, 100, 500) )

    def test_my_json(self):
        d = MyJson.load_json_file_with_comments('../test/scan_algorithm_parameters.json')
        d2 = {"first": 5,"every": 100,"limit": 500, "max_parallel_capture_cnt": 1,  "random_scan": 250}
        self.assertEqual(d,d2)

    def test_capture_heap(self):
        cp = CaptureHeap("../test/scan_algorithm_parameters.json")
        #d = MyJson.load_json_file_with_comments('../config/scan_algorithm_parameters.json')
        #d2 = {"first": 5,"every": 100,"limit": 500, "max_capture_parallel_count": 5}
        self.assertEqual(cp.max_parallel_capture_cnt,1)

    def test_get_capture_params(self):
        x = self.ad.get_capture_params("S201.214.56.9")
        y = [{'category': u'Recon.Scanning', 'ip_addr': 'S201.214.56.9', 'direction': 'src_ip', 'packets': 10, 'timeout': 100}]
        self.assertEqual(x,y)


    def test_delete_obsolete_items(self):
        cp = CaptureHeap("../test/scan_algorithm_parameters.json")
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.215.56.9'],[u'195.113.253.123']],'category': [u'Abusive.Harassment'],'time':get_random_valid_time()})
        x = self.ad.get_capture_params("S201.215.56.9")
        y = cp.add_to_heap(x, 10)
        self.assertEqual(y,True)
        x = self.ad.get_capture_params("S201.214.56.9")
        y = cp.add_to_heap(x, 1)
        self.assertEqual(y,False)


    def test_add_to_heap(self):
        cp = CaptureHeap("../test/scan_algorithm_parameters.json")
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.215.56.9'],[u'195.113.253.123']],'category': [u'Abusive.Harassment'],'time':get_random_valid_time()})
        x = [{'category': u'Recon.Scanning', 'ip_addr': 'S201.214.56.9', 'direction': 'src_ip', 'packets': 10, 'timeout': 0}]
        y = cp.add_to_heap(x, 10)
        self.assertEqual(y,True)
        x = self.ad.get_capture_params("S201.214.56.9")
        y = cp.add_to_heap(x, 1)
        self.assertEqual(y,True)

    def test_mapping(self):
        idea =  {u'Node': [{u'SW': [u'Nemea', u'HostStatsNemea'], u'Type': [u'Flow', u'Statistical'], u'Name': u'cz.cesnet.nemea.hoststats'}], u'Category': [u'Recon.Scanning'], u'EventTime': u'2017-01-01T02:06:00Z', u'Description': u'Horizontal port scan', u'ConnCount': 655, u'CeaseTime': u'2017-01-01T02:10:53Z', u'Format': u'IDEA0', u'ID': u'1bdfff5e-6ad4-4e63-98f6-e3e350996a5f', u'Source': [{u'IP4': [u'185.35.62.107'], u'Proto': [u'tcp']}], u'FlowCount': 655, u'DetectTime': u'2017-05-02T18:13:59Z', u'CreateTime': u'2017-05-02T18:13:59Z'}
        m = Mapping("../config/mapping")
        h = m.map_alert_to_hash(idea)

        dis = {'Node': [{u'Type': [u'Flow', u'Statistical'], u'SW': [u'Nemea', u'HostStatsNemea'], u'Name': u'cz.cesnet.nemea.hoststats'}], 'DetectTime': u'2017-05-02T18:13:59Z', 'SourceIP6': None, 'SourceIP4': [u'185.35.62.107'], 'TargetIP4': None, 'Category': [u'Recon.Scanning'], 'TargetIP6': None}
        self.assertEqual(h, dis)

        h = IdeaMapping.map_alert_to_hash(idea)
        self.assertEqual(h, dis)





if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "MyTest" ).setLevel( logging.DEBUG )
    unittest.main()

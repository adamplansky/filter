#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import sys
import logging
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/filter" )


from filter import AlertDatabase, AlertExtractor, Filter, Score
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
        self.ad = AlertDatabase("../config/static_prices.json")
        self.first_alert = {'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Scanning'],'time':get_random_valid_time()}
        self.ad.add(self.first_alert)

    def test_get_static_price_from_cfg(self):
        self.assertEqual(self.ad.get_static_price('Recon.Scanning'), 1)
        self.assertEqual(self.ad.get_static_price("UNDEFINEDCATEGORY"), 10)

    def test_get_static_price(self):
        self.assertEqual(self.ad.get_static_price(u'Recon.Scanning'), 1)
        self.assertEqual(self.ad.get_static_price([u'Recon.Scanning']), 1)
        self.assertEqual(self.ad.get_static_price(['Recon.Scanning','Abusive.Spam']), 10)

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

    def test_add_to_probability_database(self):
        d = defaultdict(float)
        d["Recon.Scanning"] = 1;d["Recon.Sniffing"] = 1;d["Recon.Searching"] = 1;d["cnt"] = 3
        self.assertEqual(self.ad.add_to_probability_database(['Recon.Sniffing','Recon.Searching']), d)

    def test_get_category_probability(self):
        self.ad.add_to_probability_database(['Recon.Sniffing','Recon.Searching'])
        self.assertEqual(self.ad.get_probability_by_category("Recon.Sniffing"),1.0/3)

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

    def test_treshold(self):
        self.assertEqual(Score.TRESHOLD_SCANS, 2)

    def test_is_important(self):
        #❌ nacist score z configuraku
        Score.__init__("../test/scan_algorithm_parameters")
        self.assertEqual(Score.scan_params(), (90, 100))
        self.assertEqual(Score.scan_is_important(2),False)
        self.assertEqual(Score.scan_is_important(10),True)
        self.assertEqual(Score.scan_is_important(110),True)
        #self.assertEqual(Score.scan_is_important(136+150),True)
        #self.assertEqual(Score.scan_is_important(200),False)

    def test_score_scan_alg_params(self):
        Score.__init__("../test/scan_algorithm_parameters")
        self.assertEqual(Score.scan_params(), (90, 100))



if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "MyTest" ).setLevel( logging.DEBUG )
    unittest.main()


import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from filter.filter import AlertDatabase, AlertExtractor
#import datetime
from datetime import datetime, timedelta, timezone

class MyTest(unittest.TestCase):
    def test_get_max_score(self):
        ad = AlertDatabase()
        a = [[datetime(2017, 2, 14, 6, 49, 33), 4, ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea']], [datetime(2017, 2, 14, 6, 49, 33), 3, ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea']]]
        ad.database["S1.2.3.4"] = a
        self.assertEqual(ad.get_max_score("S1.2.3.4"), 4)

    def test_get_last_score(self):
        ad = AlertDatabase()
        da_alert = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime(2017, 2, 13, 19, 23, 50), 'ips': [['88.250.248.71'], ['78.128.254.197']]}
        da_alert1 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 2, 'time': datetime.now(timezone.utc), 'ips': [['88.250.248.71'], ['78.128.254.197']]}
        da_alert2 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 3, 'time': datetime.now(timezone.utc), 'ips': [['88.250.248.71'], ['78.128.254.197']]}
        ad.add(da_alert)
        ad.add(da_alert1)
        ad.add(da_alert2)

        self.assertEqual(ad.get_last_score('S88.250.248.71'), 3)
    def test_get_last_score(self):
        ad = AlertDatabase()
        da_alert = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.now(timezone.utc) - timedelta(days=1) , 'ips': [['88.250.248.71'], ['78.128.254.197']]}
        ad.add(da_alert)

        self.assertEqual(ad.get_last_score('S88.250.248.71'), -1)

    def test_test_last_score(self):
        pass
    def test_extract_ip_and_direction(self):
        direction, ip = AlertExtractor.extract_ip_and_direction("S1.2.3.4")
        self.assertEqual(direction, "S")
        self.assertEqual(ip, "1.2.3.4")

    # def test_recalculate_cnt_hour(self):
    #     print("yOyO")
    #     da_alert = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.datetime(2017, 2, 13, 19, 23, 50), 'ips': [['88.250.248.71'], ['78.128.254.197']]}
    #     da_alert1 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.datetime.now(), 'ips': [['88.250.248.71'], ['78.128.254.197']]}
    #     da_alert2 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.datetime.now(), 'ips': [['88.250.248.72'], ['78.128.254.195']]}
    #     da_alert3 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.datetime.now() - datetime.timedelta(minutes=1), 'ips': [['88.250.248.72'], ['78.128.254.195']]}
    #     da_alert4 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.datetime.now() - datetime.timedelta(minutes=5), 'ips': [['88.250.248.72'], ['78.128.254.195']]}
    #     da_alert5 = {'node': ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea'], 'score': 1, 'time': datetime.datetime.now() - datetime.timedelta(minutes=100), 'ips': [['88.250.248.72'], ['78.128.254.195']]}
    #     ad = AlertDatabase()
    #     ad.add(da_alert)
    #     ad.add(da_alert1)
    #     ad.add(da_alert2)
    #     ad.add(da_alert3)
    #     ad.add(da_alert4)
    #     ad.add(da_alert5)
    #     print(ad.database())
    #     #print("XOXO")
    #     #print(ad.database()["S88.250.248.71"]["alerts"])
    #     ad.add(da_alert2)


if __name__ == '__main__':
    unittest.main()

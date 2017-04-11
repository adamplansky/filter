
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/filter" )

# sys.path.insert(0, '/Users/adamplansky/Desktop/filter_dpp/filter')
# sys.path.insert(0, '/Users/adamplansky/Desktop/filter_dpp')
# sys.path.insert(0, '/Users/adamplansky/Desktop/filter_dpp/test',)
#


from filter import AlertDatabase, AlertExtractor
#import datetime
from datetime import datetime, timedelta
import pytz
import random

def get_random_valid_time():
    random_int = random.randint(1, 55)
    return datetime.now(pytz.utc) - timedelta(minutes=random_int)


class MyTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('MyTest.__init__')
        unittest.TestCase.__init__(self, *args, **kwargs)
    # def __init__(self):
        self.ad = AlertDatabase("../config/static_prices.json")
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[u'201.214.56.9'],[u'195.113.253.123']],'category': [u'Recon.Scanning'],'time':get_random_valid_time()})

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

    def get_last_category_array(self):
        self.ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],'ips': [[],[u'195.113.253.123']],'category': [u'Recon.Searching'],'time':datetime.now(pytz.utc)})
        self.assertEqual(self.ad.get_last_category_array(u'201.214.56.9'),[u'Recon.Searching'])

    # def test_get_max_score(self):
    #     ad = AlertDatabase("../config/static_prices.json")
    #     ad.add({'node': [u'cz.cesnet.au1.warden_filer', u'cz.cesnet.labrea'],
    #             'ips': [[u'201.214.56.9'], [u'195.113.253.123']],
    #             'category': [u'Recon.Scanning'],
    #             'time':datetime.now(pytz.utc) - timedelta(minutes=15)}
    #             #'time': datetime(2017, 4, 11, 11, 25, 57, tzinfo=pytz.UTC)}
    #            )
    #     self.assertEqual(ad.get_max_score("S201.214.56.9"), 1)
    #     # self.assertEqual(ad.get_last_category_array("S1.2.3.4"),4)

if __name__ == '__main__':
    unittest.main()

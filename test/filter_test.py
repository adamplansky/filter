
import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from filter.filter import AlertDatabase
import datetime

class MyTest(unittest.TestCase):
    def test_get_max_score(self):
        ad = AlertDatabase()
        a = [[datetime.datetime(2017, 2, 14, 6, 49, 33), 4, ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea']], [datetime.datetime(2017, 2, 14, 6, 49, 33), 3, ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea']]]
        ad.database["S1.2.3.4"] = a
        self.assertEqual(ad.get_max_score("S1.2.3.4"), 4)

    def test_get_max_score_1(self):
        ad = AlertDatabase()
        b = [[datetime.datetime(2017, 2, 14, 6, 49, 33), 10, ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea']], [datetime.datetime(2017, 2, 14, 6, 49, 33), 3, ['cz.cesnet.au1.warden_filer', 'cz.cesnet.labrea']]]
        ad.database["S1.2.3.5"] = b
        self.assertEqual(ad.get_max_score("S1.2.3.5"), 10)

if __name__ == '__main__':
    unittest.main()

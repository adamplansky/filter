from idea_generator import IdeaGenerator
from datetime import datetime, date

import json
class AlertGenerator(IdeaGenerator):
    def create_alert(self):
        alert = {}
        alert['ID'] = self.get_id()
        alert['Source'] = [self.get_source_json()]
        alert['Category'] = [self.get_category_json()]
        alert['CreateTime'],  alert['DetectTime'] = self.get_detect_and_create_time_json()
        alert['Format'] = self.get_format_json()
        return json.dumps(alert)

    def get_source_json(self):
        alert = {}
        alert['IP4'] = self.get_n_ipv4(5)
        return alert

    def get_category_json(self):
        return self.get_category()

    #DetectTime is mandatory, CreateTime is optional
    def get_detect_and_create_time_json(self):
        dt = self.get_detect_time()
        ct = self.get_create_time(dt)
        return [ ct.strftime("%Y-%m-%d %H:%M:%S%Z"), dt.strftime("%Y-%m-%d %H:%M:%S%Z") ]

    def get_format_json(self):
        return "IDEA0"


ag = AlertGenerator()
print(ag.create_alert())

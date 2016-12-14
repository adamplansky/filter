import itertools
import uuid
import random
from datetime import datetime, date, timedelta
import datetime
from faker import Factory
# faker doc: https://faker.readthedocs.io/en/latest/providers/faker.providers.date_time.html

class IdeaGenerator:
    def __init__(self):
        self.fake = Factory.create()

    def get_ipv4(self):
        return self.fake.ipv4(network=False)

    def get_ipv6(self):
        return self.fake.ipv6(network=False)

    def get_n_ips(self, n, fun):
        ary = []
        for _ in itertools.repeat(None, n):
            ary.append( fun() )
        return ary

    def get_n_ipv4(self, n):
        return self.get_n_ips(n, self.get_ipv4)

    def get_n_ipv6(self, n):
        return self.get_n_ips(n, self.get_ipv6)

    def get_id(self):
        return str(uuid.uuid4())

    def get_time(self, start_date_param = "-30m", end_date_param = 'now'):
        return self.fake.date_time_between(start_date=start_date_param, end_date=end_date_param, tzinfo=None)
    def get_detect_time(self):
        return self.get_time()
    def get_create_time(self, detect_time_param):
        return self.get_time(detect_time_param-datetime.timedelta(minutes=15),detect_time_param)

    def get_category(self):
        return random.choice( self.get_category_list() )

    def get_category_list(self):
        return [
        "Abusive.Spam",
        "Abusive.Harassment",
        "Abusive.Child",
        "Abusive.Sexual",
        "Abusive.Violence",
        "Malware.Virus",
        "Malware.Worm",
        "Malware.Trojan",
        "Malware.Spyware",
        "Malware.Dialer",
        "Malware.Rootkit",
        "Recon.Scanning",
        "Recon.Sniffing",
        "Recon.SocialEngineering",
        "Recon.Searching",
        "Attempt.Exploit",
        "Attempt.Login",
        "Attempt.NewSignature",
        "Intrusion.AdminCompromise",
        "Intrusion.UserCompromise",
        "Intrusion.AppCompromise",
        "Intrusion.Botnet",
        "Availability.DoS",
        "Availability.DDoS",
        "Availability.Sabotage",
        "Availability.Outage",
        "Information.UnauthorizedAccess",
        "Information.UnauthorizedModification",
        "Fraud.UnauthorizedUsage",
        "Fraud.Copyright",
        "Fraud.Masquerade",
        "Fraud.Phishing",
        "Fraud.Scam",
        "Vulnerable.Open",
        "Vulnerable.Config",
        "Anomaly.Traffic",
        "Anomaly.Connection",
        "Anomaly.Protocol",
        "Anomaly.System",
        "Anomaly.Application",
        "Anomaly.Behaviour",
        "Other",
        "Test",
    ]

# wg = IdeaGenerator()
# print(wg.get_n_ipv4(5))
# print(wg.get_n_ipv6(5))
# print(wg.get_detect_time())
# print(wg.get_id())
# print(wg.get_category())

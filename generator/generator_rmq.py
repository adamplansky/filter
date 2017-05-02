#!/usr/bin/env python3
#Tomas Cejka kancelar: A-1056
import json
import random
from uuid import uuid4
from pprint import pprint
import time
from time import sleep
from dateutil import parser
from time import gmtime, time
#python idea_sender.py -i 'u:hoststats-alerts,u:amplification-alerts,u:bruteforce-alerts,u:haddrscan-alerts,u:vportscan-alerts'
import pika
import json
import os
import pytrap
import sys
i = 0

def getRandomId():
    """Return unique ID of IDEA message. It is done by UUID in this implementation."""
    return str(uuid4())

def get_date_iso(dt):
    return '%04d-%02d-%02dT%02d:%02d:%02dZ' % dt[0:6]


JSONS_PROCESSED_PATH = '../jsons/'
def dump_json_to_file(data, uuid = False):

    if uuid == True:
        file_name = getRandomId()
    else:
        file_name = data["ID"]

    file_name =  JSONS_PROCESSED_PATH + file_name + ".json"
    print("filename " + file_name)

    with open(file_name, 'w') as outfile:
        json.dump(data, outfile)

def get_randomint():
    #return 1
    #return 500
    return random.randint(1,50)


credentials = pika.PlainCredentials(os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])
parameters = pika.ConnectionParameters(host="localhost", port=5672, virtual_host='/', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='broadcast_idea', exchange_type='fanout')

#FILENAME1 = 'warden_161001_161007_sorted.json'
FILENAME1 = 'warden_data.json'
FILENAME1 = 'warden_01_sorted_remove_test_NEMEA'

#FILENAME1 = 'warden_161001_161007.json'
with open(FILENAME1) as fin:
    alert_in_second = get_randomint()
    for line in fin:
        try:
            if(i == alert_in_second):
                alert_in_second = get_randomint()
                i = 0
                #sleep(1)

            data = json.loads(line)
            # pprint("{} {}".format(data["CreateTime"],data["DetectTime"]))
            dt = parser.parse(data["DetectTime"])
            if data.get("CreateTime"):
                ct = parser.parse(data["CreateTime"])

            diff_ct_dt = (ct - dt).seconds
            print("ct:{} dt:{} diff: {}".format(ct,dt, diff_ct_dt))
            t = time()
            detect_time_g = gmtime(t - diff_ct_dt)
            create_time_g = gmtime(t)
            detect_time_iso = get_date_iso(detect_time_g)
            create_time_iso = get_date_iso(create_time_g)
            print("ct:{} dt:{}".format(create_time_iso, detect_time_iso))
            #print('-------')
            data["DetectTime"] = detect_time_iso
            if data.get("CreateTime"):
                data["CreateTime"] = create_time_iso
            else:
                data["CreateTime"] = get_date_iso(gmtime())
            pprint("ip: {}, ct:{}, ct:{}, diff: {}, category: {}".format(data["Source"],data["CreateTime"],data["DetectTime"],diff_ct_dt,data["Category"]))
            i+=1

            message = json.dumps(data.decode('utf-8').encode('utf-8'))
            print(message)
            channel.basic_publish(exchange='broadcast_idea',routing_key='',body=message)
            print(" [x] Sent 'IDEA Alert'")

            #dump_json_to_file(data, uuid = True)
        except Exception:
            pass

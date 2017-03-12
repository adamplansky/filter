# #!/usr/bin/env python
#python idea_sender.py -i 'u:hoststats-alerts,u:amplification-alerts,u:bruteforce-alerts,u:haddrscan-alerts,u:vportscan-alerts'
import pika
import json
import os
import pytrap
import sys

trap = pytrap.TrapCtx()
ifc_input_len = len(sys.argv[2].split(","))
trap.init(sys.argv, ifc_input_len, 0)
inputspec = "IDEA"
trap.setRequiredFmt(0, pytrap.FMT_JSON, inputspec)

credentials = pika.PlainCredentials(os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])
parameters = pika.ConnectionParameters(host="localhost", port=5672, virtual_host='/', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='broadcast_idea', exchange_type='fanout')

while True:
    try:
        data = trap.recv()
        message = json.dumps(data.decode('utf-8').encode('utf-8'))
        print(message)
        channel.basic_publish(exchange='broadcast_idea',routing_key='',body=message)
        print(" [x] Sent 'IDEA Alert'")

    except pytrap.FormatChanged as e:
        fmttype, inputspec = trap.getDataFmt(0)
        data = e.data
    if len(data) <= 1:
        break


# close RABBITMQ connection
connection.close()
# Free allocated TRAP IFCs
trap.finalize()

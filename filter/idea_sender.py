# #!/usr/bin/env python
# python idea_sender.py -i 'u:hoststats-alerts,u:amplification-alerts'
import pika
import ssl
import json
import os
import pytrap
import sys

trap = pytrap.TrapCtx()
ifc_input_len = len(sys.argv[2].split(","))
trap.init(sys.argv, ifc_input_len, 0)
inputspec = "IDEA"
trap.setRequiredFmt(0, pytrap.FMT_JSON, inputspec)

ssl_options = {
    "ca_certs":"/home/nemea/cacert.pem",
    "certfile": "/home/nemea/client/cert.pem",
    "keyfile": "/home/nemea/client/key.pem",
    "cert_reqs": ssl.CERT_REQUIRED,
    "ssl_version":ssl.PROTOCOL_TLSv1_2
}
credentials = pika.PlainCredentials(os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])
parameters = pika.ConnectionParameters(host='192.168.2.120', port=5671, virtual_host='/', heartbeat_interval = 0, credentials=credentials, ssl = True, ssl_options = ssl_options)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='broadcast_idea', exchange_type='fanout')

while True:
    try:
        data = trap.recv()
        message = json.dumps(data.decode('utf-8').encode('utf-8'))
        channel.basic_publish(exchange='broadcast_idea',routing_key='',body=message)
        print(" [x] Sent 'IDEA Alert'")

    except pytrap.FormatChanged as e:
        fmttype, inputspec = trap.getDataFmt(0)
        data = e.data
    except Exception as e:
        print(e)
    if len(data) <= 1:
        break


# close RABBITMQ connection
connection.close()
# Free allocated TRAP IFCs
trap.finalize()

import json
import sys
import os
from os.path import dirname as dirn
import glob
from jq import jq
from pprint import pprint


json_idea = {"Node": [{"Type": ["Relay"], "Name": "cz.cesnet.ftas"}, {"SW": ["FTAS"], "Name": "cz.cesnet.gc15", "Tags": ["Flow"]}], "WinStartTime": "2016-10-05T14:08:06+02:00", "Description": "TCP SYN against internal IP address ranges, sources - DETECTED traffic anomaly", "AvgPacketSize": 48, "Format": "IDEA0", "WinEndTime": "2016-10-05T14:08:09+02:00", "Category": ["Anomaly.Traffic"], "CreateTime": "2016-10-05T14:08:42+02:00", "Note": "206.191.151.226 (source IP) - found 4830 flows (limit 'Flow-Cnt>=1000 flows/s or Flow-Cnt>=0.333 flows/s and Pkts-estimated>=1000 p/s') within period of 3 seconds. Next message not before 16/10/05 14:09:39 CEST +0200 in case of continuous detection. Notes - detector uses extrapolated values (bytes, packets, flowcnt) in case of sampled flows; detector fragments long (duration) flows into 3s intervals for evaluation purposes.", "Source": [{"Proto": ["tcp"], "PortCount": 1, "ProtoCount": 1, "IP4": ["206.191.151.226"], "Type": ["Incomplete"], "Port": [28331]}], "ByteCount": 231840, "FlowCount": 4830, "PacketCount": 4830, "DetectTime": "2016-10-05T14:08:42+02:00", "Duration": 0, "Ref": ["https://ftas.cesnet.cz/ftas/stat.pl?select_output=1212&select_output-use=yes&query_style=advanced&advanced_query=src_ip=206.191.151.226&first=2016%2F10%2F05%2014%3A07%3A06&last=2016%2F10%2F05%2014%3A09%3A07&use_all_fields=1"], "ID": "1475669322_gc15.cesnet.cz_1212_src_ip_206.191.151.226", "Attach": [{"Content": "Forwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.7   tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.11  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.19  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.22  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.8   tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.38  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.55  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.59  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.43  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.72  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.88  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.87  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.109 tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.99  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.18  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.85  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.2   tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.127 tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.13  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61\nForwarded: 206.191.151.226 tcp(6)/28331 --> 195.113.114.15  tcp(6)/ssh(22): 48/96 B, 1/2 p, 48 Bpp, 12:08:06[GMT], 14:08:06[CEST +0200], +0.000000 s, tos=00000000, tcp_flags=syn(2), flow_source=Hradec Kralove: R129(25), src_if=91744, dst_if=61", "Note": "Traffic sample (20 records max.)", "ContentType": "text/csv"}], "Target": [{"PortCount": 1, "Proto": ["tcp"], "ProtoCount": 1, "Note": "Counts are measured up to 4 distinct values; arrays are cropped to 2 distinct values.", "IP4": ["195.113.114.11", "195.113.114.19"], "IP4Count": 4, "Type": ["Incomplete"], "Port": [22]}]}

ROOT_PATH = os.path.realpath(dirn(os.path.abspath(__file__)))
CFG_JSON_PATH = ROOT_PATH + '/mapping'


formats = {}
mapping_formats = {}
ary_from = []
ary_to = []

def remove_ws(str):
    return str.strip().replace('\"', '')


if __name__ == '__main__':
    with open(CFG_JSON_PATH) as data_file:
        for line in data_file:
            if(line == '\n'):
                jq = ', '.join([str(x) for x in ary_from])
                #mapping_formats[val] =
                formats[key] = {val: {"jq": jq, "map_to": ary_to}}
                ary_from = []
                ary_to = []
            elif(line[0] == "\""):
                format_json = line.split("==")
                key = remove_ws(format_json[0])
                val = remove_ws(format_json[1])
                formats[key] = {}
            else:
                mapping_json = line.split("->")
                mapping_key = remove_ws(mapping_json[0])
                mapping_val = remove_ws(mapping_json[1])
                ary_from.append(mapping_key)
                ary_to.append(mapping_val)
    jq = ', '.join([str(x) for x in ary_from])
    #mapping_formats[val] = {"jq": '\"' + jq + '\"', "map_to": ary_to}
    #pprint(mapping_formats)
    formats[key] = {val: {"jq": jq, "map_to": ary_to}}
    #jq_str = str(formats[".Format"]["IDEA0"]["jq"])


    #print(json_idea.__class__, jq_str)
    #print(jq(".").transform(text="42") )

from jq import jq
# jq_str = formats[".Format"]["IDEA0"]["jq"]
# print(jq_str)#print(jq_str, json_idea)
# jq_output = jq(jq_str).transform(json_idea, multiple_output=True)
# format_hash = {}
# idea = {}
# for val in jq_output:
#     print(val)
#
# pprint(jq_output)

#print(formats)

def get_first_key(my_dict):
    return next(iter(my_dict))
def handle_idea(idea_alert):
    for k in formats.keys():
        kk = get_first_key(formats[k])
        if(jq(k).transform(json_idea, multiple_output=True)[0] == kk):
            print("bingo")
            hash_out = formats[k][kk]
            jq_output = jq(hash_out["jq"]).transform(idea_alert, multiple_output=True)
            hash_formated = {}
            for x in range(0, len(jq_output)):
                hash_formated[hash_out["map_to"][x]] = jq_output[x]
            print(hash_formated)
            print(hash_formated["Source"])

handle_idea(json_idea)

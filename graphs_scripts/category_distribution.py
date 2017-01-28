#!/usr/bin/env python3
import logging
import json
import matplotlib.pyplot as plt
import sys
import matplotlib.ticker as mticker
import operator
#cat warden_161001_161007.json | jq '.Category[] ' | sort | uniq -c > pie_category_preprocess.csv
#usage: python3 category_distribution.py pie_category_preprocess.csv category.png
"""
 input file must have this syntax ()
 8862 "Abusive.Spam"
  34 "Anomaly.Connection"
  12 "Anomaly.Protocol"
14927 "Anomaly.Traffic"
84373 "Attempt.Exploit"
146101 "Attempt.Login"
   1 "Availability.DDoS"
 881 "Availability.DoS"
62745 "Intrusion.Botnet"
8020 "Malware"
3264 "Other"
15869516 "Recon.Scanning"
1662 "Vulnerable.Config"
"""

labels = []
sizes = []
data_set = {}
with open(sys.argv[1]) as infile:
    for line in infile:
        data = line.strip().split(" ")
        if data[0] == "#":continue
        label = data[1].replace("'", "").replace("\"", "")
        size = int(data[0])
        data_set[label] = size

sorted_data = sorted(data_set.items(), key=operator.itemgetter(0))
labels = [ x[0] for x in sorted_data]
sizes = [ x[1] for x in sorted_data]
fig1, ax1 = plt.subplots()
patches, texts = ax1.pie(sizes, startangle=90, radius=1.2)
porcent = []
summ = sum(sizes)
for val in sizes:
    porcent.append(100.*val/summ)

labels = ['{0} - {1:1.6f} %'.format(i,j) for i,j in zip(labels, porcent)]
sort_legend = True
if sort_legend:
    patches, labels, dummy =  zip(*sorted(zip(patches, labels, sizes),
                                          key=lambda x: x[2],
                                          reverse=True))

plt.legend(patches, labels, loc='lower left',
           fontsize=8)

plt.savefig(sys.argv[2])

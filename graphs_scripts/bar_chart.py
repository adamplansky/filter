#!/usr/bin/env python3
import logging
import json
import matplotlib.pyplot as plt
import sys
import matplotlib.ticker as mticker
import operator

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
ax1.bar(sizes,sizes)
plt.xticks(labels)
plt.savefig(sys.argv[2])

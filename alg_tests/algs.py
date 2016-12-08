#!/usr/bin/env python3

import random
import heapq
import pprint
from math import log


first = lambda h: 2**h - 1      # H stands for level height
last = lambda h: first(h + 1)
level = lambda heap, h: heap[first(h):last(h)]
prepare = lambda e, field: str(e).center(field)


def hprint(heap, width=None):
    if width is None:
        width = max(len(str(e)) for e in heap)
    height = int(log(len(heap), 2)) + 1
    gap = ' ' * width
    for h in range(height):
        below = 2 ** (height - h - 1)
        field = (2 * below - 1) * width
        print(gap.join(prepare(e, field) for e in level(heap, h)))


# class FirstList(tuple):
#     def __lt__(self, other):
#         return self[1] < other[1]

t1 = (5, ['6.1.2.7'])
t2 = (5, ['6.1.2.7'])
t3 = (5, ['6.1.2.7'])

ary = []
heapq.heappush(ary,t1)
heapq.heappush(ary,t2)
heapq.heappushpop(ary,t3)
print(ary)


# class MyHeap(heapq):
#     #how many probes do I have?
#     #PROBES_CAPACITY = 5
#     def __init__(self):
#         pass
#         #super(CurrentClass, self)
#         #self.heap = []
#     def heapify(self, ary):
#         pass
#     def add(self, threat):
#         pass
#
# ary = []
# d = {"K":123}
# predef = (5, d)
# ary.append( predef )
# ary.append( predef )
# for i in range(10):
#     ary.append( random.randint(1, 100) )
#
# print(ary)
#
# hp = MyHeap()
# hp.heapify(ary)
# print(ary)
# hprint(ary)

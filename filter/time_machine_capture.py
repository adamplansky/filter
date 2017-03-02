#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################
## COMMUNICATION PROTOCOL START
###############################################################

import ipaddr
import time
import struct

# import tm_shell

from socket import error as socket_error
REQ_ADD = 0
REQ_REMOVE = 1
REQ_LIST = 2
REQ_DETAIL = 3
REQ_HISTORY_BUFFER = 4
REQ_INFO = 5
REQ_QUIT = 6
REQ_HS = 7

TARGET_SRC_IP = 0
TARGET_DST_IP = 1
TARGET_BIDIR_IP = 2
TARGET_ALL = 3
TURN_ON = 4
TURN_OFF = 5
INFO = 6
AUTO = 7
MANUAL = 8

MSG_MONITORING = 1
MSG_INCIDENT = 2
MSG_CAPTURE = 3
MSG_VISUAL = 4

VERSION_MAJOR = 0
VERSION_MINOR = 9

RES_SUCCESS = 0
RES_FAIL = 1
RES_INVALID = 2
RES_LIST = 3
RES_DETAIL = 4
RES_HB_INFO = 5
RES_INFO = 6

IP4PREFIX = '\x00\x00\x00\x00\x00\x00\x00\x00'
IP4POSTFIX = "\xFF\xFF\xFF\xFF"
MAX_UNIT32 = 4294967295


def direction_to_string(direction):
    direction_str = 'Unknown direction'
    if direction == TARGET_SRC_IP:
        direction_str = 'source ip'
    elif direction == TARGET_DST_IP:
        direction_str = 'destination ip'
    elif direction == TARGET_BIDIR_IP:
        direction_str = 'bidirectional ip'
    return direction_str


class Ip:

    def __init__(self, ip):
        self._ip = ip

    def __str__(self):
        if self._ip[:4] == bytearray(IP4POSTFIX) and self._ip[8:] \
            == bytearray(IP4PREFIX):

         # IPv4 convert

            ip = struct.unpack('<L', self._ip[4:8])[0]

         # return string

            return str(ipaddr.IPv4Address(ip))
        else:

         # IPv6 convert

            (ip1, ip2) = struct.unpack('<QQ', self._ip)

         # return string

            return str(ipaddr.IPv6Address(ip2 << 64 | ip1))

    def __hash__(self):
        return hash(self._ip)

    def __eq__(self, other):
        return self._ip == other._ip

    def __ne__(self, other):

      # Not strictly necessary, but to avoid having both x==y and x!=y
      # True at the same time

        return not self == other

    def pack(self):
        return self._ip

    @staticmethod
    def recv(sock):
        return Ip(sock.recv(16))

    @staticmethod
    def from_str(key_str):
        try:
            key = ipaddr.IPv4Address(key_str).packed
            key = IP4POSTFIX + key[::-1] + IP4PREFIX
        except ValueError:
            try:
                key = ipaddr.IPv6Address(key_str).packed[::-1]
            except ValueError:
                raise ValueError('String ' + key_str
                                 + ' could not be changed to Ip.')
        return Ip(key)


class Message(object):

    @staticmethod
    def recv_struct(sock, fmt):
        data = sock.recv(struct.calcsize(fmt))
        if not data:
            raise socket_error
        return struct.unpack(fmt, data)

    def send(self, sock):
        sock.send(self.pack())

    @staticmethod
    def recv(sock):
        (version_major, version_minor) = Message.recv_struct(sock, '<BB'
                )
        if version_major != VERSION_MAJOR or version_minor \
            != VERSION_MINOR:
            raise ValueError('ERROR: received another type of version')
        return None

    def pack(self):
        return struct.pack('<BB', VERSION_MAJOR, VERSION_MINOR)


# ===================================
# REPLY class and it's subclasses

class Reply(Message):

    def __init__(self, type):
        self.type = type

    @staticmethod
    def type_to_class(type):
        if type == RES_SUCCESS:
            return Reply_success
        elif type == RES_FAIL:
            return Reply_fail
        elif type == RES_LIST:
            return Reply_list
        elif type == RES_DETAIL:
            return Reply_detail
        elif type == RES_HB_INFO:
            return Reply_hc_info
        elif type == RES_INFO:
            return Reply_info
        elif type == RES_INVALID:
            return Reply_invalid
        else:
            raise ValueError('Unknown response type: ' + str(type))

    @staticmethod
    def recv(sock):
        Message.recv(sock)
        type = Message.recv_struct(sock, '<H')[0]
        return Reply.type_to_class(type).recv(sock)

    def pack(self):
        return super(Reply, self).pack() + struct.pack('<H', self.type)


class Reply_success(Reply):

    def __init__(self):
        super(Reply_success, self).__init__(RES_SUCCESS)

    @staticmethod
    def recv(sock):
        return Reply_success()

    def __str__(self):
        return 'Operaction was successfull\n'


class Reply_fail(Reply):

    def __init__(self):
        super(Reply_fail, self).__init__(RES_FAIL)

    @staticmethod
    def recv(sock):
        return Reply_fail()

    def __str__(self):
        return 'Operaction failed\n'


class Reply_invalid(Reply):

    def __init__(self):
        super(Reply_invalid, self).__init__(RES_INVALID)

    @staticmethod
    def recv(sock):
        return Reply_invalid()

    def __str__(self):
        return 'Unknown operation\n'


class Reply_list(Reply):

    def __init__(self, addr_list):
        super(Reply_list, self).__init__(RES_LIST)
        self.addr_list = addr_list

    @staticmethod
    def aggregate(arr):
        aggr_addr = []

      # for all Reply_list items that are in the array

        for ls in arr:

         # for all items in one object of Reply_list

            for addr in ls.addr_list:

            # if address is not in the list -> add it to the list

                if addr not in aggr_addr:
                    aggr_addr.append(addr)
        return Reply_list(aggr_addr)

    @staticmethod
    def recv(sock):
        length = Message.recv_struct(sock, '<I')[0]
        addr_list = []
        for _ in xrange(length):

         # recv IP

            ip = Ip.recv(sock)

         # recv direction

            direction = Message.recv_struct(sock, '<B')[0]

         # append

            addr_list.append([ip, direction])
        return Reply_list(addr_list)

    def pack(self):
        packed = super(Reply_list, self).pack()
        packed += struct.pack('<I', len(self.addr_list))
        for addr in self.addr_list:

         # pack IP

            packed += addr[0].pack()

         # pack direction

            packed += struct.pack('<B', addr[1])

         # packed += struct.pack("<BB", addr[1], addr[2])

        return packed

    def __str__(self):
        ret = 'List of length ' + str(len(self.addr_list)) + ':' + '\n'
        for addr in self.addr_list:
            ret += direction_to_string(addr[1]) + ' ' + str(addr[0]) \
                + '\n'
        return ret


class Reply_detail(Reply):

    def __init__(
        self,
        ip,
        direction,
        hc_progress,
        lc_packets,
        lc_limit,
        act_time,
        timeout,
        filenames,
        ):
        super(Reply_detail, self).__init__(RES_DETAIL)
        self.ip = ip
        self.direction = direction
        self.hc_progress = hc_progress
        self.lc_packets = lc_packets
        self.lc_limit = lc_limit
        self.act_time = act_time
        self.timeout = timeout
        self.filenames = filenames

      # remember timeout time for string

        self.timeout_time = time.localtime(time.time() + timeout
                - act_time)

    @staticmethod
    def aggregate(arr, capture_name=None, finished_cur_packets=0):
        ip = arr[0].ip
        direction = arr[0].direction
        hc_progress = arr[0].hc_progress
        lc_packets = arr[0].lc_packets + finished_cur_packets
        lc_limit = arr[0].lc_limit + finished_cur_packets
        act_time = arr[0].act_time
        timeout = arr[0].timeout
        filenames = arr[0].filenames
        for det in arr[1:]:

         # sum packets

            lc_limit += det.lc_limit
            lc_packets += det.lc_packets

         # find the smallest probress of hc

            if hc_progress > det.hc_progress:
                hc_progress = det.hc_progress

         # find the biggest difference between timeout and act_time (longest time)

            if timeout - act_time < det.timeout - det.act_time:
                timeout = det.timeout
                act_time = det.act_time
            filenames += ',' + det.filenames

      # check right range of variables

        if lc_limit > MAX_UNIT32:
            lc_limit = MAX_UNIT32
        if lc_packets > MAX_UNIT32:
            lc_packets = MAX_UNIT32
        if capture_name:
            filenames = capture_name
        return Reply_detail(
            ip,
            direction,
            hc_progress,
            lc_packets,
            lc_limit,
            act_time,
            timeout,
            filenames,
            )

    @staticmethod
    def recv(sock):
        ip = Ip.recv(sock)
        (
            direction,
            hc_progress,
            lc_packets,
            lc_limit,
            act_time,
            timeout,
            strlen,
            ) = Message.recv_struct(sock, '<BBIIIIB')
        filenames = sock.recv(strlen)
        return Reply_detail(
            ip,
            direction,
            hc_progress,
            lc_packets,
            lc_limit,
            act_time,
            timeout,
            filenames,
            )

    def pack(self):
        packed = super(Reply_detail, self).pack()
        packed += self.ip.pack()
        packed += struct.pack(
            '<BBIIIIB',
            self.direction,
            self.hc_progress,
            self.lc_packets,
            self.lc_limit,
            self.act_time,
            self.timeout,
            len(self.filenames),
            )
        packed += self.filenames
        return packed

    def __str__(self):

      # read IP address

        ret = 'IP: ' + str(self.ip) + '\n'
        ret += 'Direction: ' + direction_to_string(self.direction) \
            + '\n'
        ret += 'History capture progress: ' + str(self.hc_progress) \
            + '%' + '\n'
        if self.lc_limit != MAX_UNIT32:
            ret += 'Packets captured: ' + str(self.lc_packets) + ' / ' \
                + str(self.lc_limit) + '\n'
        else:
            ret += 'Packets captured: ' + str(self.lc_packets) + '\n'
        if self.timeout != MAX_UNIT32:
            ret += 'Capturing time: ' \
                + str((self.act_time if self.act_time
                      <= self.timeout else self.timeout)) + 's / ' \
                + str(self.timeout) + 's' + '\n'
            ret += 'Rule will timeout on ' \
                + time.strftime('%Y-%m-%d %H:%M:%S', self.timeout_time) \
                + '\n'
        else:
            ret += 'Capturing time: ' + str(self.act_time) + 's' + '\n'

      # read name of destination files group

        ret += 'Capture name: ' + self.filenames + '\n'
        if self.lc_packets >= self.lc_limit or self.act_time \
            >= self.timeout:
            ret += 'Live Capture finished!\n'
        return ret


class Reply_hc_info(Reply):

    def __init__(
        self,
        hc_count,
        packets,
        avg_time_len,
        min_time_len,
        max_time_len,
        active_request_count,
        heavy_size,
        queue_length,
        free_mem,
        ):
        super(Reply_hc_info, self).__init__(RES_HB_INFO)
        self.hc_count = hc_count
        self.packets = packets
        self.avg_time_len = avg_time_len
        self.min_time_len = min_time_len
        self.max_time_len = max_time_len
        self.active_request_count = active_request_count
        self.heavy_size = heavy_size
        self.queue_length = queue_length
        self.free_mem = free_mem

    @staticmethod
    def aggregate(arr):
        hc_count = arr[0].hc_count
        packets = arr[0].packets
        avg_time_len = arr[0].avg_time_len
        min_time_len = arr[0].min_time_len
        max_time_len = arr[0].max_time_len
        active_request_count = arr[0].active_request_count
        heavy_size = arr[0].heavy_size
        queue_length = arr[0].queue_length
        free_mem = arr[0].free_mem
        for inf in arr[1:]:

         # sum of hc count

            hc_count += inf.hc_count

         # sum of len

            avg_time_len += inf.avg_time_len

         # min time

            min_time_len = min(min_time_len, inf.min_time_len)

         # max time

            max_time_len = max(max_time_len, inf.max_time_len)

         # sum of requsts count

            active_request_count += inf.active_request_count

         # min of heavy size

            heavy_size = min(heavy_size, inf.heavy_size)

         # sum of queue length

            queue_length += inf.queue_length

         # sum of free mem

            free_mem += inf.free_mem

         # sum of packets

            packets += inf.packets

      # make avarage from avg time

        avg_time_len /= len(arr)
        return Reply_hc_info(
            hc_count,
            packets,
            avg_time_len,
            min_time_len,
            max_time_len,
            active_request_count,
            heavy_size,
            queue_length,
            free_mem,
            )

    @staticmethod
    def recv(sock):
        (
            hc_count,
            packets,
            avg_time_len,
            min_time_len,
            max_time_len,
            active_request_count,
            heavy_size,
            queue_length,
            free_mem,
            ) = Message.recv_struct(sock, '<IIIIIIIQQ')
        return Reply_hc_info(
            hc_count,
            packets,
            avg_time_len,
            min_time_len,
            max_time_len,
            active_request_count,
            heavy_size,
            queue_length,
            free_mem,
            )

    def pack(self):
        packed = super(Reply_hc_info, self).pack()
        packed += struct.pack(
            '<IIIIIIIQQ',
            self.hc_count,
            self.packets,
            self.avg_time_len,
            self.min_time_len,
            self.max_time_len,
            self.active_request_count,
            self.heavy_size,
            self.queue_length,
            self.free_mem,
            )
        return packed

    def __str__(self):
        if self.queue_length == 0:
            ret = \
                'History buffer is turned off. Use "history_capture turn_on [SIZE MB]" to turn on capturing to the buffer.' \
                + '\n'
            return ret
        else:
            ret = 'History buffer instances: ' + str(self.hc_count) \
                + '\n'
            ret += 'Buffer size: ' + str(self.queue_length / (1024
                    * 1024)) + ' MB' + '\n'
            ret += 'Heavy size: ' + str(self.heavy_size) + '\n'
            ret += 'Buffer size of one instance: ' \
                + str(self.queue_length / (1024 * 1024
                      * self.hc_count)) + ' MB' + '\n'
            ret += 'Free memory: ' + ((str(self.free_mem / (1024
                    * 1024)) + ' MB' if self.free_mem / (1024 * 1024)
                    != 0 else str(self.free_mem) + ' B')) + '\n'
            ret += 'Buffer load: ' + '%0.2f' % ((self.queue_length
                    - self.free_mem) / float(self.queue_length) * 100) \
                + ' %\n'
            ret += 'Packets captured: ' + str(self.packets) + '\n'
            ret += 'Avarage time captured: ' + str(self.avg_time_len) \
                + ' s,\t(' + '%0.2f' % (self.avg_time_len / float(60)) \
                + ' min)' + '\n'
            ret += 'Minimum time captured: ' + str(self.min_time_len) \
                + ' s,\t(' + '%0.2f' % (self.min_time_len / float(60)) \
                + ' min)' + '\n'
            ret += 'Maximum time captured: ' + str(self.max_time_len) \
                + ' s,\t(' + '%0.2f' % (self.max_time_len / float(60)) \
                + ' min)' + '\n'
            ret += 'Active requset count: ' \
                + str(self.active_request_count) + '\n'
            return ret


class Reply_info(Reply):

    def __init__(self, inf_type):
        super(Reply_info, self).__init__(RES_INFO)
        self.inf_type = inf_type

    @staticmethod
    def type_to_class(type):
        if type == MSG_CAPTURE:
            return Reply_info_progress
        elif type == MSG_INCIDENT:
            return Reply_info_new
        elif type == MSG_VISUAL:
            return Reply_info_done
        else:
            raise ValueError('Unknown response type: ' + str(type))

    @staticmethod
    def recv(sock):
        inf_type = Message.recv_struct(sock, '<B')[0]
        cls = Reply_info.type_to_class(inf_type)
        return cls.recv(sock)

    def pack(self):
        packed = super(Reply_info, self).pack()
        packed += struct.pack('<B', self.inf_type)
        return packed

    def __str__(self):
        ret = 'Info message of type: ' + str(self.inf_type) + '\n'
        return ret


class Reply_info_new(Reply_info):

    def __init__(self, id, ip):
        super(Reply_info_new, self).__init__(MSG_INCIDENT)
        self.id = id
        self.ip = ip

    @staticmethod
    def recv(sock):
        id = Message.recv_struct(sock, '<I')[0]
        ip = Ip.recv(sock)
        return Reply_info_new(id, ip)

    def pack(self):
        packed = super(Reply_info_new, self).pack()
        packed += struct.pack('<I', self.id)
        packed += self.ip.pack()
        return packed

    def __str__(self):
        ret = 'Info message - new incident:\n'
        ret += 'ID = ' + str(self.id) + '\n'
        ret += 'IP = ' + str(self.ip) + '\n'
        return ret


class Reply_info_progress(Reply_info):

    def __init__(self, id, progress):
        super(Reply_info_progress, self).__init__(MSG_CAPTURE)
        self.id = id
        self.progress = progress

    @staticmethod
    def recv(sock):
        (id, progress) = Message.recv_struct(sock, '<IB')
        return Reply_info_progress(id, progress)

    def pack(self):
        packed = super(Reply_info_progress, self).pack()
        packed += struct.pack('<IB', self.id, self.progress)
        return packed

    def __str__(self):
        ret = 'Info message - progress:\n'
        ret += 'ID = ' + str(self.id) + '\n'
        ret += 'progress = ' + str(self.progress) + '\n'
        return ret


class Reply_info_done(Reply_info):

    def __init__(
        self,
        id,
        hist_packets=0,
        cur_packets=0,
        history='',
        current='',
        ):
        super(Reply_info_done, self).__init__(MSG_VISUAL)
        self.id = id
        self.history = history
        self.current = current
        self.cur_packets = cur_packets
        self.hist_packets = hist_packets

    @staticmethod
    def recv(sock):
        (inf_id, hist_packets, cur_packets, len_history, len_current) = \
            Message.recv_struct(sock, '<IIIHH')
        if len_history > 0:
            hist = sock.recv(len_history).decode()
        else:
            hist = ''
        if len_current > 0:
            curr = sock.recv(len_current).decode()
        else:
            curr = ''
        return Reply_info_done(inf_id, hist_packets, cur_packets, hist,
                               curr)

    def pack(self):
        packed = super(Reply_info_done, self).pack()
        packed += struct.pack(
            '<IIIHH',
            self.id,
            self.hist_packets,
            self.cur_packets,
            len(self.history),
            len(self.current),
            )
        if len(self.history) > 0:
            packed += self.history
        if len(self.current) > 0:
            packed += self.current
        return packed

    def __str__(self):
        ret = 'Info message - capture done:\n'
        ret += 'ID = ' + str(self.id) + '\n'
        ret += 'History packets: ' + str(self.hist_packets) \
            + ', Current packets: ' + str(self.cur_packets) + '\n'
        if len(self.history) > 0:
            ret += 'history files = ' + self.history + '\n'
        if len(self.current) > 0:
            ret += 'current files = ' + self.current + '\n'
        return ret


# ===================================
# REQUEST class and it's subclasses

class Request(Message):

    def __init__(self, operation, direction=0):
        self.operation = operation
        self.direction = direction

    @staticmethod
    def type_to_class(operation):
        if operation == REQ_ADD:
            return Request_add
        elif operation == REQ_REMOVE:
            return Request_remove
        elif operation == REQ_LIST:
            return Request_list
        elif operation == REQ_DETAIL:
            return Request_detail
        elif operation == REQ_HISTORY_BUFFER:
            return Request_history_capture
        elif operation == REQ_INFO:
            return Request_info
        elif operation == REQ_HS:
            return Request_heavy_size
        elif operation == REQ_QUIT:
            return Request_quit
        else:
            raise ValueError('Unknown request type: ' + str(operation))

    @staticmethod
    def recv(sock):
        Message.recv(sock)
        (operation, direction) = Message.recv_struct(sock, '<BB')
        return Request.type_to_class(operation).recv(sock, direction)

    def pack(self):
        return super(Request, self).pack() + struct.pack('<BB',
                self.operation, self.direction)


class Request_quit(Request):

    def __init__(self):
        super(Request_quit, self).__init__(REQ_QUIT)

    @staticmethod
    def recv(sock, direction=0):
        return Request_quit()


class Request_add(Request):

    def __init__(
        self,
        addr,
        direction,
        packets,
        timeout,
        filename,
        ):
        super(Request_add, self).__init__(REQ_ADD, direction)
        self.addr = addr
        self.packets = packets
        self.timeout = timeout
        self.filename = filename

    @staticmethod
    def recv(sock, direction):
        addr = Ip.recv(sock)
        (packets, timeout, length) = Message.recv_struct(sock, '<IIB')
        filename = sock.recv(length)
        return Request_add(addr, direction, packets, timeout, filename)

    def pack(self):
        packed = super(Request_add, self).pack()
        packed += self.addr.pack()
        packed += struct.pack('<IIB', self.packets, self.timeout,
                              len(self.filename))
        packed += self.filename
        return packed

    def add_prefix(self, prefix):
        self.filename = prefix + self.filename


class Request_remove(Request):

    def __init__(self, addr, direction):
        super(Request_remove, self).__init__(REQ_REMOVE, direction)
        self.addr = addr
        self.direction = direction

    @staticmethod
    def recv(sock, direction):
        addr = Ip.recv(sock)
        return Request_remove(addr, direction)

    def pack(self):
        packed = super(Request_remove, self).pack()
        packed += self.addr.pack()
        return packed


class Request_list(Request):

    def __init__(self, direction):
        super(Request_list, self).__init__(REQ_LIST, direction)

    @staticmethod
    def recv(sock, direction):
        return Request_list(direction)


class Request_detail(Request):

    def __init__(self, addr, direction):
        super(Request_detail, self).__init__(REQ_DETAIL, direction)
        self.addr = addr

    @staticmethod
    def recv(sock, direction):
        addr = Ip.recv(sock)
        return Request_detail(addr, direction)

    def pack(self):
        packed = super(Request_detail, self).pack()
        packed += self.addr.pack()
        return packed


class Request_history_capture(Request):

    def __init__(self, operation, size=0):
        super(Request_history_capture,
              self).__init__(REQ_HISTORY_BUFFER, operation)
        self.size = size

    @staticmethod
    def recv(sock, direction):
        if direction == TURN_ON:
            size = Message.recv_struct(sock, '<I')[0]
            return Request_history_capture(direction, size)
        return Request_history_capture(direction)

    def pack(self):
        packed = super(Request_history_capture, self).pack()
        if self.direction == TURN_ON:
            packed += struct.pack('<I', self.size)
        return packed


class Request_heavy_size(Request):

    def __init__(self, type, size):
        super(Request_heavy_size, self).__init__(REQ_HS, type)
        self.size = size

    @staticmethod
    def recv(sock, direction):
        size = Message.recv_struct(sock, '<I')[0]
        return Request_heavy_size(direction, size)

    def pack(self):
        packed = super(Request_heavy_size, self).pack()
        packed += struct.pack('<I', self.size)
        return packed


class Request_info(Request):

    def __init__(self, type):
        super(Request_info, self).__init__(REQ_INFO, type)

    @staticmethod
    def recv(sock, direction):
        return Request_info(direction)


# END of REQUEST class and it's subclasses
# ===================================

###############################################################
## COMMUNICATION PROTOCOL END
###############################################################

import cmd
import socket
import sys
import threading

# from communication_protocol import *

from optparse import OptionParser


def print_reply_thr(answer, id, print_header=False):
    stop = False
    while not stop:
        if not isinstance(Sock.print_reply_from(id, print_header),
                          Reply_info):
            stop = True


def propose_target_direction(text):
    result = []

   # propose direction of capture

    if 'src_ip'.startswith(text):
        result.append('src_ip ')
    if 'dst_ip'.startswith(text):
        result.append('dst_ip ')
    if 'bidir_ip'.startswith(text):
        result.append('bidir_ip ')
    return result


def propose_target_list(text, line):
    result = []
    if len(text) != 0 and len(line.split()) != 2:
        return result
    if len(text) == 0 and len(line.split()) != 1:
        return result
    if 'src_ip'.startswith(text):
        result.append('src_ip')
    if 'dst_ip'.startswith(text):
        result.append('dst_ip')
    if 'bidir_ip'.startswith(text):
        result.append('bidir_ip')
    if 'all'.startswith(text):
        result.append('all')
    return result


def propose_ip(text, target=TARGET_BIDIR_IP):
    req = Request_list(TARGET_ALL)
    rep = Sock.send_rep_recv_rep(req, False)
    rep = [x for x in rep if isinstance(x, Reply_list)]
    lst = Reply_list.aggregate(rep)
    len_text = len(text)
    if len(lst.addr_list) > 0:
        res = [str(x[0]) for x in lst.addr_list if target
               == TARGET_BIDIR_IP or target == TARGET_SRC_IP and x[1]
               != TARGET_DST_IP or target == TARGET_DST_IP and x[1]
               != TARGET_SRC_IP]
        if len(res) > 0:
            if len_text == 0:
                return res
            else:
                res = [x for x in res if x.startswith(text)]

            # solve problem with IPv6 (: is not replaceable in complete function)

                if ':' in text:
                    if len(res) == 1:
                        return [(res[0])[text.rindex(':') + 1:]]
                    else:
                        res.append(' ')
                        return res
                else:
                    return res
    return ['<IP address>', ' ']


def get_target(target_str):
    if target_str.lower() == 'src_ip':
        return TARGET_SRC_IP
    elif target_str.lower() == 'dst_ip':
        return TARGET_DST_IP
    elif target_str.lower() == 'bidir_ip':
        return TARGET_BIDIR_IP
    else:
        return None


def get_target_list(target_str):
    if target_str.lower() == 'src_ip':
        return TARGET_SRC_IP
    elif target_str.lower() == 'dst_ip':
        return TARGET_DST_IP
    elif target_str.lower() == 'bidir_ip':
        return TARGET_BIDIR_IP
    elif target_str.lower() == 'all':
        return TARGET_ALL
    else:
        return None


def get_hc_target(target_str):
    if target_str.lower() == 'info':
        return INFO
    elif target_str.lower() == 'turn_on':
        return TURN_ON
    elif target_str.lower() == 'turn_off':
        return TURN_OFF
    return None


def get_hs_target(target_str):
    if target_str.lower() == 'manual':
        return MANUAL
    elif target_str.lower() == 'auto':
        return AUTO


def read_address_from_file(filename):
    addr = []
    with open(filename, 'r') as in_file:
        for line in in_file:
            line = line.strip()
            if not line.startswith('#'):
                record = []
                array = line.split()
                if len(array) < 2:
                    print 'Error in address file. It has to be in format"[IP] [port]"'
                    return None
                record.append(array[0])
                record.append(int(array[1]))
                addr.append(record)
    return addr


class Sock:

    _sock = []

    class Probe:

        _id = 0

        def __init__(
            self,
            addr,
            port,
            active=False,
            connected=False,
            socket=None,
            ):
            self.addr = addr
            self.port = port
            self.active = active
            self.connected = connected
            self.socket = None
            self.id = Sock.Probe._id
            Sock.Probe._id += 1

        def connect(self):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.addr, self.port))
                self.active = True
                self.connected = True
                self.socket = s
            except socket_error, serr:
                self.active = False
                self.connected = False
                self.socket = None
                raise serr

        def __str__(self):
            return str(self.addr) + ':' + str(self.port)

        def send(self, mess):
            try:
                if self.active == True and self.connected == True:
                    self.socket.send(mess.pack())
                    return True
                else:
                    return False
            except socket_error, serr:
                self.connected = False
                self.active = False
                print 'Error: Connection with:' + str(self) \
                    + ' was lost.'
                raise serr

        def print_probe(self):
            print 'ID: ' + str(self.id)
            print '   ' + str(self)
            print '   connected: ' + str(self.connected)
            print '   enabled: ' + str(self.active)

        def set_active(self, val):
            if self.connected and val:
                self.active = True
            else:
                self.active = False

        def recv(self):
            try:
                mess = Reply.recv(self.socket)
                return mess
            except socket_error, serr:

            # For debug
            # logging.exception("Something awful happened!")

                print 'Error: Connection with probe ' + str(self) \
                    + '. was canceled'
                raise serr

        def recv_and_print(self, print_header=False):
            rep = self.recv()
            string = str(rep)
            if print_header:
                print 'Probe: ' + str(self)
                string = '\t'.join(('\t' + string).splitlines(True))
            sys.stdout.write(string)
            sys.stdout.flush()
            return rep

    @staticmethod
    def add_probes(addr):
        for i in addr:
            Sock._sock.append(Sock.Probe(i[0], i[1]))

    @staticmethod
    def connect():
        conn_count = 0
        for i in Sock._sock:
            print 'Connecting to ' + str(i)
            try:
                i.connect()
                conn_count += 1
            except socket_error:
                print 'Error: Connection could not be cretad'
        return conn_count

    @staticmethod
    def send(data):
        for i in Sock._sock:
            try:
                i.send(data)
            except socket_error, serr:
                if len(Sock.get_active()) == 0:
                    print 'There are no other clients -> Turing off'
                    exit(1)
                else:
                    raise serr

    @staticmethod
    def send_to(data, target):
        for i in target:
            try:
                Sock._sock[i].send(data)
            except socket_error, serr:
                if len(Sock.get_active()) == 0:
                    print 'There are no other clients -> Turing off'
                    exit(1)
                else:
                    raise serr

    @staticmethod
    def length():
        return len(Sock._sock)

    @staticmethod
    def print_probes():
        for i in Sock._sock:
            i.print_probe()
        print 'You can enable just connected probes: ' \
            + str(Sock.get_connected())

    @staticmethod
    def get_connected():
        connected = []
        for i in range(Sock.length()):
            if Sock._sock[i].connected == True:
                connected.append(i)
        return connected

    @staticmethod
    def get_active():
        active = []
        for i in range(Sock.length()):
            if Sock._sock[i].active == True:
                active.append(i)
        return active

    @staticmethod
    def set_active(indexes=None):

      # if indexes array is not specified active all

        if indexes == None:
            for i in Sock._sock:
                i.set_active(True)
            return

      # At first disable all socks

        for i in Sock._sock:
            i.set_active(False)

      # Enable specified

        for i in indexes:
            if i < 0 or i >= Sock.length():
                print 'Probe with ID ' + str(i) \
                    + ' does not exists. It is out of range. See the probes ids.'
            elif Sock._sock[i].connected == False:
                print 'Could not set probe with ID ' + str(i) \
                    + ' to active, because it is disconnected.'
            else:
                Sock._sock[i].set_active(True)

      # if no probes were activated by command, active all of them

        if len(Sock.get_active()) == 0:
            print 'No probes were activated by command -> Activation of all probes'
            return Sock.set_active()

    @staticmethod
    def recv_from(index):
        try:
            mess = Sock._sock[index].recv()
        except socket_error, serr:
            if len(Sock.get_active()) == 0:
                print 'There are no other clients -> Turing off'
                exit(1)
            else:
                raise serr
        return mess

    @staticmethod
    def print_reply_from(ind, print_header=False):
        try:
            rep = Sock._sock[ind].recv_and_print(print_header)
        except (socket_error, struct.error), serr:
            if len(Sock.get_active()) == 0:
                print 'There are no other clients -> Turing off'
                exit(1)
            raise serr
        return rep

    @staticmethod
    def send_rep_recv_rep(req, print_rep=True):
        rep_arr = []
        print_header = Sock.length() > 1
        for i in Sock._sock:
            if i.active and i.connected:
                try:
                    if i.send(req):
                        if print_rep:
                            rep_arr.append(i.recv_and_print(print_header))
                        else:
                            rep_arr.append(i.recv())
                    else:
                        print 'Message could not be sent'
                except socket_error:
                    print 'Rest of answer from probes ' + str(i) \
                        + ' could not be received.'
                    if len(Sock.get_active()) == 0:
                        print 'There are no other clients -> Turing off'
                        exit(1)
                except struct.error:
                    print 'Probe is disconnected'
                    if len(Sock.get_active()) == 0:
                        print 'There are no other clients -> Turing off'
                        exit(1)
        return rep_arr


class Shell(cmd.Cmd):

    _sock = None
    _reply = None
    _request = None

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'time_machine> '
        self.do_EOF = self.do_quit

    def do_probes(self, args):
        args = args.split()
        if len(args) == 0:
            Sock.print_probes()
            return None
        elif len(args) == 1 and args[0].lower() == 'all':
            Sock.set_active()
            print 'all probes activated'
        else:
            try:
                int_arr = [int(i) for i in args]
            except ValueError:
                print 'Invlaid probe IDs. It has to be written in format: "probes x y ...", where x and y are IDs of probes.'
                print 'Write "probes" to get info about probes and their IDs'
                return None
            Sock.set_active(int_arr)
            print 'Active probes: ' + str(Sock.get_active())

    def complete_probes(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        result = []
        if len(line.split()) > 2:
            return result
        if 'all'.startswith(text):
            result.append('all')
        if len(line.split()) == 1:
            result.append(str(Sock.get_connected()))
        return result

    def help_probes(self):
        print """
Get information about connected probes. It is possible to select active probes which are used to send commands to.

usage (info about probes): probes
usage (set active probes): probes <id1> <id2> <id3> ...
   - To set all probes to active use "all" instead of IDs"""

    def do_history_capture(self, args):
        size = 0
        args = args.split()
        if len(args) < 1 or len(args) > 2:
            self.help_history_capture()
            return None

        operation = get_hc_target(args[0])
        if operation == None:
            print "unsupported operation, choose either 'turn_on', 'turn_off' or 'info'"
            return None
        if operation == TURN_ON:
            if len(args) != 2:
                self.help_history_capture()
                return None
            try:
                size = int(args[1])
            except ValueError:
                print 'invalid buffer size. Should be number of MB.'
                return None

        req = Request_history_capture(operation, size)
        Sock.send_rep_recv_rep(req)

    def complete_history_capture(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        len_text = len(text)
        arr = line.split()
        arr_len = len(arr)
        result = []
        if arr_len == 1 and len_text == 0 or arr_len == 2 and len_text \
            > 0:
            if len_text > 0 and len_text < 6 \
                and 'turn_o'.startswith(text):
                result.append('turn_o')
                return ['turn_o']
            if 'info'.startswith(text):
                result.append('info')
            if 'turn_on'.startswith(text):
                result.append('turn_on ')
            if 'turn_off'.startswith(text):
                result.append('turn_off')
        if arr_len == 2 and len_text == 0:
            if arr[1].lower() == 'turn_on':
                result += ['<size MB>', ' ']
        return result

    def help_history_capture(self):
        print """
Command can turn on, turn off the history capture or print information about the buffer.
If the buffer is turned on, the history capture is done for every incoming capture request.

usage: history_capture <rule> [buffer size]
   - available rules: turn_on, turn_off, info
   - buffer size: If rule 'turn_on' is used, specify size of buffer, use 0 for default size"""

    def do_info(self, args):
        args = args.split()
        if len(args) > 1:
            self.help_info()
            return None

        req = Request_info(TURN_ON)
        Sock.send(req)
        thr_arr = []
        active_probes = Sock.get_active()
        for i in active_probes:
            if isinstance(Sock.recv_from(i), Reply_success):

            # create thread for listening info

                listeningThread = \
                    threading.Thread(target=print_reply_thr, args=[i,
                        len(active_probes) > 1])
                listeningThread.daemon = True
                listeningThread.start()
                thr_arr.append(listeningThread)
        raw_input('Press <enter> to stop INFO\n')
        print 'Terminating INFO'

      # turn off the INFO

        req = Request_info(TURN_OFF)
        Sock.send(req)
        for i in thr_arr:
            i.join()

    def complete_info(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        return

    def help_info(self):
        print """
Receive actual progress of active capturing rules.

usage: info
   - It will turn on the info mode"""

    def help_heavy_size_manual(self):
        print """usage: heavy_size MANUAL <value>
   - value = max count of packet to be heavy flow"""

    def help_heavy_size_auto(self):
        print """usage: heavy_size AUTO <value>
   - value = count of secconds to be stored in history_capture"""

    def do_heavy_size(self, args):
        size = 0
        args = args.split()
        if len(args) != 1:
            self.help_heavy_size()
            return None
        try:
            size = int(args[0])
        except ValueError:
            print 'invalid value. Should be number of packet.'
            return None
        req = Request_heavy_size(MANUAL, size)
        Sock.send_rep_recv_rep(req)

    def complete_heavy_size(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        if len(line.split()) == 1 and len(text) == 0:
            return ['<size (packet limit)>', ' ']

    def help_heavy_size(self):
        print """
Set size of beginning of the flow which is stored to history buffer.

usage: heavy_size <size>
   - size: Size of beginning of the flow (number of packets) that is stored in history buffer."""

    def do_add(self, args):
        args = args.split()
        packets = -1
        timeout = -1
        if len(args) == 5:
            try:
                timeout = int(args[4])
            except ValueError:
                print 'invalid timeout specified'
                return None
            packets = int(args[3])
        elif len(args) == 4:
            try:
                packets = int(args[3])
            except ValueError:
                print 'invalid packet limit specified'
                return None
        elif len(args) != 3:
            self.help_add()
            return None

        direction = get_target(args[0])
        if direction == None:
            print "unsupported direction, choose either 'src_ip', 'dst_ip' or 'bidir_ip'"
            return None
        try:
            addr = Ip.from_str(args[1])
        except ValueError, v:
            print v
            return None

        filename = args[2]
        if len(filename) > 100:
            print 'protocol v' + VERSION_MAJOR + '.' + VERSION_MINOR \
                + ' supports up to 100 characters for filename'
            return None
        if packets < 0:
            packets = MAX_UNIT32
        if timeout < 0:
            timeout = MAX_UNIT32

        req = Request_add(addr, direction, packets, timeout, filename)
        Sock.send_rep_recv_rep(req)

    def complete_add(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        len_text = len(text)
        arr = line.split()
        arr_len = len(arr)
        result = []
        if arr_len == 1 and len_text == 0 or arr_len == 2 and len_text \
            > 0:

         # propose direction of capture

            return propose_target_direction(text)
        elif arr_len == 2 and len_text == 0:
            if get_target(arr[1]) != None:
                return ['<IP address>', ' ']
        elif arr_len == 3 and len_text == 0:
            if get_target(arr[1]) != None:
                return ['<capture name>', ' ']
        elif arr_len == 4 and len_text == 0:
            if get_target(arr[1]) != None:
                return ['[packet limit]', ' ']
        elif arr_len == 5 and len_text == 0:
            if get_target(arr[1]) != None:
                return ['[timeout]', ' ']
        return result

    def help_add(self):
        print """
Add new capturing rule. If the IP address is being captured and given capture name is equal, the limits and direction are updated.
New packet limit = captured packets + specified packet limit
New timeout = actual time + timeout
New direction = old direction + new direction (bidir_ip = src_ip + dst_ip)

usage: add <direction> <IP address> <capture name> [packet limit] [timeout]
   - available direction: src_ip, dst_ip, bidir_ip
   - IP address: IP whose data is captured
   - capture name: Name is used for filenames of captured data
   Optional parameters:
      - packet limit : minimal number of packets to capture, use -1 for unlimited (default)
      - timeout: minimal capture time in seconds, use -1 for unlimited (default)"""

    def do_remove(self, args):
        args = args.split()
        if len(args) != 2:
            self.help_remove()
            return None

        direction = get_target(args[0])
        if direction == None:
            print "unsupported direction, choose either 'src_ip', 'dst_ip' or 'bidir_ip'"
            return None

        try:
            addr = Ip.from_str(args[1])
        except ValueError, v:
            print v
            return None

        req = Request_remove(addr, direction)
        Sock.send_rep_recv_rep(req)

    def complete_remove(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        len_text = len(text)
        arr = line.split()
        arr_len = len(arr)
        if arr_len == 1 and len_text == 0 or arr_len == 2 and len_text \
            > 0:

         # propose direction of capture

            return propose_target_direction(text)
        elif arr_len == 2 and len_text == 0 or arr_len == 3 \
            and (len_text > 0 or arr[2].startswith(':')):
            try:
                target = get_target(arr[1])
                if target == None:
                    return []
                if arr_len > 2:
                    return propose_ip(arr[2], target)
                else:
                    return propose_ip([], target)
            except:
                pass
            return ['<IP address>', ' ']

    def help_remove(self):
        print """
Remove capturing rule specified by IP address.

usage: remove <direction> <IP address>
   - available direction: src_ip, dst_ip, bidir_ip"""

    def do_list(self, args):
        args = args.split()
        if len(args) == 0:
            direction = TARGET_ALL
        elif len(args) == 1:
            direction = get_target_list(args[0])
            if direction == None:
                print "unsupported direction, choose either 'src_ip', 'dst_ip', 'bidir_ip' or 'all'"
                return None
        else:
            self.help_list()
            return None
        req = Request_list(direction)
        Sock.send_rep_recv_rep(req)

    def complete_list(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        len_text = len(text)
        arr = line.split()
        arr_len = len(arr)
        result = []
        if arr_len == 1 and len_text == 0 or arr_len == 2 and len_text \
            > 0:

         # propose direction of capture

            result = propose_target_direction(text)
            if 'all'.startswith(text):
                result.append('all')
        return result

    def help_list(self):
        print """
Print all IP address and their direction that are being captured.

usage: list <direction>
   - available direction: src_ip, dst_ip, bidir_ip"""

    def do_detail(self, args):
        args = args.split()
        if len(args) != 1:
            self.help_detail()
            return None

        try:
            addr = Ip.from_str(args[0])
        except ValueError, v:
            print v
            return None

        req = Request_detail(addr, 0)
        Sock.send_rep_recv_rep(req)

    def complete_detail(
        self,
        text,
        line,
        begidx,
        endidx,
        ):
        len_text = len(text)
        arr = line.split()
        arr_len = len(arr)
        if arr_len == 1 and len_text == 0 or arr_len == 2 and (len_text
                > 0 or arr[1].startswith(':')):
            try:
                if arr_len > 1:
                    return propose_ip(arr[1], TARGET_BIDIR_IP)
                else:
                    return propose_ip([], TARGET_BIDIR_IP)
            except:
                pass
            return ['<IP address>', ' ']

    def help_detail(self):
        print """
Print details about captured IP address.

usage: detail <IP address>"""

    def do_quit(self, args):
        print
        return True

    def do_exit(self, args):
        print
        return True


parser = OptionParser()
parser.add_option(
    '-i',
    '--addr',
    dest='ip',
    default='localhost',
    help='Address of running time machine (default: localhost)',
    metavar='[ip address]',
    )
parser.add_option(
    '-p',
    '--port',
    dest='port',
    default=37564,
    help='Port of running time machine',
    metavar='[port]',
    )
parser.add_option(
    '-a',
    '--input_file_addresses',
    dest='file_addr',
    default='',
    help="File with IPs and ports of running time machines. In this case, only time machines specified in this file will be connected. Time machines should be specified in format: '<addres> <port>'"
        ,
    metavar='[filename]',
    )
parser.add_option(
    '-t',
    '--history_capture_info',
    default=False,
    dest='hc_info',
    action='store_true',
    help='Info about history buffer. (This option wil not open shell)',
    )
parser.add_option(
    '-n',
    '--history_capture_turn_on',
    default=0,
    dest='hc_turn_on',
    metavar='[size in MB]',
    help='Turn on the history capture. (This option wil not open shell)'
        ,
    )
parser.add_option(
    '-f',
    '--history_capture_turn_off',
    default=False,
    dest='hc_off',
    action='store_true',
    help='Turn off the history buffer. (This option wil not open shell)'
        ,
    )
parser.add_option(
    '-s',
    '--history_capture_heavy_flow_manual',
    default=0,
    dest='hc_heavy_size',
    metavar='[number of packets]',
    help='Change size of beginning of the flow (number of packets of the flow) which will be stored in history capture. (This option wil not open shell)'
        ,
    )


class Capture:

    @classmethod
    def do_add(cls, args):
        args = args.split()
        packets = -1
        timeout = -1
        if len(args) == 5:
            try:
                timeout = int(args[4])
            except ValueError:
                print 'invalid timeout specified'
                return None
            packets = int(args[3])
        elif len(args) == 4:
            try:
                packets = int(args[3])
            except ValueError:
                print 'invalid packet limit specified'
                return None
        elif len(args) != 3:
            print 'add <direction> <IP address> <capture name> [packet limit] [timeout]'
            return None

        direction = get_target(args[0])
        if direction == None:
            print "unsupported direction, choose either 'src_ip', 'dst_ip' or 'bidir_ip'"
            return None
        try:
            addr = Ip.from_str(args[1])
        except ValueError, v:
            print v
            return None

        filename = args[2]
        if len(filename) > 100:
            print 'protocol v' + VERSION_MAJOR + '.' + VERSION_MINOR \
                + ' supports up to 100 characters for filename'
            return None
        if packets < 0:
            packets = MAX_UNIT32
        if timeout < 0:
            timeout = MAX_UNIT32

        req = Request_add(addr, direction, packets, timeout, filename)
        Sock.send_rep_recv_rep(req)

    @classmethod
    def do_list(self, args):
        args = args.split()
        if len(args) == 0:
            direction = TARGET_ALL
        elif len(args) == 1:
            direction = get_target_list(args[0])
            if direction == None:
                print "unsupported direction, choose either 'src_ip', 'dst_ip', 'bidir_ip' or 'all'"
                return None
        else:
            #self.help_list()
            return None
        req = Request_list(direction)
        Sock.send_rep_recv_rep(req)

    @classmethod
    def do_remove(self, args):
        # remove <direction> <IP address>
        # direction: src_ip, dst_ip, bidir_ip
       print("removing: ",args)
       args = args.split()
       if len(args) != 2:
          self.help_remove()
          return None

       direction = get_target(args[0])
       if direction == None:
          print("unsupported direction, choose either 'src_ip', 'dst_ip' or 'bidir_ip'")
          return None

       try:
          addr = Ip.from_str(args[1])
       except ValueError as v:
          print(v)
          return None

       req = Request_remove(addr, direction)
       Sock.send_rep_recv_rep(req)


if __name__ == '__main__':

   # ip "localhost"
   # port 37564
   # file_addr ""
   # histroy_capture_info False
   # history_capture_turn_on 0
   # history_capture_turn_off False
   # history_capture_heavy_flow_manual 0

    (options, args) = parser.parse_args()
    addr_info = [['localhost', 37564]]

   # create connection

    Sock.add_probes(addr_info)
    if Sock.connect() == 0:
        print 'No clients connected -> Exit'
        exit(1)
    direction = "src_ip" #direction: src_ip, dst_ip, bidir_ip
    ip = "2.2.3.4"
    name = "TEST"
    packet_limit = 100
    timeout = 200
    #Capture.do_add('src_ip 2.2.3.4 kks 1 1')
    Capture.do_add("{} {} {} {} {}".format(direction, ip, name, packet_limit, timeout))
    Capture.do_list("")
    Capture.do_remove("{} {}".format(direction, ip))
    Capture.do_list("")

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filter.time_machine_capture import Capture, Sock




class CaptureRequest():
    init_call = True
    @classmethod
    def __init__(cls):
        cls.init_call = False
        cls.addr_info = [['localhost', 37564]]

    @classmethod
    def send(cls, dir_and_ip):
        if(cls.init_call != False): cls.__init__()
        if not cls.connection_is_established():
            cls.connect_to_time_manager()

        if cls.connection_is_established():
            ip = "8.8.8.1"
            direction = "src_ip"
            #print(bcolors.OKGREEN + "Capture Request => ip: {}, direction: {}. packets: {}, seconds: {}".format(ip, direction, 10000, 300) + bcolors.ENDC)
            Capture.do_add("{} {} {} {} {}".format(direction, ip, "XYZA", 10000, 500))
            Capture.do_list("")
            #Capture.do_remove("{} {}".format(direction, ip))
            #Capture.do_list("")



    @classmethod
    def connection_is_established(cls):
        return Sock.connect() > 0

    @classmethod
    def connect_to_time_manager(cls):
        Sock.add_probes(cls.addr_info)


if __name__ == '__main__':
    CaptureRequest.send("xxx")

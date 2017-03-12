import cmd
import threading
import time

class HelloWorld(cmd.Cmd):
    """Simple command processor example."""

    def do_greet(self, line):
        print "hello 12312 3123 "

    def do_EOF(self, line):
        return True


    def do_start(self,line):
        print('-----------')
        #print(thrd.get_ident())
        print(threading.current_thread().name)
        self.tc = ThreadCls()
        self.tc.start()
    def do_count(self, line):

        cnt = 1
        for i in range(5):
            cnt += 1
            cnt

    def do_stop(self,line):
        self.tc.stop = True


class ThreadCls(threading.Thread):
    def run(self):
        self.count()


    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = False

    def count(self):
        cnt = 0
        print('-----------')
        print(threading.current_thread().name)
        print('-----------')
        while True:
            print(cnt)
            cnt+=1
            time.sleep(3)
            if self.stop == True:
                break


if __name__ == '__main__':
    HelloWorld().cmdloop()

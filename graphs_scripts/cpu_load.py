# #!/usr/bin/env python
# import os
# import tempfile
# import time
# import sys
#
# def total(pids):
#     return [sum(map(int, file('/proc/%s/stat' % pid).read().split()[13:17])) for pid in pids]
#
# def main():
#     if len(sys.argv) == 1 or sys.argv[1] == '-h':
#         print 'log.py output.png pid1 pid2..'
#         return
#     pids = sys.argv[2:]
#     results = []
#     prev = total(pids)
#     try:
#         while True:
#             new = total(pids)
#             result = [(new[i]-prev[i])/0.1 for i, pid in enumerate(pids)]
#             results.append(result)
#             time.sleep(0.1)
#             prev = new
#     except KeyboardInterrupt:
#         pass
#     t1, t2 = tempfile.mkstemp()[1], tempfile.mkstemp()[1]
#     f1, f2 = file(t1, 'w'), file(t2, 'w')
#     print
#     print 'data: %s' % t1
#     print 'plot: %s' % t2
#     for result in results:
#         print >>f1, ' '.join(map(str, result))
#     print >>f2, 'set terminal png size %d,480' % (len(results)*5)
#     print >>f2, "set out '%s'" % sys.argv[1]
#     print >>f2, 'plot ' + ', '.join([("'%s' using ($0/10):%d with linespoints title '%s'" % (t1, i+1, pid)) for i, pid in enumerate(pids)])
#     f1.close()
#     f2.close()
#     os.system('gnuplot %s' % t2)
#
# if __name__ == '__main__':
#     main()


import time
import string
import sys
import commands

def get_cpumem(pid):
    d = [i for i in commands.getoutput("ps aux").split("\n")
        if i.split()[1] == str(pid)]
    return (float(d[0].split()[2]), float(d[0].split()[3])) if d else None

if __name__ == '__main__':
    if not len(sys.argv) == 2 or not all(i in string.digits for i in sys.argv[1]):
        print("usage: %s PID" % sys.argv[0])
        exit(2)
    print("%CPU\t%MEM")
    try:
        while True:
            x = get_cpumem(sys.argv[1])
            if not x:
                print("no such process")
                exit(1)
            print("%.2f\t%.2f" % x)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print
        exit(0)

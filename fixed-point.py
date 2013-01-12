#-*-coding:utf-8-*-

from simsimi import SimSimi
import time

if __name__ == '__main__':
    chick1 = SimSimi()
    chick2 = SimSimi()
    x0 = '我们说会话吧'
    x1 = ''
    while x1 != x0:
        x1 = chick1.chat(x0)
        print "chick1: %s" % x1
        time.sleep(2)
        x0 = chick2.chat(x1)
        print "chick2: %s" % x0
        time.sleep(2)


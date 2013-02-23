#-*-coding:utf-8-*-

from renren import RenRen
import time

if __name__ == '__main__':
    try:
        from my_accounts import accounts
    except:
        print "please configure your renren account in 'my_account.py' first"
        sys.exit(-1)
    renren = RenRen()
    renren.login(accounts[0][0], accounts[0][1])
    #renren.saveCookie('cookie.txt')
    #renren.loginByCookie('cookie.txt')
    #info = renren.getUserInfo()
    print renren.info

    notifications = renren.getNotifications()
    print notifications
    for n in notifications:
        payloads, content = renren.getNotiData(n)
        print payloads
        print content
        payloads['message'] = 'test reply "%s"' % content
        r = renren.addComment(payloads)
        print r
        if not 'code' in r:
            print "failed"
        elif r['code'] != 0:
            print r['msg']
        time.sleep(2)


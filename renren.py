#-*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>
Copyright (c) 2012 hupili <hpl1989@gmail.com>

Original Author:
    Wong2 <wonderfuly@gmail.com>
Changes Statement:
    Changes made by Pili Hu <hpl1989@gmail.com> on
    Jan 10 2013:
        Support captcha.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


# 人人各种接口

import requests
import json
import re
import random
from urlparse import urlparse, parse_qsl
from pyquery import PyQuery
from ntype import NTYPES
from encrypt import encryptString
import pickle
import sys
import os


class RenRen:

    def __init__(self, email=None, pwd=None):
        self.session = requests.Session()
        self.token = {}

        if email and pwd:
            self.login(email, pwd)

    def save(self, path = None):
        if path is None:
            path = self.email + ".info.pickle"
        obj = {'cookie': self.session.cookies, 'token': self.token, 'info': self.info}
        pickle.dump(obj, open(path, 'w'))
        return True


    def load(self, path = None):
        if path is None:
            path = self.email + ".info.pickle"
        try:
            obj = pickle.load(open(path, 'r'))
            self.session.cookies = obj['cookie']
            self.token = obj['token']
            self.info = obj['info']
            self.getToken()
            if self.token['requestToken'] != '':
                return True
            else:
                return False
        except Exception, e:
            return False

    def _loginByCookie(self, cookie_str):
        cookie_dict = dict([v.split('=', 1) for v in cookie_str.strip().split(';')])
        self.session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        self.getToken()

    def loginByCookie(self, cookie_path):
        with open(cookie_path) as fp:
            cookie_str = fp.read()
            cookie_dict = dict([v.split('=', 1) for v in cookie_str.strip().split(';')])
            print cookie_dict
            self.session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        self.getToken()

    def saveCookie(self, cookie_path):
        with open(cookie_path, 'w') as fp:
            cookie_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
            print cookie_dict
            cookie_str = ';'.join([k + '=' + v for k, v in cookie_dict.iteritems()])
            fp.write(cookie_str)

    def login(self, email, pwd):
        self.email = email
        if self.load():
            return

        key = self.getEncryptKey()

        if self.getShowCaptcha(email) == 1:
            fn = 'icode.%s.jpg' % os.getpid()
            self.getICode(fn)
            print "Please input the code in file '%s':" % fn
            icode = raw_input().strip()
            os.remove(fn)
        else:
            icode = ''

        data = {
            'email': email,
            'origURL': 'http://www.renren.com/home',
            'icode': icode,
            'domain': 'renren.com',
            'key_id': 1,
            'captcha_type': 'web_login',
            'password': encryptString(key['e'], key['n'], pwd) if key['isEncrypt'] else pwd,
            'rkey': key['rkey']
        }
        print "login data: %s" % data
        url = 'http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=%f' % random.random()
        r = self.post(url, data)
        result = r.json()
        print result
        if result['code']:
            print 'login successfully'
            self.email = email
            r = self.get(result['homeUrl'])
            self.info = self.getUserInfo()
            self.getToken(r.text)
            self.save()
        else:
            print 'login error', r.text

    def getICode(self, fn):
        r = self.get("http://icode.renren.com/getcode.do?t=web_login&rnd=%s" % random.random())
        if r.status_code == 200 and r.raw.headers['content-type'] == 'image/jpeg':
            with open(fn, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            print "get icode failure"

    def getShowCaptcha(self, email=None):
        r = self.post('http://www.renren.com/ajax/ShowCaptcha', data={'email': email})
        return r.json()

    def getEncryptKey(self):
        r = requests.get('http://login.renren.com/ajax/getEncryptKey')
        return r.json()

    def getToken(self, html=''):
        p = re.compile("get_check:'(.*)',get_check_x:'(.*)',env")

        if not html or html == '':
            r = self.get('http://www.renren.com')
            html = r.text

        result = p.search(html)
        self.token = {
            'requestToken': result.group(1),
            '_rtk': result.group(2)
        }

    def _parse_timeline(self, text):
        dom = PyQuery(text)
        articles = dom.children()
        s_list = []
        for a in articles:
            aa = PyQuery(a)
            try:
                f = {}
                f['text'] = PyQuery(aa.children()[1]).text()
                try:
                    # This is a share item
                    f['reply'] = json.loads(PyQuery(PyQuery(aa.children()[3]).children()[3]).text())
                    #print "a share item"
                except IndexError:
                    # This is a status item
                    try:
                        f['reply'] = json.loads(PyQuery(PyQuery(aa.children()[2]).children()[3]).text())
                        #print "a status item"
                    except IndexError:
                        print "un recognizable feeds: %s" % f['text']
                if 'reply' in f:
                    s_list.append(f)
            except Exception, e:
                print "Exception: %s" % e
                pass

        for s in s_list:
            s['data'] = {
                    'doing_id': s['reply']['cid'], 
                    'owner_id': s['reply']['oid'],
                    'type_num': s['reply']['typeNum']
                    }

        return s_list
        #return text

    def update(self, text):
        url_update = 'http://shell.renren.com/%s/status' % self.info['hostid']
        r = self.post(url_update, {'content': text, 'hostid': self.info['hostid'], 'channel': 'renren'})
        return r.json()

    def home_timeline(self, page = None):
        if page:
            r = self.post('http://guide.renren.com/feedguide.do', {'p':page})
        else:
            r = self.post('http://guide.renren.com/feedguide.do')
        return self._parse_timeline(r.text)

    def request(self, url, method, data={}):
        if data:
            data.update(self.token)

        if method == 'get':
            return self.session.get(url, data=data)
        elif method == 'post':
            return self.session.post(url, data=data)

    def get(self, url, data={}):
        return self.request(url, 'get', data)

    def post(self, url, data={}):
        return self.request(url, 'post', data)

    def getUserInfo(self):
        r = self.get('http://notify.renren.com/wpi/getonlinecount.do')
        return r.json()

    def getNotifications(self):
        url = 'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&limit=50&begin=0&view=17'
        r = self.get(url)
        try:
            result = json.loads(r.text, strict=False)
        except Exception, e:
            print 'error', e
            result = []
        return result

    def removeNotification(self, notify_id):
        self.get('http://notify.renren.com/rmessage/remove?nl=' + str(notify_id))

    def getDoings(self, uid, page=0):
        url = 'http://status.renren.com/GetSomeomeDoingList.do?userId=%s&curpage=%d' % (str(uid), page)
        r = self.get(url)
        return r.json().get('doingArray', [])

    def getDoingById(self, owner_id, doing_id):
        doings = self.getDoings(owner_id)
        doing = filter(lambda doing: doing['id'] == doing_id, doings)
        return doing[0] if doing else None

    def getDoingComments(self, owner_id, doing_id):
        url = 'http://status.renren.com/feedcommentretrieve.do'
        r = self.post(url, {
            'doingId': doing_id,
            'source': doing_id,
            'owner': owner_id,
            't': 3
        })

        return r.json()['replyList']

    def getCommentById(self, owner_id, doing_id, comment_id):
        comments = self.getDoingComments(owner_id, doing_id)
        comment = filter(lambda comment: comment['id'] == int(comment_id), comments)
        return comment[0] if comment else None

    def addCommentGeneral(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'
        #url = 'http://page.renren.com/doing/reply'

        # 'stype' is not mandatory
        # 't'=4 is for shares
        # 't'=3 is for status
        # t must exist
        payloads = {
            'rpLayer': 0,
            'source': data['doing_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }
        if data.get('type_num', None):
            payloads['t'] = data.get('type_num')

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        print payloads
        print self.email, 'going to send a comment: ', payloads['c']

        r = self.post(url, payloads)
        r.raise_for_status()

        print 'comment sent', r.json()
        return r.json()

    def addCommentShare(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'
        #url = 'http://page.renren.com/doing/reply'

        # 'stype' is not mandatory
        # 't'=4 is for shares
        # 't'=3 is for status
        # t must exist
        payloads = {
            't': 4,
            #'stype': 103, 
            'rpLayer': 0,
            'source': data['doing_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        print payloads
        print self.email, 'going to send a comment: ', payloads['c']

        r = self.post(url, payloads)
        r.raise_for_status()

        print 'comment sent', r.json()
        return r.json()

    def addComment(self, data):
        return {
            'status': self.addStatusComment,
            'album' : self.addAlbumComment,
            'photo' : self.addPhotoComment,
            'blog'  : self.addBlogComment,
            'share' : self.addStatusComment,
            'gossip': self.addGossip
        }[data['type']](data)

    def sendComment(self, url, payloads):
        r = self.post(url, payloads)
        r.raise_for_status()
        return r.json()

    # 评论状态
    def addStatusComment(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'

        payloads = {
            't': 3,
            'rpLayer': 0,
            'source': data['source_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        print payloads
        print self.email, 'going to send a comment: ', payloads['c']
        return self.sendComment(url, payloads)

    # 回复留言
    def addGossip(self, data):
        url = 'http://gossip.renren.com/gossip.do'
        
        payloads = {
            'id': data['owner_id'], 
            'only_to_me': 1,
            'mode': 'conversation',
            'cc': data['author_id'],
            'body': data['message'],
            'ref':'http://gossip.renren.com/getgossiplist.do'
        }

        return self.sendComment(url, payloads)

    # 回复分享
    def addShareComment(self, data):
        url = 'http://share.renren.com/share/addComment.do'
        
        payloads = {
            'comment': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'shareId' : data['source_id'],
            'shareOwner': data['owner_id'],
            'replyToCommentId': data['reply_id'],
            'repetNo' : data['author_id']
        }

        return self.sendComment(url, payloads)

    # 回复日志
    def addBlogComment(self, data):
        url = 'http://blog.renren.com/PostComment.do'
        
        payloads = {
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment': 'true',
            'guestName': '小黄鸡', 
            'id' : data['source_id'],
            'only_to_me': 0,
            'owner': data['owner_id'],
            'replyCommentId': data['reply_id'],
            'to': data['author_id']
        }

        return self.sendComment(url, payloads)

    # 回复相册
    def addAlbumComment(self, data):
        url = 'http://photo.renren.com/photo/%d/album-%d/comment' % (data['owner_id'], data['source_id'])
        
        payloads = {
            'id': data['source_id'],
            'only_to_me' : 'false',
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment' : 'true', 
            'owner' : data['owner_id'],
            'replyCommentId' : data['reply_id'],
            'to' : data['author_id']
        }

        return self.sendComment(url, payloads)

    def addPhotoComment(self, data):
        url = 'http://photo.renren.com/photo/%d/photo-%d/comment' % (data['owner_id'], data['source_id'])
        
        payloads = {
            'guestName': '小黄鸡',
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment' : 'true',
            'owner' : data['owner_id'],
            'realWhisper':'false',
            'replyCommentId' : data['reply_id'],
            'to' : data['author_id']
        }

        return self.sendComment(url, payloads)


    # 访问某人页面
    def visit(self, uid):
        self.get('http://www.renren.com/' + str(uid) + '/profile')

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
    #print 'hello', info['hostname']
    #print renren.getNotifications()
    #renren.visit(328748051)

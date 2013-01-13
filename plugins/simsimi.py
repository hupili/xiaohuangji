#-*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>

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


# 从simsimi读数据

import sys
sys.path.append('..')

import requests
import cookielib
import socket

try:
    import MySQLdb
    from settings import MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DBNAME
    use_mysql = True
except:
    use_mysql = False

try:
    from settings import SIMSIMI_KEY
except:
    SIMSIMI_KEY = ''

if use_mysql:
    mysqldb = MySQLdb.connect(host=MYSQL_HOST, port=3306, user=MYSQL_USER, passwd=MYSQL_PASS, db=MYSQL_DBNAME, charset='utf8', use_unicode=False)
    cursor = mysqldb.cursor()
    try:
        workerhostname = socket.gethostname()
    except:
        workerhostname = 'unknown'


class SimSimi:

    def __init__(self):

        #self.headers = {
        #    #'Referer': 'http://www.simsimi.com/talk.htm?lc=ch',
        #    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:18.0) Gecko/20100101 Firefox/18.0', 
        #    #'Accept': 'application/json, text/javascript, */*; q=0.01', 
        #    'Accept-Language': 'en-US,en;q=0.5', 
        #    'Accept-Encoding': 'gzip, deflate', 
        #    #'Content-Type': 'application/json; charset=utf-8', 
        #    #'X-Requested-With': 'XMLHttpRequest', 
        #    'Connection': 'keep-alive'
        #}

        self.session = requests.Session()

        self.chat_url = 'http://www.simsimi.com/func/req?msg=%s&lc=ch'
        self.api_url = 'http://api.simsimi.com/request.p?key=%s&lc=ch&ft=1.0&text=%s'

        if not SIMSIMI_KEY:
            self.initSimSimiCookie()

    def request(self, url, method, data={}):
        #if data:
        #    data.update({'Referer': 'http://www.simsimi.com/talk.htm?lc=ch'})

        if method == 'get':
            return self.session.get(url, data=data)
        elif method == 'post':
            return self.session.post(url, data=data)

    def get(self, url, data={}):
        return self.request(url, 'get', data)

    def post(self, url, data={}):
        return self.request(url, 'post', data)

    def initSimSimiCookie(self):
        self.get('http://www.simsimi.com/talk.htm')
        self.get('http://www.simsimi.com/talk.htm/func/langInfo')
        self.get('http://www.simsimi.com/talk.htm/talk.htm?lc=ch')
        #r = requests.get('http://www.simsimi.com/talk.htm')
        #self.chat_cookies = r.cookies
        #r = requests.get('http://www.simsimi.com/func/langInfo', headers=self.headers)
        #self.chat_cookies = r.cookies
        #r = requests.get('http://www.simsimi.com/talk.htm?lc=ch', cookies=self.chat_cookies, headers=self.headers)
        #self.chat_cookies = r.cookies

    def getSimSimiResult(self, message, method='normal'):
        if method == 'normal':
            #r = requests.get(self.chat_url % message, cookies=self.chat_cookies, headers=self.headers)
            r = self.get(self.chat_url % message)
            #self.chat_cookies = r.cookies
        else:
            url = self.api_url % (SIMSIMI_KEY, message) 
            r = requests.get(url)
        return r

    def chat(self, message=''):
        if message:
            r = self.getSimSimiResult(message, 'normal' if not SIMSIMI_KEY else 'api')
            try:
                answer = r.json()['response']
                if use_mysql:
                    sql = "INSERT INTO question_and_answers (question, answer, worker) VALUES(%s, %s, %s)"
                    try:
                        cursor.execute(sql, (message, answer, workerhostname))
                    except Exception as e:
                        print e
                return answer.encode('utf-8')
            except:
                return '呵呵'
        else:
            return '叫我干嘛'

simsimi = SimSimi()

def test(data, bot):
    return True

def handle(data, bot):
    return simsimi.chat(data['message'])

if __name__ == '__main__':
    pass
    #print handle({'message': '最后一个问题'}, None)
    #print handle({'message': '爱谁？'}, None)

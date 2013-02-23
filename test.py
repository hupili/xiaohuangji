#-*-coding:utf-8-*-

from renren import RenRen
from ntype import NTYPES
import re

NTYPES = {
    'reply_in_status_comment': 16,
    'at_in_status': 196
}

self_match_pattern = re.compile('@小黄鸡(\(601621937\))?')

#from controller import getNotiData

# 从一条评论里提取出内容，去掉'回复xx:'和'@小黄鸡'
def extractContent(message):
    content = self_match_pattern.sub('', message)
    content_s = content.split('：', 1)
    if len(content_s) == 1:
        content_s = content.split(': ', 1)
    if len(content_s) == 1:
        content_s = content.split(':', 1)
    content = content_s[-1]
    return content

def getNotiData(bot, data):
    ntype, content = int(data['type']), ''

    payloads = {
        'owner_id': data['owner'],
        'source_id': data['source']
    }

    if ntype == NTYPES['at_in_status'] or ntype == NTYPES['reply_in_status_comment']:
        owner_id, doing_id = data['owner'], data['doing_id']

        payloads['type'] = 'status'

        if ntype == NTYPES['at_in_status'] and data['replied_id'] == data['from']:
            content = self_match_pattern.sub('', data['doing_content'].encode('utf-8'))
        else:
            # 防止在自己状态下@自己的时候有两条评论
            if ntype == NTYPES['at_in_status'] and owner_id == '601621937':
                return None, None
            reply_id = data['replied_id']
            comment = bot.getCommentById(owner_id, doing_id, reply_id)
            if comment:
                payloads.update({
                    'author_id': comment['ownerId'],
                    'author_name': comment['ubname'],
                    'reply_id': reply_id
                })
                content = extractContent(comment['replyContent'].encode('utf-8'))
            else:
                return None, None
    else:
        return None, None

    return payloads, content.strip()

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
    payloads, content = getNotiData(renren, notifications[0])
    print payloads
    print content

#!/bin/env python
from django.conf import settings
import json,time,datetime
import urllib
import urllib.parse, http.client
from social_django.models import UserSocialAuth
import datetime
from msknet_censorship.models import SiteSettingManager

siteSetting = SiteSettingManager()
gid=0
admission_gid=0
try:
    gid = int(siteSetting['discourse.group.insider.id'])
    admission_gid = int(siteSetting['discourse.group.admission.id'])
except:
    gid=0
    admission_gid=0

gname = siteSetting['discourse.group.insider.name']


load_json = lambda x: json.loads(str(x,'utf-8'))

def uid_to_discourse_uid(uid):
    try:
        return UserSocialAuth.objects.get(user_id=uid).uid
    except:
        return '0'

def discourse_uid_to_uid(duid):
    try:
        return UserSocialAuth.objects.get(uid=duid).user.id
    except:
        return '0'

## use GID!
def add_to_group(duid):
    params = {'group_id': gid}
    return do_rest('/admin/users/%d/groups.json' % (int(duid)), "POST", params)

def remove_from_group(duid):
    return do_rest('/groups/%d/members.json'%(int(gid)),"DELETE",{'user_id':int(duid)})

def do_rest(url,method="PUT",params={}):
    conn = http.client.HTTPSConnection(urllib.parse.urlparse(settings.DISCOURSE_BASE_URL).hostname)
    params['api_key']=settings.DISCOURSE_SYSTEM_API_KEY
    params['api_username']=settings.DISCOURSE_SYSTEM_API_USERNAME
    params = urllib.parse.urlencode(params)
    conn.request(method, url, params, headers = {
        'Content-type': 'application/x-www-form-urlencoded',
        'HTTP_USER_API_KEY': settings.DISCOURSE_SYSTEM_API_KEY})
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return (response.status,data)

# use GName!
def get_insiders():
    s=do_rest('/groups/%s/members.json?offset=0&limit=2147483647'%(gname,),"GET")[1]
    return load_json(s)['members']

def get_user_info(uid):
    return load_json(do_rest('/admin/users/%d.json'%int(uid),"GET")[1])

def is_in_group(uid, gid):
    info=get_user_info(uid)
    for i in info.get('groups',[]):
        if i.get('id')==gid:
            return True
    return False

is_insider = lambda uid: is_in_group(uid, gid)
is_censor = lambda uid: is_in_group(uid, admission_gid)

def pm(uid,title,text):
    if type(uid) == int:
        duid = uid_to_discourse_uid(uid)
        username  = get_user_info(duid)['username']
    else:
        username = uid
    return do_rest('/posts',"POST",{'archetype':'private_message','title':title,'raw':text,'target_usernames':username})

PM_TITLE_ACCEPT='恭喜，您的 hitorino* insider 申请已经通过'
PM_TXT_ACCEPT='''尊敬的 hitorino* insider 申请人，

我们很高兴地通知您，您的 hitorino* insider 申请已经审核通过。
您应该已经获得社区里区权限。如有问题，请到社区「表区 - 里区申请区」报告，感谢您的支持。
我们希望您能够在 hitorino* 内发现更多价值，享受更加安全与文明的社区服务。
祝您愉快度过每一天。

hitorino* 管理组
hitorino.moe
'''

PM_TITLE_REJECT='注意，您的 hitorino* insider 申请已被退回'
PM_TXT_REJECT='''尊敬的 hitorino* insider 申请人，

我们很无奈地通知您，您的 hitorino* insider 申请已被退回。
经过管理组的认真讨论，我们认为您提交的申请中的有效资料不足以我们做出准确的判断。
我们建议您补充完善资料后再次申请。
祝您愉快度过每一天。

hitorino* 管理组
hitorino.moe
'''
PM_TITLE_BLACKLIST='抱歉，您的 hitorino* insider 申请未能通过'
PM_TXT_BLACKLIST='''尊敬的 hitorino* insider 申请人，

我们很遗憾地通知您，您的 hitorino* insider 申请未能审核通过。
经过管理组的认真讨论，我们认为 hitorino* insider 的定位当前不能适合您的需要。
我们相信这是当前对双方最好的选择。
祝您愉快度过每一天。

hitorino* 管理组 
hitorino.moe
'''


def pm_send_accept(user):
    pm(user.id,siteSetting['discourse.pm.accept.title'],siteSetting['discourse.pm.accept.content'])
def pm_send_blacklist(user):
    pm(user.id,siteSetting['discourse.pm.blacklisted.title'],siteSetting['discourse.pm.blacklisted.content'])
def pm_send_reject(user):
    pm(user.id,siteSetting['discourse.pm.rejected.title'],siteSetting['discourse.pm.rejected.content'])


def pm_send_new_submit(user):
    pm('hitorino-admission',
       '一份新里区申请 %s' % (datetime.datetime.now().isoformat(sep=' '),),
       '一份新的里区申请： https://insider.hitorino.moe/admission/%d/' %
           (user.id))

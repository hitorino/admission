#coding=utf-8
import locale
if locale.getpreferredencoding().upper() != 'UTF-8':
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from msknet_censorship.models import *

from django.views.generic.list import ListView
from collections import namedtuple, OrderedDict
from . import worktile
from .utils import group_api
from social_django.models import UserSocialAuth


from msknet_censorship.models import SiteSettingManager
siteSetting = SiteSettingManager()

import logging

import re
QID = re.compile(r'qid_(\d+)')
YID = re.compile(r'yid_(\d+)')

logger =  logging.getLogger('PermissionLog')

uid_to_discourse_uid = group_api.uid_to_discourse_uid

def set_reviewed(user):
    Commit.objects.filter(user=user).update(is_under_review=False)

def latest_commit(user):
    return Commit.objects.filter(user=user).latest('commit_time') 

def set_latest_unreviewed(user):
    try:
        c=latest_commit(user)
        c.is_under_review=True
        c.save()
    finally:
        pass


GROUP_NAMES = ['pending', 'blacklisted']
def getGroups():
    if not getGroups.initialized:
        getGroups.GROUPS={}
        for gn in GROUP_NAMES:
            getGroups.GROUPS[gn] = Group.objects.get_or_create(name=gn)[0]
        getGroups.initialized = True
    return getGroups.GROUPS
    
getGroups.initialized = False

def move_to_group(user,groupname=''):
    try:
        for gn in GROUP_NAMES:
            user.groups.remove(getGroups()[gn])
        if groupname != '' and groupname in GROUP_NAMES:
            user.groups.add(getGroups()[groupname])
    finally:
        pass

def is_in_group(user,groupname):
    try:
        return getGroups()[groupname] in user.groups.all()
    except:
        return False

def is_censor(user):
    try:
        return group_api.is_censor(uid_to_discourse_uid(user.id))
    except:
        return False

def is_under_review(user):
    try:
        return latest_commit(user).is_under_review
    except:
        return False

# Create your views here.

class QuestionnaireListView(ListView):
    model = Questionnaire

def login(request):
    return render(request, 'msknet_censorship/login.html', {'next': request.GET['next']})

@login_required(login_url='/user-login/')
def official_quiz(request):
    if request.method == 'POST':
        return quiz_submit(request, 3)
    else:
        return quiz_show(request, 3)

@login_required(login_url='/user-login/')
def quiz(request,quiz_id):
    quiz_id = int(quiz_id)
    if request.method == 'POST':
        return quiz_submit(request, quiz_id)
    else:
        return quiz_show(request, quiz_id)



def quiz_show(request,quiz_id):
    info = {}
    info['questionnaire'] = Questionnaire.objects.filter(id=quiz_id)[0]
    info['questions'] = Question.objects.filter(questionnaire=info['questionnaire'])
    info['alert_link'] = 'https://forum.hitorino.moe/'
    info['alert_link_text'] = '回到论坛'
    if group_api.is_insider(uid_to_discourse_uid(request.user.id)):
        info['alert_message'] = siteSetting['msg.alert.insider']
        return render(request, 'msknet_censorship/alert.html', info)
    if len(Commit.objects.filter(user=request.user)) > 0:
        if latest_commit(request.user).is_under_review:
            info['alert_message'] = siteSetting['msg.alert.under_review']
            return render(request,'msknet_censorship/alert.html', info)
    if is_in_group(request.user,'blacklisted'):
        info['alert_message'] = siteSetting['msg.alert.blacklisted']
        return render(request,'msknet_censorship/alert.html', info)
    info['pending'] = is_in_group(request.user, 'pending')
    for q in info['questions']:
        if q.is_choice or q.is_choices():
            q.choice_all=Choice.objects.filter(question=q)
        elif q.is_table():
            q.x_axis_entries = AxisEntry.objects.filter(question=q, axis_number=1)
            q.y_axis_entries = AxisEntry.objects.filter(question=q, axis_number=2)
    info['dependencies'] = {}
    for dep in Dependency.objects.filter(question__questionnaire=info['questionnaire']):
        info['dependencies'][dep.question.id] = \
            info['dependencies'].get(dep.question.id, [])
        info['dependencies'][dep.question.id].append({
            'choice_id': dep.depends_on.id,
            'choice_question': dep.depends_on.question.id
        })
    info['dependencies'] = str(info['dependencies'])
    return render(request,'msknet_censorship/questionnaire_show.html',info)

def quiz_submit(request, quiz_id):
    if group_api.is_insider(uid_to_discourse_uid(request.user.id)):
        return HttpResponse('您已经是正式会员！',status=403)
    quiz = Questionnaire.objects.get(id=quiz_id)
    c = Commit.objects.create(questionnaire=quiz,user=request.user)
    for question in request.POST.keys():
        if not question.startswith('qid_'): continue
        qid = QID.search(question)
        if qid:
            qid = int(qid.group(1))
        q = Question.objects.filter(id=qid)[0]
        if q == None: continue
        ans = request.POST[question]
        if ans == None: continue
        
        a = Answer.objects.get_or_create(question=q,commit=c)[0]

        if ans == '' and not q.optional:
            #a.is_answered = False
            c.delete()
            return render(request,'msknet_censorship/alert.html',{
                'questionnaire':quiz,
                'alert_message': '表单不完整，请重新填写。',
                'alert_link': reverse('quiz'),
                'alert_link_text': '返回'
            })
        elif not ans or ans == '':
            continue
        elif q.is_choice or q.is_choices():
            s = Choice.objects.filter(id=int(ans))[0]
            a.choice_answer = s
        elif q.is_scale():
            a.scale_answer = int(ans)
        elif q.is_table() and YID.search(question):
            yid = int(YID.search(question).group(1))
            xid = int(ans)
            aea = AxisEntryAnswer.objects.create(answer=a,
                x_axis_answer = AxisEntry.objects.get(id=xid),
                y_axis_answer = AxisEntry.objects.get(id=yid))
        else:
            a.text_answer = ans
        a.save()
    c.save()
    group_api.pm_send_new_submit(request.user)
    return redirect('quiz') #,quiz_id=quiz_id)

@permission_required('msknet_censorship.manage_commit')
def decide_user(request,uid):
    if not ensure_admission(request):
        return redirect('quiz')
    suggest = UserSuggest.objects.get_or_create(elder=request.user,applicant=User.objects.get(id=uid))[0]
    if request.POST['decision'] in ('yes','no','unknown'):
        suggest.decision = {'yes':True,'no':False,'unknown':None}[request.POST['decision']]
    else:
        return HttpResponse('钦点内定也要按照基本法！',status=403)
    suggest.suggest = request.POST['suggest']
    suggest.save()
    return redirect('user-report',uid=uid)

@permission_required('msknet_censorship.manage_commit')
def clear_user_status(request,uid):
    if not ensure_admission(request):
        return redirect('quiz')
    if is_censor(request.user):#is_in_group(request.user,'censor'): #.is_staff:
        user=User.objects.get(id=uid)
        if is_under_review(user):
            set_latest_unreviewed(user)
        move_to_group(user,'')
        discourse_uid=uid_to_discourse_uid(uid)
        res_code, error = group_api.remove_from_group(discourse_uid)
        if res_code == 200:
            logger.info('管理员 %s 已经撤销用户 %s 的权限'%(request.user.username, user.username))
            return redirect('user-report',uid=uid)
        #elif res_code == 422:
        #    return HttpResponse('未曾加入过！请访问 '+'https://forum.hitorino.moe/admin/users/'+discourse_uid+'/'+user.username+' 修改！',status=res_code)
        else:
            return HttpResponse('删除失败！错误代码：HTTP %d' % (res_code,), status=res_code)
    else:
        return HttpResponse('钦点内定也要按照基本法！',status=403)

@permission_required('msknet_censorship.manage_commit')
def reject_user(request,uid):
    if not ensure_admission(request):
        return redirect('quiz')
    if is_censor(request.user): #,'censor'): #.is_staff:
        user=User.objects.get(id=uid)
        group_api.pm_send_reject(user)
        logger.info('管理员 %s 已驳回用户 %s 的申请，已发送站内信'%(request.user.username, user.username))
        set_reviewed(user)
        move_to_group(user,'pending')
        return redirect('user-report',uid=uid)
    else:
        return HttpResponse('钦点内定也要按照基本法！',status=403)

@permission_required('msknet_censorship.manage_commit')
def blacklist_user(request,uid):
    if not ensure_admission(request):
        return redirect('quiz')
    if is_censor(request.user):#,'censor'):#.is_staff:
        user=User.objects.get(id=uid)
        group_api.pm_send_blacklist(user)
        logger.info('管理员 %s 已彻底拒绝用户 %s 的申请，已发送站内信'%(request.user.username, user.username))
        set_reviewed(user)
        move_to_group(user,'blacklisted')
        return redirect('user-report',uid=uid)
    else:
        return HttpResponse('钦点内定也要按照基本法！',status=403)

@permission_required('msknet_censorship.manage_commit')
def modify_user(request,uid):
    if not ensure_admission(request):
        return redirect('quiz')
    if is_censor(request.user):#,'censor'): #.is_staff:
        user=User.objects.get(id=uid)
        group_api.pm_send_accept(user)
        logger.info('管理员 %s 已通过用户 %s 的申请，已发送站内信'%(request.user.username, user.username))
        set_reviewed(user)
        discourse_uid=uid_to_discourse_uid(uid)
        # 向 Discourse 添加
        res_code, error = group_api.add_to_group(discourse_uid)
        #logger.error("%d:%s"%(res_code,error))
        if res_code == 200:
            move_to_group(user,'')
            logger.info('管理员 %s 已经为用户 %s 加入权限'%(request.user.username, user.username))
            return redirect('user-report',uid=uid)
        #elif res_code == 422:
        #    return HttpResponse('已经加入过！请访问 '+'https://forum.hitorino.moe/admin/users/'+discourse_uid+'/'+user.username+' 修改！',status=res_code)
        else:
            return HttpResponse('加入失败！错误代码：HTTP %d' % (res_code,),status=res_code)
        #return redirect('https://hitorino.ren/admin/users/'+discourse_uid+'/'+user.username)
    else:
        return HttpResponse('钦点内定也要按照基本法！',status=403)

#@permission_required('msknet_censorship.manage_commit')
#def disallow_user(request,uid):
#    if request.user.is_staff:
#        user=User.objects.get(id=uid)
#        logger.info('管理员 %s 正在撤销用户 %s 的权限'%(request.user.username, user.username))
#        discourse_uid=uid_to_discourse_uid(uid)
#        res_code, error = group_api.remove_from_group(discourse_uid)
#        #logger.error("%d:%s"%(res_code,error))
#        if res_code == 200:
#            logger.info('管理员 %s 已经撤销用户 %s 的权限'%(request.user.username, user.username))
#            return redirect('user-report',uid=uid)
#        elif res_code == 422:
#            return HttpResponse('未曾加入过！请访问 '+'https://hitorino.ren/admin/users/'+discourse_uid+'/'+user.username+' 修改！',status=res_code)
#        else:
#            return HttpResponse('删除失败！请访问 '+'https://hitorino.ren/admin/users/'+discourse_uid+'/'+user.username+' 修改！',status=res_code)
#    else:
#        return HttpResponse('钦点内定也要按照基本法！',status=403)

EinKommit=namedtuple('EinKommit',['questions','commit'])
@permission_required('msknet_censorship.manage_commit',login_url='/login/discourse')
def report_user(request,uid):
    if not ensure_admission(request):
        return redirect('quiz')
    info = {'censor':request.user,'uid':uid}
    user = User.objects.get(id=uid)
    try:
        info['suggest'] = UserSuggest.objects.get(elder__id=request.user.id,applicant=user)
    except:
        info['suggest'] = False
    info['suggestions'] = UserSuggest.objects.filter(applicant=user)
    info['suggestions_agree'] = info['suggestions'].filter(decision=True)
    info['suggestions_disagree'] = info['suggestions'].filter(decision=False)
    info['blacklisted'] = is_in_group(user,'blacklisted')
    info['pending'] = is_in_group(user,'pending')
    info['insider'] = group_api.is_insider(uid_to_discourse_uid(uid))
    info['is_under_review'] = is_under_review(user)
    info['username'] = user.username
    info['duid'] = uid_to_discourse_uid(uid)
    info['commits'] = []
    for c in Commit.objects.filter(user=user).order_by('-commit_time'):
        info['commits'].append(EinKommit(questions=OrderedDict([(a.question.question_text, a._content_text()) for a in Answer.objects.filter(commit=c)]),commit=c))
    return render(request, 'msknet_censorship/adm_report_user.html',info)

@permission_required('msknet_censorship.manage_commit')
def delete_commit(request,cid):
    if not ensure_admission(request):
        return redirect('quiz')
    ensure_admission(request)
    Commit.objects.filter(id=cid).delete()
    return redirect(request.GET.get('next','/'))

@permission_required('msknet_censorship.manage_commit')
def user_list(request):
    if not ensure_admission(request):
        return redirect('quiz')
    context = {}
    commit_list = Commit.objects.exclude(user__username__contains='misaka-commander')

    context['insider_list']=[group_api.discourse_uid_to_uid(i['id']) for i in group_api.get_insiders()]
    context['blacklisted'] = getGroups()['blacklisted'].user_set.all()
    context['pending'] = getGroups()['pending'].user_set.all()
    context['user_list'] = OrderedDict()

    for c in commit_list:
        user = c.user
        user.has_commit = True
        user.reviewing = c.is_under_review
        user.commit_time = c.commit_time
        user.suggested = user.suggestions.filter(elder=request.user).count()>0
        if user.id in context['user_list'].keys():
            del context['user_list'][user.id]
        context['user_list'][user.id] = user
    
    context['user_list'] = list(context['user_list'].values())
    return render(request, 'msknet_censorship/user_list.html', context)

def ensure_admission(request):
    duid = uid_to_discourse_uid(request.user.id)
    admission = Group.objects.get_or_create(name='admission')[0]
    if group_api.is_censor(duid):
        request.user.groups.add(admission)
        request.user.save()
        return True
    else:
        request.user.groups.remove(admission)
        request.user.save()
        return False
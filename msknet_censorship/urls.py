from django.conf.urls import url,include
from django.contrib import admin
from msknet_censorship.views import *
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^application/$', official_quiz, name='quiz'),
    #url(r'^questionnaire/(?P<quiz_id>[0-9]+)/$', quiz, name='quiz'),
#    url(r'^questionnaire/$',QuestionnaireListView.as_view(),name='quiz-list'),
    url(r'^admission/(?P<uid>[0-9]+)/$',report_user,name='user-report'),
    url(r'^admission/(?P<uid>[0-9]+)/decide/$',decide_user,name='user-decision'),
#    url(r'^user-report/(?P<uid>[0-9]+)/disallow/$',disallow_user,name='user-disallow'),
    url(r'^admission/(?P<uid>[0-9]+)/modified/$',modify_user,name='user-modified'),
    url(r'^admission/(?P<uid>[0-9]+)/reject/$',reject_user,name='user-rejected'),
    url(r'^admission/(?P<uid>[0-9]+)/blacklist/$',blacklist_user,name='user-blacklisted'),
    url(r'^admission/(?P<uid>[0-9]+)/clear-status/$',clear_user_status,name='user-status-clear'),
    url(r'^admission/commit/(?P<cid>[0-9]+)/delete/$',delete_commit,name='delete-commit'),
    url(r'^admission/$',user_list,name='user-list'),
    url(r'user-login/',login,name='user-login'),
    url(r'^$',RedirectView.as_view(pattern_name='quiz', permanent=True), name='index'),
# url(r'^$',QuestionnaireListView.as_view(),name='quiz-list'),
]

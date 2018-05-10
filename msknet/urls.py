"""msknet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url,include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.views.generic.base import RedirectView
from django.shortcuts import redirect

urlpatterns = [
        url(r'^management/', admin.site.urls),
        url(r'^logout/$',(lambda req:(lambda x:redirect(req.GET['next'] if 'next' in req.GET else 'quiz'))(logout(req))),name='logout'),
        url(r'^login/$',RedirectView.as_view(url='discourse/', permanent=False,query_string=True),name='login'),
        url(r'',include('social.apps.django_app.urls',namespace='social')),
        url(r'',include('msknet_censorship.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

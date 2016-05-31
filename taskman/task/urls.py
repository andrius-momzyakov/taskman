"""taskman URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from django.contrib import admin

from . import views as v

urlpatterns = [
    url(r'^new/$', v.NewTask.as_view(), name='new'),
    url(r'^detail/(?P<slug>[0-9]+)/$', v.TaskDetail.as_view(), name='detail'),
    url(r'^edit/(?P<task_id>[0-9]+)/$', v.EditTask.as_view(), name='edit'),
    url(r'^file/(?P<name>.*)$', v.serve_file, name='file'),
    url(r'^comment/$', v.NewComment.as_view(), name='comment'),
    url(r'^attachment/$', v.NewAttachment.as_view(), name='attachment'),
    url(r'^page(?P<page>[0-9]+)/$', v.TaskList.as_view(), name='home'),
    url(r'setpriority/(?P<task_id>\d+)/$', v.update_task_priority, name='priority'),
    url(r'^$', v.root)
]

#-*- coding: utf-8 -*-
from django.conf.urls import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . views import (meetingsinfo, CreateWebinarViewSet, startwebinar, get_meeting_info, WebinarRequestViewSet)
from django.conf.urls import include, url
from django.contrib.auth.views import login
from django.views.i18n import javascript_catalog


js_info_dict = {
  'packages': ()
}

urlpatterns = [
    url(r'^meetingsinfo/$', meetingsinfo, name='meetingsinfo'),

    url(r'^create_webinar/$', CreateWebinarViewSet.as_view(actions={
        "get": "list",
        "post": "create"
    }), name='create_webinar'),

    url(r'^create_webinar/(?P<pk>[0-9]+)/$', CreateWebinarViewSet.as_view(actions={
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy"
    }), name='detail_webinar'),

    url(r'^create_webinar/(?P<webinar_id>[0-9]+)/requests/$', WebinarRequestViewSet.as_view(actions={
        "get": "list",
        "post": "create"
    })),

    url(r'^create_webinar/(?P<webinar_id>[0-9]+)/requests/(?P<pk>[0-9]+)$', WebinarRequestViewSet.as_view(actions={
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy"
    })),

    url(r'^meeting/(?P<meeting_id>[a-zA-Z0-9 _-]+)/startwebinar$', startwebinar, name='start_webinar'),

    url(r'^getmeetinginfo/(?P<meeting_id>[a-zA-Z0-9 _-]+)/$', get_meeting_info, name='get_meeting_info'),
    ]


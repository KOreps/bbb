# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from time import strftime, localtime

from django.utils.translation import ugettext_lazy as _

from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from . models import Webinar
from . import settings
from django.template.response import TemplateResponse
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from base.views import MetaData, AutoJoinPermissionsMixin
from permissions_api.permissions import DjangoModelPermissionsWithView
from . import models, serializers


@login_required
def start_meeting(request, meeting_id):
    meeting = Webinar.objects.get(id=meeting_id)
    if request.user == meeting.owner:
        result = meeting.create_and_get_url()
        if result == 'error':
            return (
                error(
                    request,
                    text=_('sorry! server BBB unavailable now'))
            )
        return (
            HttpResponseRedirect(
                meeting.join_url(
                    request.user.username,
                    meeting.moderator_password,
                    request,
                    start=1))
        )
    else:
        return error(request, text=_('sorry! You can`t start this conference'))


@login_required
def meetingsinfo(request):
    """ Список вебинаров """
    my_meetings = Webinar.get_meetings_info(request.user)
    return JsonResponse(list(my_meetings), safe=False)


class CreateWebinarViewSet(viewsets.ModelViewSet, AutoJoinPermissionsMixin):
    serializer_class = serializers.WebinarSerializer
    metadata_class = MetaData
    permission_classes = (DjangoModelPermissionsWithView,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        if self.action == 'retrieve':
            return Webinar.objects.filter(id=int(self.kwargs.get('pk')))
        else:
            return Webinar.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class WebinarRequestViewSet(viewsets.ModelViewSet, AutoJoinPermissionsMixin):
    metadata_class = MetaData
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return models.WebinarRequest.objects.select_related('from_user').filter(webinar=self.kwargs['webinar_id'])

    def get_serializer_class(self):
        return {
            "list": serializers.WebinarRequestSerializer,
            "retrieve": serializers.WebinarRequestSerializer,
            "create": serializers.WebinarRequestSerializer,
            "update": serializers.WebinarRequestSerializerUpdate,
            "partial_update": serializers.WebinarRequestSerializerUpdate,
            "metadata": serializers.WebinarRequestSerializer
        }[self.action]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user,
                        webinar_id=self.kwargs['webinar_id'])


@login_required
def startwebinar(request, meeting_id):
    meeting = Webinar.objects.get(id=meeting_id)
    result = meeting.create_and_get_url()
    if result == 'error':
        return JsonResponse({"type": "error", "message": _("BigBlueButton server is not available now")})
    if request.user.get_full_name() != "":
        fullname = request.user.get_full_name()
    else:
        fullname = request.user.username
        moderator_password = meeting.moderator_password if meeting.moderator_password != '' else settings.MODERATOR_PASSWORD
    return JsonResponse({"type": "success", "join_url": meeting.join_url(
        fullname,
        meeting.moderator_password,
        request,
        start=1
    )})


@login_required
def get_meeting_info(request, meeting_id):
    meeting = Webinar.objects.get(id=meeting_id)
    recordings = meeting.get_records()
    mess = ''
    if recordings == 'error':
        recordings = None
        mess = _('Server BBB unavailable now')
    rec_array = []
    for i in recordings:
        elem = i.__dict__
        rec_array.append(elem)
    return JsonResponse({'recordings': rec_array, 'mess': mess}, safe=False)
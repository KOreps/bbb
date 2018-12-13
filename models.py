#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _
from project.settings import AUTH_USER_MODEL
from auditlog.registry import auditlog

from urllib2 import urlopen
from urllib import urlencode
from hashlib import sha1
import xml.etree.ElementTree as ET
import random
from time import gmtime, strftime

from . import settings
from django.utils import timezone
from random import randrange
import json
import datetime
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import transaction

from users.models import User


def parse(response):
    try:
        xml = ET.XML(response)
        code = xml.find('returncode').text
        if code == 'SUCCESS':
            return xml
        else:
            raise
    except:
        return 'error'


def connect_bbb(url):
    try:
        result = urlopen(url).read()
    except:
        result = 'error'
    return result


class Record():
    id = ''
    type = ''
    url = ''
    published = ''
    starttime = ''
    endtime = ''
    start_time = ''
    end_time = ''
    participants = ''


class Webinar(models.Model):

    name = models.CharField(
        verbose_name=_('name'),
        max_length=100,
        unique=True)
    webinar_description = RichTextUploadingField(null=True, blank=True, verbose_name=_("webinar_description"))
    photo = models.ImageField(_("Upload photo"), upload_to='webinar_photos', null=True, blank=True)
    attendee_password = models.CharField(
        verbose_name=_('password of user'),
        max_length=50, blank=True) #set True
    moderator_password = models.CharField(
        verbose_name=_('password of moderator'),
        max_length=50, blank=True) #set True
    duration = models.TimeField(verbose_name=_('duration'),
                                blank=True,
                                null=True,
                                )
    # Записывать
    record = models.BooleanField(verbose_name=_('make record'), default=False)
    timestart = models.DateTimeField(verbose_name=_('data time of start'),
                                     default=timezone.now

                                     )
    timestop = models.DateTimeField(
        verbose_name=_('date time of end'),
        null=True)
    # Публичная
    public = models.BooleanField(verbose_name=_('is public'), default=True)
    # Доступно извне
    openout = models.BooleanField(
        verbose_name=_('is open from out'),
        default=True)
    # Приветственное сообщение
    welcome_message = models.CharField(
        default=_('Welcome message'),
        help_text=_('Message which displayed on the chat window'),
        max_length=200, blank=True, null=True)
    owner = models.ForeignKey(AUTH_USER_MODEL)
    running = ''
    info = None

    participants = models.ManyToManyField(User, related_name="Webinar_User",
                                          verbose_name=_("participants"), blank=True)

    def __unicode__(self):
        return "%s" % self.name

    class Search:
        filters = {
            "name": "__default__",
        }

    @classmethod
    def api_call(self, query, call):
        prepared = "%s%s%s" % (call, query, settings.SALT)
        checksum = sha1(prepared).hexdigest()
        result = "%s&checksum=%s" % (query, checksum)
        return result

    def is_running(self):
        call = 'isMeetingRunning'
        query = urlencode((
            ('meetingID', 'meeting_' + str(self.id)),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        if result == 'error':
            return 'error'
        elif result != 2:
            return result.find('running').text
        else:
            return 'not running'

    def end_meeting(self, password):
        call = 'end'
        query = urlencode((
            ('meetingID', 'meeting_' + str(self.id)),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        if result:
            pass
        else:
            return 'error'

    @classmethod
    def meeting_info(self, id, password):
        call = 'getMeetingInfo'
        query = urlencode((
            ('meetingID', 'meeting_' + str(id)),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        print url
        r = parse(connect_bbb(url))
        if r:
            d = {
                _('participant count'): r.find('participantCount').text,
                _('moderator count'): r.find('moderatorCount').text,
                _('password of user'): r.find('attendeePW').text,
                _('password of moderator'): r.find('moderatorPW').text,
            }
            return d
        else:
            return None

    @classmethod
    def url_meetings(self):
        call = 'getMeetings'
        query = urlencode((
            ('random', randrange(100000, 1000000)),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        return url

    @classmethod
    def del_record(self, recID):
        call = 'deleteRecordings'
        query = urlencode((
            ('recordID', str(recID)),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        print url
        r = parse(connect_bbb(url))
        return r

    @classmethod
    def get_meetings(self, user=None, admin=None):
        if user:
            if admin:
                meetings = Webinar.objects.all()
            else:
                meetings = Webinar.objects.filter(owner=user)
        else:
            meetings = Webinar.objects.filter(public=True)
        call = 'getMeetings'
        query = urlencode((
            ('random', 'random'),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        d = []
        print str(dir(result[1]))
        for meeting in meetings:
            if result != 'error' and result:
                list_meeting_bbb = result[1].findall('meeting')
                for m in list_meeting_bbb:
                    meetingID = m.find('meetingID').text
                    if 'meeting_' + str(meeting.id) == meetingID:
                        meeting.running = m.find('running').text
                        meeting.info = meeting.meeting_info(
                            meeting.id,
                            meeting.moderator_password)
            d.append(meeting)
        return d

    def create_and_get_url(self):
        call = 'create'
        voicebridge = 70000 + random.randint(0, 9999)
        mettingID = 'meeting_' + str(self.id)
        query = urlencode((
            ('meetingID', mettingID),
            ('name', self.name.encode('utf-8')),
            ('attendeePW', self.attendee_password),
            ('moderatorPW', self.moderator_password),
            ('voiceBridge', voicebridge),
            ('logoutURL ', settings.logoutURL),
            ('duration', self.duration),
            ('record', self.record),
            ('welcome', self.welcome_message.encode('utf-8')),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        return result

    @classmethod
    def change_public_record(self, record_id, publish):
        call = 'publishRecordings'
        if publish == 'true':
            publish = 'false'
        else:
            publish = 'true'
        query = urlencode((
            ('recordID', record_id),
            ('publish', publish),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        return result

    def get_records(self):
        call = 'getRecordings'
        query = urlencode((
            ('meetingID', 'meeting_' + str(self.id)),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        records = []
        if result == 'error':
            return result
        if result is not None:
            for r in result.find('recordings').findall('recording'):
                rec = Record()
                rec.id = r.find('recordID').text
                playbacks = r.findall('playback')
                rec.published = r.find('published').text
                rec.start_time = int(r.find('startTime').text)
                rec.end_time = int(r.find('endTime').text)
                rec.participants = int(r.find('participants').text)

                for p in playbacks:
                    for f in p.findall('format'):
                        rec.type = f.find('type').text
                        rec.url = f.find('url').text
                records.append(rec)
        return records

    def join_url(self, name, password, request, start=0):
        call = 'join'
        flag = 0
        if start == 0:
            if self.is_running() != 'false':
                flag = 1
            else:
                url = 'not running'
        else:
            flag = 1
        if flag == 1:
            if request.user.id == self.owner.id:
                query = urlencode((
                    ('fullName', name.encode('utf-8')),
                    ('meetingID', 'meeting_' + str(self.id)),
                    ('password', password),
                ))
            else:
                query = urlencode((
                    ('fullName', name.encode('utf-8')),
                    ('meetingID', 'meeting_' + str(self.id)),
                    ('password', password),
                    ('role', 'VIEWER')
                ))
            hashed = self.api_call(query, call)
            url = settings.BBB_API_URL + call + '?' + hashed
        return url

    @classmethod
    def get_meetings_info(self, user=None, admin=None):
        if user:
            if admin:
                meetings = Webinar.objects.all()
            else:
                meetings = Webinar.objects.filter(owner=user)
        else:
            meetings = Webinar.objects.filter(public=True)
        call = 'getMeetings'
        query = urlencode((
            ('random', 'random'),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse(connect_bbb(url))
        d = []
        print str(dir(result[1]))
        for meeting in meetings:
            if result != 'error' and result:
                list_meeting_bbb = result[1].findall('meeting')
                for m in list_meeting_bbb:
                    meetingID = m.find('meetingID').text
                    if 'meeting_' + str(meeting.id) == meetingID:
                        meeting.running = m.find('running').text
                        meeting.info = meeting.meeting_info(
                            meeting.id,
                            meeting.moderator_password)
            from django.forms.models import model_to_dict
            d_dict = model_to_dict(meeting)
            meet_inf = meeting.__dict__
            d.append(d_dict)
        return d


class WebinarRequest(models.Model):
    _user_field = 'from_user'

    CHOICES = (
        ('', _("New")),
        ('y', _('Accepted')),
        ('n', _('Rejected'))
    )

    webinar = models.ForeignKey(Webinar, verbose_name=_("Webinar"))
    accepted = models.CharField(max_length=1, default='', choices=CHOICES, null=False, blank=True,
                                verbose_name=_("accepted"))

    from_user = models.ForeignKey(User, related_name="sent_webinar_requests", null=False, blank=False,
                                  verbose_name=_("from_user"))

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.accepted == 'y':
            self.webinar.participants.add(getattr(self, self._user_field))
        super(WebinarRequest, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("WebinarRequest")
        verbose_name_plural = _("WebinarRequests")
        unique_together = (("webinar", "from_user"),)


auditlog.register(WebinarRequest)


""" Список зарегистрированных на вебинар пользователей  """
class Registration(models.Model):
    user = models.OneToOneField(
        AUTH_USER_MODEL, models.CASCADE, primary_key=True,
        related_name='registration_user',
        verbose_name=_('user'),
        help_text=_('User'))
    meetings = models.ManyToManyField(
        Webinar,
        verbose_name=_('List of meetings that the user is registered')
    )
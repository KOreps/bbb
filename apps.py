# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class BigbluebuttonConfig(AppConfig):
    name = 'webinar'
    verbose_name = _('webinar')
    verbose_name_plural = _('webinars')

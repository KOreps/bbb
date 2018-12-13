from django.contrib import admin
from .models import Webinar, Registration, WebinarRequest


class WebinarAdmin(admin.ModelAdmin):
    list_display = ('name', 'webinar_description', 'owner',)
    search_fields = ('name',)


class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user',)


class WebinarRequestAdmin(admin.ModelAdmin):
    list_filter = ('webinar', 'from_user')
    list_display = ("webinar", "from_user", "accepted",)


admin.site.register(Webinar, WebinarAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(WebinarRequest, WebinarRequestAdmin)

from rest_framework import serializers
from . import models
from project.settings import AUTH_USER_MODEL
from base.rest_utils import ObjectPermissionsMixin, StringIdField, ObjectMethodField
from .permissions import WebinarRequestViewSetPermissions as WebinarRequestsPerm


class WebinarSerializer(serializers.ModelSerializer):
    owner_verbose_name = serializers.SerializerMethodField(read_only=True)
    participants = StringIdField(many=True)
    user_invites = serializers.SerializerMethodField(read_only=True)
    __childs_perm__ = serializers.SerializerMethodField()

    class Meta:
        model = models.Webinar
        # fields = '__all__'
        exclude = ('openout',)

    owner = serializers.PrimaryKeyRelatedField(
        queryset=AUTH_USER_MODEL,
        default=serializers.CurrentUserDefault()
    )
    moderator_password = serializers.CharField(required=True)

    def get_owner_verbose_name(self, obj):
        if obj.owner.get_full_name() == '':
            return obj.owner.username
        else:
            return obj.owner.get_full_name()

    def get___childs_perm__(self, obj):
        if 'request' not in self.context:
            return None
        user = self.context["request"].user
        return {
            "add_request": bool(WebinarRequestsPerm.check("create", user, obj, context=self.context)),
            "view_request": bool(WebinarRequestsPerm.check("list", user, obj, context=self.context)),
        }

    def get_user_invites(self, webinar):
        if 'request' not in self.context:
            return None
        user = self.context['request'].user
        webinar_request = webinar.webinarrequest_set.filter(from_user=user).first()
        return {
            "webinar_request": WebinarRequestSerializer(webinar_request).data if webinar_request else None
        }


class WebinarRequestSerializer(serializers.ModelSerializer, ObjectPermissionsMixin):
    from_user = StringIdField()
    accepted_display = ObjectMethodField(prefix="get_")

    class Meta:
        model = models.WebinarRequest
        fields = ("id", "accepted", "accepted_display", "from_user",)
        read_only_fields = fields


class WebinarRequestSerializerUpdate(serializers.ModelSerializer):

    class Meta:
        model = models.WebinarRequest
        fields = ("accepted",)

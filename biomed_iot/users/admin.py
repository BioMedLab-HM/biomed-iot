from core.admin_site import admin_site
from django.contrib import admin
from .models import CustomUser, Profile, NodeRedUserData, MqttClient, MqttMetaData, InfluxUserData


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'image')

class NodeRedUserDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'container_name', 'container_port', 'username', 'password', 'access_token')

class MqttClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'username', 'password', 'textname', 'rolename')

class MqttMetaDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_topic_id', 'nodered_role_name', 'device_role_name')

class InfluxUserDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'bucket_name', 'bucket_id', 'bucket_token', 'bucket_token_id')

# use custom admin_site instead of admin.site
admin_site.register(CustomUser)
admin_site.register(Profile, ProfileAdmin)
admin_site.register(NodeRedUserData, NodeRedUserDataAdmin)
admin_site.register(MqttClient, MqttClientAdmin)
admin_site.register(MqttMetaData, MqttMetaDataAdmin)
admin_site.register(InfluxUserData, InfluxUserDataAdmin)

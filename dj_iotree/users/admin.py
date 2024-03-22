from django.contrib import admin
from .models import Profile
from .models import NodeRedUserData
from .models import MqttClient
from .models import MqttMetaData


admin.site.register(Profile)
admin.site.register(MqttMetaData)
admin.site.register(MqttClient)
admin.site.register(NodeRedUserData)

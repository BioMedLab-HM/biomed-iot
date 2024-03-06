from django.contrib import admin
from .models import Profile
from .models import NodeRedUserData
from .models import MQTTClient


admin.site.register(Profile)
admin.site.register(NodeRedUserData)
admin.site.register(MQTTClient)

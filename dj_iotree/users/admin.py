from django.contrib import admin
from .models import CustomUser
from .models import Profile
from .models import NodeRedUserData
from .models import MqttClient
from .models import MqttMetaData
from .models import InfluxUserData


admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(MqttMetaData)
admin.site.register(MqttClient)
admin.site.register(NodeRedUserData)
admin.site.register(InfluxUserData)

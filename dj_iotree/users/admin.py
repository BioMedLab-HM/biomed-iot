from django.contrib import admin
from .models import Profile
from .models import NodeRedUserData
from .models import MosquittoGroup
from .models import MosquittoRole
from .models import MosquittoClientData


admin.site.register(Profile)
admin.site.register(NodeRedUserData)
admin.site.register(MosquittoGroup)
admin.site.register(MosquittoRole)
admin.site.register(MosquittoClientData)

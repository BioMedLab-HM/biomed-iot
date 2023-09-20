from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='core-home'),
    path('about/', views.about, name='core-about'),
    path('contact-us/', views.contact_us, name='core-contact-us'),
    path('impressum/', views.impressum, name='core-impressum'),
]
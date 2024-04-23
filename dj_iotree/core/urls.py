from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='core-home'),
    path('manual/', views.manual, name='core-manual'),
    path('about/', views.about, name='core-about'),
    path('contact-us/', views.contact_us, name='core-contact-us'),  # remove?
    path('legal-notice/', views.legal_notice, name='core-legal-notice'),
    path('privacy-policy/', views.privacy_policy, name='core-privacy-policy'),
]
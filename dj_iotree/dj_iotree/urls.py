"""
URL configuration for dj_iotree project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # path('auth/callback/', views.oauth_callback, name='oauth_callback'),

    path('devices/', user_views.devices, name='devices'),
    path('add-client/', user_views.add_client, name='add-client'),
    path('modify-client/<str:client_username>/', user_views.modify_client, name='modify-client'),
    path('delete-client/<str:client_username>/', user_views.delete_client, name='delete-client'),

    path('nodered-manager/', user_views.nodered_manager, name='nodered-manager'),
    path('nodered-embedded/', user_views.nodered_embedded, name='nodered-embedded'),
    path('nodered-status-check/', user_views.nodered_status_check, name='nodered-status-check'),

    path('data-explorer/', user_views.data_explorer, name='data-explorer'),

    path('grafana-embedded/', user_views.grafana_embedded, name='grafana-embedded'),

    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),

    # path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),  # uses Django's own login view
    path('login/', user_views.user_login, name='login'),
    # path('login/', user_views.CustomLoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    # path('set_timezone/', user_views.set_timezone, name='set_timezone'),
    path('', include('core.urls')),
]

# TODO: static files; not for production use, see "Deploying static files" (https://docs.djangoproject.com/en/4.2/howto/static-files/)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

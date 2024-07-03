"""
URL configuration for biomed_iot project.

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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
# from users.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    # path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # path('auth/callback/', views.oauth_callback, name='oauth_callback'),

    path('devices/', user_views.devices, name='devices'),
    path('message-and-topic-structure/', user_views.message_and_topic_structure, name='message-and-topic-structure'),
    path('code-examples/', user_views.code_examples, name='code-examples'),
    path('setup-gateway/', user_views.setup_gateway, name='setup-gateway'),

    path('nodered-manager/', user_views.nodered_manager, name='nodered-manager'),
    path('nodered-create/', user_views.nodered_create, name='nodered-create'),
    path('nodered-wait/', user_views.nodered_wait, name='nodered-wait'),
    path('nodered-open/', user_views.nodered_open, name='nodered-open'),
    path('nodered-restart/', user_views.nodered_restart, name='nodered-restart'),
    path('nodered-unavailable/', user_views.nodered_unavailable, name='nodered-unavailable'),
    path('nodered-status-check/', user_views.nodered_status_check, name='nodered-status-check'),
    path('nodered/', user_views.nodered, name='nodered'),
    path('nodered-dashboard/', user_views.nodered_dashboard, name='nodered-dashboard'),
    path('access-nodered/', user_views.access_nodered, name='access-nodered'),  # access-nodered/<str:token>/

    path('manage-data/', user_views.manage_data, name='manage-data'),

    path('visualize/', user_views.visualize, name='visualize'),
    path('get-grafana/', user_views.get_grafana, name='get-grafana'),
    re_path(r'^grafana/(?P<path>.*)$', user_views.GrafanaProxyView.as_view(), name='grafana-proxy'),

    path('register/', user_views.register, name='register'),
    path('verify/<uidb64>/<token>/', user_views.verify_email, name='verify-email'),

    # download urls with filename sanitization to prevent directory traversal. 
    # Allows only alphanumeric characters, underscores, hyphens, and periods and no slash or backslash
    re_path(r'^download/(?P<filename>[\w\-. ]+)$', user_views.public_download, name='public_download'),
    re_path(
        r'^restricted_download/(?P<filename>[\w\-. ]+)$', 
        user_views.restricted_download, 
        name='restricted_download'
        ),

    path('profile/', user_views.profile, name='profile'),

    # path('login/', user_views.user_login, name='login'),  # Old version. Keep as backup
    path('login/', user_views.CustomLoginView.as_view(template_name='users/login.html'), name='login'),

    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
        name='password_reset_complete',
    ),

    # path('set_timezone/', user_views.set_timezone, name='set_timezone'),

    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_DEVELOPMENT)

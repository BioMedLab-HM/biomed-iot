import os
import jwt
from datetime import datetime, timedelta, timezone
import requests
import secrets
import json
import logging
import mimetypes
from influxdb_client import InfluxDBClient
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404, StreamingHttpResponse
from django.db import IntegrityError
from django.db import transaction
from .models import NodeRedUserData, CustomUser, Profile  # noqa: F401
from .forms import UserRegisterForm, UserUpdateForm, UserLoginForm, MqttClientForm, SelectDataForm
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType
from .services.nodered_utils import NoderedContainer, update_nodered_nginx_conf
from .services.code_loader import load_code_examples, load_nodered_flow_examples
from .services.email_templates import registration_confirmation_email
from .services.influx_data_utils import InfluxDataManager, to_rfc3339
from biomed_iot.config_loader import config
from revproxy.views import ProxyView
# For classed based login view, remove comment after tests
from django.contrib.auth.views import LoginView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings


logger = logging.getLogger(__name__)


def send_verification_email(user, request):
    # To be called right after creating the user instance in the registration logic
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    url = request.build_absolute_uri(reverse('verify-email', kwargs={'uidb64': uid, 'token': token}))
    message = registration_confirmation_email(url)
    subject = 'Biomed IoT - Verify your email address'
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
    except Exception as e:
        logger.error(f'Failed to send email: {e}')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = None
            try:
                user = form.save()  # noqa F841
                if config.mail.EMAIL_VERIFICATION == "true":
                    send_verification_email(user, request)
                    msg = ('Your account has been created! '
                           'Click the link in the confirmation email that was sent to you.')
                    messages.success(request, msg)
                    return redirect('login')
                messages.success(request, 'Your account has been created! You are now able to log in')
                return redirect('login')
            except Exception:
                if user:
                    user.delete()
                messages.error(request, 'An error occurred while creating your account. Please try again.')
    else:
        form = UserRegisterForm()

    page_title = 'Register'
    context = {'form': form, 'title': page_title, 'thin_navbar': False}
    return render(request, 'users/register.html', context)


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_confirmed = True
        user.save()
        messages.success(request, 'Email has been verified')
        return redirect('login')
    else:
        messages.error(request, 'The link is invalid or has expired.')
        return redirect('login')


class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('core-home')
    extra_context = {'title': 'Login'}

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        user = form.get_user()
        logger.info('User logged in successfully: %s', user.email)
        login(self.request, user)
        return redirect(self.get_success_url())


@login_required
def profile(request):
    context = {}
    if request.method == 'POST':  # Changing Profile info currently not active
        u_form = UserUpdateForm(request.POST, instance=request.user)
        # p_form: Profile form commented out because it only contains an image which is currently not used
        # p_form = ProfileUpdateForm(request.POST,
        #                            request.FILES,  # FILES is an Image
        #                            instance=request.user.profile)
        if u_form.is_valid():  # and p_form.is_valid():
            u_form.save()
            # p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        # p_form = ProfileUpdateForm(instance=request.user.profile)

    page_title = 'Your User Profile'
    context = {
        'title': page_title,
        'u_form': u_form,
        # 'p_form': p_form
        'thin_navbar': False,
        'user': request.user,
    }

    return render(request, 'users/profile.html', context)


@login_required
def devices(request):
    """
    For inexperienced user, MQTT-Clients are called devices since each client is usually linked to a device
    although theoretically, one could use more than one client on one device.
    For technical correctness, the term client is used here.
    """
    print('in "devices view"')
    mqtt_client_manager = MqttClientManager(request.user)

    if request.method == 'POST':
        new_device_form = MqttClientForm(request.POST)
        if request.POST.get('action') == 'create':
            print('in "create"')
            if new_device_form.is_valid():
                print('form is valid')
                new_textname = new_device_form.cleaned_data['textname']
                print(f'New Textname from form = {new_textname}')
                mqtt_client_manager.create_client(textname=new_textname, role_type=RoleType.DEVICE.value)
                print('after create client')
                messages.success(request, f'Device with name "{new_textname}" successfully created.')
                return redirect('devices')
            else:
                messages.error(request, 'Device name is not valid. Max. 30 characters!')
                return redirect('devices')

        elif 'modify' in request.POST:
            # see MqttClientManager.modify_client()
            pass

        elif request.POST.get('device_username'):  # TODO: ambiguous! --> could also be sth else than delete.
            client_username = request.POST.get('device_username')
            print(f'delete device ({client_username}) case')
            success = mqtt_client_manager.delete_client(client_username)
            print(success)
            if success:
                messages.success(
                    request,
                    f'Device with username "{client_username}" successfully deleted.',
                )
                return redirect('devices')
            else:
                messages.error(request, 'Failed to delete the device. Please try again.')
                return redirect('devices')

    mqtt_meta_data_manager = MqttMetaDataManager(request.user)
    topic_id = mqtt_meta_data_manager.metadata.user_topic_id
    in_topic = f'in/{topic_id}/your/subtopic'
    out_topic = f'out/{topic_id}/your/subtopic'

    new_device_form = MqttClientForm()
    # get list of all device clients
    device_clients_data = mqtt_client_manager.get_device_clients()

    context = {
        'in_topic': in_topic,
        'out_topic': out_topic,
        'topic_id': topic_id,
        'device_clients': device_clients_data,
        'form': new_device_form,
        'title': 'Devices',
        'thin_navbar': False,
    }
    return render(request, 'users/devices.html', context)


@login_required
def message_and_topic_structure(request):
    mqtt_meta_data_manager = MqttMetaDataManager(request.user)
    topic_id = mqtt_meta_data_manager.metadata.user_topic_id
    in_topic = f'in/{topic_id}/your/subtopic'
    out_topic = f'out/{topic_id}/your/subtopic'

    message_example = {
        'temperature': 25.3,
        'timestamp': 1713341175,
    }
    message_example_large = {
        'temperature': 25.3,
        'humidity': 50,
        'sensorX': 'text value',
        '...': '...',
        'timestamp': 1713341175,
    }

    message_example_json = json.dumps(message_example, indent=4)
    message_example_large_json = json.dumps(message_example_large, indent=4)

    current_server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context = {
        'message_example': message_example_json,
        'message_example_large': message_example_large_json,
        'in_topic': in_topic,
        'out_topic': out_topic,
        'topic_id': topic_id,
        'current_server_time': current_server_time,
        'title': 'Message & Topic Structure',
        'thin_navbar': False,
    }
    return render(request, 'users/message_and_topic_structure.html', context)


@login_required
def code_examples(request):
    examples_content = load_code_examples()

    page_title = 'Code Examples'
    context = {'title': page_title, 'examples': examples_content, 'thin_navbar': False}
    return render(request, 'users/code_examples.html', context)


@login_required
def setup_gateway(request):
    tls = config.host.TLS == "true"
    if request.method == 'POST':
        if tls:
            file_name = 'biomed_iot_gateway.zip'
            download_path = reverse('public_download', args=[file_name])
            return redirect(download_path)
        else:
            msg = "Gateway is currently only available for setups using TLS (https)."
            messages.info(request, msg)
            return redirect('setup-gateway')

    if config.host.DOMAIN != "":
        hostname = config.host.DOMAIN
    else:
        hostname = config.host.IP

    page_title = 'Gateway Setup'
    download_url = f"https://{hostname}/download/biomed_iot_gateway.zip" if tls else ""
    context = {'title': page_title, 'download_url': download_url, 'tls': tls}
    return render(request, 'users/setup_gateway.html', context)


def public_download(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'public_download_files', os.path.basename(filename))
    if os.path.exists(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    else:
        raise Http404("File does not exist")


@login_required
def restricted_download(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'restricted_download_files', os.path.basename(filename))
    if os.path.exists(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    else:
        raise Http404("File does not exist")


def get_or_create_nodered_user_data(request):
    '''A helper function to get NodeRedUserData  for current user or create new if no data is there'''
    with transaction.atomic():
        try:
            nodered_data, created = NodeRedUserData.objects.get_or_create(
                user=request.user,
                defaults={
                    'container_name': NodeRedUserData.generate_unique_container_name(),
                    'access_token': secrets.token_urlsafe(50),
                },
            )
        except IntegrityError:
            pass
    return nodered_data


@login_required
def nodered_manager(request):
    logger.info("In nodered_manager")
    nodered_data = get_or_create_nodered_user_data(request)

    nodered_container = NoderedContainer(nodered_data)
    nodered_container.determine_state()

    if nodered_container.state != 'none':
        # check port if changed after restart by non-user action
        nodered_container.determine_port()
        if nodered_data.container_port != nodered_container.port:
            update_nodered_data_container_port(nodered_data, nodered_container)
            update_nodered_nginx_conf(nodered_data)

    # Flag to prohibit direct access to redirect pages
    request.session['came_from_nodered_manager'] = True
    # Use container_name on redirected pages
    request.session['container_name'] = nodered_container.name

    if request.session.get('open_nodered_requested'):
        del request.session['open_nodered_requested']
        return redirect('nodered')

    if request.session.get('create_nodered_requested'):
        del request.session['create_nodered_requested']
        nodered_container.create(request.user)
        nodered_container.determine_state()

    if request.session.get('stop_nodered_requested'):
        del request.session['stop_nodered_requested']
        nodered_container.stop()
        nodered_container.determine_state()

    if request.session.get('restart_nodered_requested'):
        del request.session['restart_nodered_requested']
        nodered_container.restart()
        nodered_container.determine_state()

    if nodered_container.state == 'none':
        logger.info("nodered_container.state == 'none'")
        return redirect('nodered-create')

    elif nodered_container.state == 'stopped':
        logger.info("nodered_container.state == 'stopped'")
        return redirect('nodered-restart')

    elif nodered_container.state == 'starting':
        logger.info("nodered_container.state == 'starting'")
        return redirect('nodered-wait')

    elif nodered_container.state == 'running':
        logger.info("nodered_container.state == 'running'")
        if not nodered_container.nodered_data.is_configured:
            nodered_container.configure_nodered(request.user)
        return redirect('nodered-open')

    else:  # e.g. nodered_container.state == "unavailable":
        return redirect('nodered-unavailable')


@login_required
def nodered_create(request):
    if request.method == 'POST':
        request.session['create_nodered_requested'] = True
        return redirect('nodered-manager')

    if not request.session.get('came_from_nodered_manager'):
        return redirect('nodered-manager')
    del request.session['came_from_nodered_manager']

    page_title = 'Node-RED Automation - Connect Devices, Control & Save Data'
    context = {
        'title': page_title,
        'thin_navbar': False,
    }
    return render(request, 'users/nodered_create.html', context)


@login_required
def nodered_restart(request):
    if request.method == 'POST':
        request.session['restart_nodered_requested'] = True
        return redirect('nodered-manager')

    if not request.session.get('came_from_nodered_manager'):
        return redirect('nodered-manager')
    del request.session['came_from_nodered_manager']

    page_title = 'Node-RED Automation - Connect Devices, Control & Save Data'
    context = {
        'title': page_title,
        'thin_navbar': False,
    }
    return render(request, 'users/nodered_restart.html', context)


@login_required
def nodered_wait(request):
    if not request.session.get('came_from_nodered_manager'):
        return redirect('nodered-manager')
    del request.session['came_from_nodered_manager']

    page_title = 'Node-RED Automation - Connect Devices, Control & Save Data'
    context = {
        'title': page_title,
        'thin_navbar': False,
    }
    return render(request, 'users/nodered_wait.html', context)


@login_required
def nodered_open(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'open':  # currently inactive due to inline script calling nodered url
            request.session['open_nodered_requested'] = True

        elif request.POST.get('action') == 'stop':
            request.session['stop_nodered_requested'] = True

        return redirect('nodered-manager')

    if not request.session.get('came_from_nodered_manager'):
        return redirect('nodered-manager')
    del request.session['came_from_nodered_manager']

    mqtt_client_manager = MqttClientManager(request.user)
    nodered_mqtt_client_data = mqtt_client_manager.get_nodered_client()

    page_title = 'Node-RED Automation - Connect Devices, Control & Save Data'
    context = {
        'title': page_title,
        'nodered_mqtt_client_data': nodered_mqtt_client_data,
        'influxdb_token': request.user.influxuserdata.bucket_token,
        'username': request.user.nodereduserdata.username,
        'password': request.user.nodereduserdata.password,
        'thin_navbar': False,
    }
    return render(request, 'users/nodered_open.html', context)


@login_required
def nodered_unavailable(request):
    if request.method == 'POST':
        return redirect('nodered-manager')

    if not request.session.get('came_from_nodered_manager'):
        return redirect('nodered-manager')
    del request.session['came_from_nodered_manager']

    page_title = 'Node-RED Automation - Connect Devices, Control & Save Data'
    context = {
        'title': page_title,
        'thin_navbar': False,
    }
    return render(request, 'users/nodered_unavailable.html', context)


@login_required
def nodered(request):
    # if not request.session.get('came_from_nodered_manager'):
    #     messages.info(request, 'Access Node-RED from here.')
    #     return redirect('nodered-manager')

    # Retrieve container_name from session.
    container_name = request.session.get('container_name')
    if not container_name:
        messages.info(request, 'Reloading Node-RED brings you back here.')
        return redirect('nodered-manager')

    request.session['came_from_nodered_page'] = True

    # Check the current state of the container.
    current_state = NoderedContainer.check_container_state_by_name(container_name)
    # If the container is not running, delete the container_name from session and redirect.
    if current_state != 'running':
        if 'container_name' in request.session:
            del request.session['container_name']
        messages.info(request, 'Node-RED is currently not running.')
        return redirect('nodered-manager')

    # If the container is running, set the flag and do NOT delete container_name.
    request.session['came_from_nodered_page'] = True
    # (Optional) You can leave container_name in the session so that subsequent loads work.
    page_title = 'Node-RED Flows'
    context = {'title': page_title, 'thin_navbar': True}
    return render(request, 'users/nodered.html', context)


@login_required
def nodered_dashboard(request):
    try:
        nodered_data = NodeRedUserData.objects.get(user=request.user)
    except ObjectDoesNotExist:
        return redirect('nodered-manager')
    # TODO: optional write and test instead: request.user.nodereduserdata.container_name
    container_name = nodered_data.container_name

    if not container_name:
        messages.info(request, 'Start Nodered and UI first.')
        return redirect('nodered-manager')

    page_title = 'Node-RED Dashboard'
    context = {
        'container_name': container_name,
        'title': page_title,
        'thin_navbar': True,
    }
    return render(request, 'users/nodered_dashboard.html', context)


def update_nodered_data_container_port(nodered_data, nodered_container):
    ''' A helper function to update nodered container port in NodeRedUserData model '''
    with transaction.atomic():  # protection against race condition
        # Identify and lock the conflicting row
        conflicting_users = (
            NodeRedUserData.objects.select_for_update()
            .exclude(user=nodered_data.user)
            .filter(container_port=nodered_container.port)
        )

        for user_data in conflicting_users:
            user_data.container_port = None  # Set to None and not for example "" to avoid UNIQUE constraint failure
            user_data.save()

        nodered_data.container_port = nodered_container.port
        nodered_data.save()


@login_required
def nodered_flow_examples(request):
    nodered_flow_examples = load_nodered_flow_examples()

    page_title = 'Node-RED Example Flows'
    context = {
        'examples': nodered_flow_examples,
        'title': page_title,
        'thin_navbar': False,
    }
    return render(request, 'users/nodered_flow_examples.html', context)


@login_required
def nodered_status_check(request):
    """Called by JS function checkNoderedStatus() in nodered_wait.html"""
    print('nodered_status_check: Started handling request')
    # Attempt to retrieve the container name from the session.
    container_name = request.session.get('container_name')
    print('after session.get')
    if not container_name:
        print('No container name')
        return redirect('nodered-manager')
    status = NoderedContainer.check_container_state_by_name(container_name)
    print('nodered_status_check: Finished handling request')
    return JsonResponse({'status': status})


@login_required
def access_nodered(request):
    if not request.session.get('came_from_nodered_page'):
        messages.info(request, 'View Node-RED within the website.')
        return redirect('nodered-manager')
    del request.session['came_from_nodered_page']

    nodered_user_data = request.user.nodereduserdata
    container_name = nodered_user_data.container_name
    if container_name is None:
        return redirect("core-home")

    # Create a JWT payload. The token will expire in 300 minutes.
    payload = {
        'username': request.user.username,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=300)
    }

    # Generate the token using the SECRET_KEY stored in nodered_user_data.access_token
    token = jwt.encode(payload, nodered_user_data.access_token, algorithm='HS256')
    logger.info(f"NodeRED-Token: {token}")

    # # Redirect to the Node-RED instance with the token (for basic password auth only)
    # return redirect(f"/nodered/{container_name}")

    # Redirect to Node-RED, appending the token as a query parameter.
    return redirect(f"/nodered/{container_name}?access_token={token}")


@login_required
def manage_data(request):
    """
    Render the form for selecting measurement / tags / time range.
    All data-changing actions (download, delete) are handled by their
    own endpoints and reached via the <form> buttons’ `formaction`.
    """
    if request.method != "GET":
        return redirect("manage-data")        # guard against accidental POSTs

    idm   = InfluxDataManager(request.user)
    form = SelectDataForm(idm.list_measurements())

    return render(
        request,
        "users/manage_data.html",
        {"title": "Manage Measurement Data", "form": form},
    )


@login_required
def delete_data(request):
    """POST endpoint that deletes matching data, then redirects back."""
    if request.method != "POST":
        return redirect("manage-data")

    idm   = InfluxDataManager(request.user)
    form = SelectDataForm(idm.list_measurements(), request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid parameters – please correct the form.")
        return redirect("manage-data")

    ok = idm.delete(
        measurement=form.cleaned_data["measurement"],
        tags=form.cleaned_data["tags"],
        start_iso=to_rfc3339(form.cleaned_data["start_time"]),
        stop_iso=to_rfc3339(form.cleaned_data["end_time"]),
    )
    messages.success(request, "Delete completed." if ok else "Delete failed.")
    return redirect("manage-data")


@login_required
def download_data(request):
    if request.method != "POST":
        return redirect("manage-data")

    idm = InfluxDataManager(request.user)
    form = SelectDataForm(idm.list_measurements(), request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid parameters – please correct the form.")
        return redirect("manage-data")

    measurement = form.cleaned_data["measurement"]
    tags        = form.cleaned_data["tags"]
    start_iso   = to_rfc3339(form.cleaned_data["start_time"])
    stop_iso    = to_rfc3339(form.cleaned_data["end_time"])

    try:
        csv_stream, filename = idm.export_stream(
            measurement=measurement,
            tags=tags,
            start_iso=start_iso,
            stop_iso=stop_iso,
        )
    except ValueError:
        messages.warning(request, "No data matches your query – nothing to download.")
        return redirect("manage-data")

    response = StreamingHttpResponse(csv_stream, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# @login_required
# def download_data(request):
#     """POST endpoint for exporting data as zipped CSV."""
#     if request.method != "POST":
#         return redirect("manage-data")

#     idm = InfluxDataManager(request.user)
#     form = SelectDataForm(idm.list_measurements(), request.POST)
#     if not form.is_valid():
#         messages.error(request, "Invalid parameters – please correct the form.")
#         return redirect("manage-data")

#     try:
#         zip_bytes, zip_name = idm.export(
#             measurement=form.cleaned_data["measurement"],
#             tags=form.cleaned_data["tags"],
#             start_iso=to_rfc3339(form.cleaned_data["start_time"]),
#             stop_iso=to_rfc3339(form.cleaned_data["end_time"]),
#         )
#     except ValueError:
#         messages.warning(request, "No data matches your query – nothing to download.")
#         return redirect("manage-data")

#     response = HttpResponse(zip_bytes, content_type="application/zip")
#     response["Content-Disposition"] = f'attachment; filename="{zip_name}"'
#     return response


@login_required
def visualize(request):
    page_title = 'Visualize Data with Grafana'
    context = {'title': page_title, 'thin_navbar': True}
    return render(request, 'users/visualize.html', context)

@login_required
def get_grafana(request):
    return redirect('/grafana/')

# method for reverse proxy to grafana with auto login and user validation
# https://gist.github.com/feroda/c6b8f37e9389753453ebf7658f0590aa
@method_decorator(login_required, name='dispatch')
class GrafanaProxyView(ProxyView):
    hostname = config.grafana.GRAFANA_HOST
    port = config.grafana.GRAFANA_PORT
    upstream = f'http://{hostname}:{port}/grafana'

    def get_proxy_request_headers(self, request):
        logger.info("In get_proxy_request_headers")
        logger.debug(f'Username: {request.user.username}')
        headers = super(GrafanaProxyView, self).get_proxy_request_headers(request)
        headers['X-WEBAUTH-USER'] = request.user.username
        logger.debug(f'Headers: {headers}')
        return headers

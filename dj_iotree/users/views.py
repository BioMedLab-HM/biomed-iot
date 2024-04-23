import secrets
import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.db import transaction
from .models import NodeRedUserData
from .forms import UserRegisterForm, UserUpdateForm, UserLoginForm, MqttClientForm
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType
from .services.nodered_utils import NoderedContainer, update_nodered_nginx_conf
from .services.code_loader import load_code_examples, load_nodered_flow_examples
import logging


logger = logging.getLogger(__name__)


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                new_user = form.save()
                messages.success(
                    request, "Your account has been created! You are now able to log in"
                )
                return redirect("login")
            except Exception:
                messages.error(
                    request,
                    "An error occurred while creating your account. Please try again.",
                )
    else:
        form = UserRegisterForm()
    return render(request, "users/register.html", {"form": form, "thin_navbar": False})


def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            # The 'username' field can be either a username or an email
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                return redirect("core-home")
    else:
        form = UserLoginForm()

    return render(request, "users/login.html", {"form": form, "thin_navbar": False})


@login_required
def profile(request):
    context = {}
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)

        # p_form: Profile form commented out because contains only image which is currently not used
        # p_form = ProfileUpdateForm(request.POST,
        #                            request.FILES,
        #                            instance=request.user.profile) # FILES = Image
        if u_form.is_valid():  # and p_form.is_valid():
            u_form.save()
            # p_form.save()
            messages.success(request, "Your account has been updated!")
            return redirect("profile")

    else:
        u_form = UserUpdateForm(instance=request.user)
        # p_form = ProfileUpdateForm(instance=request.user.profile)

    page_title = "Your User Profile"
    context = {
        "title": page_title,
        "u_form": u_form,
        # 'p_form': p_form
        "thin_navbar": False,
    }

    return render(request, "users/profile.html", context)


# Prepare a map of common locations to timezone choices you wish to offer.
common_timezones = {
    "Berlin": "Europe/Berlin",
    "London": "Europe/London",
    "New York": "America/New_York",
}
timezones = [("New York", "America/New_York"), ("London", "Europe/London")]


# Experimental function
@login_required
def set_timezone(request):
    if request.method == "POST":
        request.session["django_timezone"] = request.POST["timezone"]
        return redirect("/")
    else:
        # Convert the dictionary to a list of tuples and sort by city name
        timezones_list = sorted(common_timezones.items(), key=lambda x: x[0])
        return render(request, "set_timezone.html", {"timezones": timezones_list, "thin_navbar": False})


@login_required
def devices(request):
    """
    For inexperienced user, MQTT-Clients are called devices since each client is usually linked to a device
    although theoretically, one could use more than one client on one device.
    For technical correctness, the term client is used here.
    """
    print('in "devices view"')
    mqtt_client_manager = MqttClientManager(request.user)

    if request.method == "POST":
        new_device_form = MqttClientForm(request.POST)
        if request.POST.get("action") == "create":
            print('in "create"')
            if new_device_form.is_valid():
                print("form is valid")
                new_textname = new_device_form.cleaned_data["textname"]
                print(f"New Textname from form = {new_textname}")
                mqtt_client_manager.create_client(
                    textname=new_textname, role_type=RoleType.DEVICE.value
                )
                print("after create client")
                messages.success(
                    request, f'Device with name "{new_textname}" successfully created.'
                )
                return redirect("devices")
            else:
                messages.error(request, "Device name is not valid. Max. 30 characters!")
                return redirect("devices")

        elif "modify" in request.POST:
            # Rename client logic
            pass

        elif request.POST.get("device_username"):
            client_username = request.POST.get("device_username")
            print(f"delete device ({client_username}) case")
            success = mqtt_client_manager.delete_client(client_username)
            print(success)
            if success:
                messages.success(
                    request,
                    f'Device with username "{client_username}" successfully deleted.',
                )
                return redirect("devices")
            else:
                messages.error(
                    request, "Failed to delete the device. Please try again."
                )
                return redirect("devices")

    mqtt_meta_data_manager = MqttMetaDataManager(request.user)
    topic_id = mqtt_meta_data_manager.metadata.user_topic_id
    in_topic = f"in/{topic_id}/your/subtopic"
    out_topic = f"out/{topic_id}/your/subtopic"

    new_device_form = MqttClientForm()
    # get list of all device clients
    device_clients_data = mqtt_client_manager.get_device_clients()

    context = {
        "in_topic": in_topic,
        "out_topic": out_topic,
        "topic_id": topic_id,
        "device_clients": device_clients_data,
        "form": new_device_form,
        "title": "Devices",
        "thin_navbar": False,
    }
    return render(request, "users/devices.html", context)


@login_required
def message_and_topic_structure(request):
    
    mqtt_meta_data_manager = MqttMetaDataManager(request.user)
    topic_id = mqtt_meta_data_manager.metadata.user_topic_id
    in_topic = f"in/{topic_id}/your/subtopic"
    out_topic = f"out/{topic_id}/your/subtopic"


    message_example = {
        "temperature": 25.3,
        "timestamp": 1713341175,
    }
    message_example_large = {
        "temperature": 25.3,
        "humidity": 50,
        "sensorX": "text value",
        "...": "...",
        "timestamp": 1713341175,
    }

    message_example_json = json.dumps(message_example, indent=4)
    message_example_large_json = json.dumps(message_example_large, indent=4)
    context = {
        "message_example": message_example_json,
        "message_example_large": message_example_large_json,
        "in_topic": in_topic,
        "out_topic": out_topic,
        "topic_id": topic_id,
        "title": "Message & Topic Structure",
        "thin_navbar": False,
        }
    return render(request, "users/message_and_topic_structure.html", context)


@login_required
def code_examples(request):
    examples_content = load_code_examples()

    page_title = "Code Examples"
    context = {"title": page_title, "examples": examples_content, "thin_navbar": False}
    return render(request, "users/code_examples.html", context)


def get_or_create_nodered_user_data(request):
    with transaction.atomic():
        try:
            nodered_data, created = NodeRedUserData.objects.get_or_create(
                user=request.user,
                defaults={
                    "container_name": NodeRedUserData.generate_unique_container_name(),
                    "access_token": secrets.token_urlsafe(22),
                },
            )
        except IntegrityError:
            pass
    return nodered_data


@login_required
def nodered_manager(request):
    # Get or create NodeRedUserData and get container state
    nodered_data = get_or_create_nodered_user_data(request)

    nodered_container = NoderedContainer(nodered_data)
    nodered_container.determine_state()

    if nodered_container.state != 'none':
        # check port if changed after restart by non-user action
        nodered_container.determine_port()
        if (nodered_data.container_port != nodered_container.port):
            update_nodered_data_container_port(nodered_data, nodered_container)  # TODO: move to NoderedContainer?
            update_nodered_nginx_conf(nodered_data)

    # Flag to prohibit direct access to redirect pages 
    request.session["came_from_nodered_manager"] = True
    # Use container_name on redirected pages
    request.session["container_name"] = nodered_container.name

    if request.session.get("open_nodered_requested"):
        del request.session["open_nodered_requested"]
        return redirect("nodered")

    if request.session.get("create_nodered_requested"):
        del request.session["create_nodered_requested"]
        nodered_container.create()
        nodered_container.determine_state()
    
    if request.session.get("stop_nodered_requested"):
        del request.session["stop_nodered_requested"]
        nodered_container.stop()
        nodered_container.determine_state()

    if request.session.get("restart_nodered_requested"):
        del request.session["restart_nodered_requested"]
        nodered_container.restart()
        nodered_container.determine_state()

    if nodered_container.state == "none":
        return redirect("nodered-create")

    elif nodered_container.state == "stopped":
        return redirect("nodered-restart")

    elif nodered_container.state ==  "starting":
        return redirect("nodered-wait")

    elif nodered_container.state == "running":
        return redirect("nodered-open")

    else: 
        # nodered_container.state == "unavailable":  # TODO: make it nice code
        return redirect("nodered-unavailable")


@login_required
def nodered_create(request):

    if request.method == "POST":
        request.session["create_nodered_requested"] = True
        return redirect("nodered-manager")

    if not request.session.get("came_from_nodered_manager"):
        return redirect("nodered-manager")
    del request.session["came_from_nodered_manager"]

    page_title = "Node-RED Automation - Connect Devices, Control & Save Data"
    context = {
        "title": page_title,
        "thin_navbar": False,
    }
    return render(request, "users/nodered_create.html", context)    


@login_required
def nodered_restart(request):
    
    if request.method == "POST":
        request.session["restart_nodered_requested"] = True
        return redirect("nodered-manager")

    if not request.session.get("came_from_nodered_manager"):
        return redirect("nodered-manager")
    del request.session["came_from_nodered_manager"]
 
    page_title = "Node-RED Automation - Connect Devices, Control & Save Data"
    context = {
        "title": page_title,
        "thin_navbar": False,
    }
    return render(request, "users/nodered_restart.html", context)


@login_required
def nodered_wait(request):
    if not request.session.get("came_from_nodered_manager"):
        return redirect("nodered-manager")
    del request.session["came_from_nodered_manager"]

    page_title = "Node-RED Automation - Connect Devices, Control & Save Data"
    context = {
        "title": page_title,
        "thin_navbar": False,
    }
    return render(request, "users/nodered_wait.html", context)


@login_required
def nodered_open(request):
    if request.method == "POST":
        if request.POST.get("action") == "open":
            request.session["open_nodered_requested"] = True

        elif request.POST.get("action") == "stop":
            request.session["stop_nodered_requested"] = True
        
        return redirect("nodered-manager")

    if not request.session.get("came_from_nodered_manager"):
        return redirect("nodered-manager")
    del request.session["came_from_nodered_manager"]

    mqtt_client_manager = MqttClientManager(request.user)
    nodered_mqtt_client_data = mqtt_client_manager.get_nodered_client()

    page_title = "Node-RED Automation - Connect Devices, Control & Save Data"
    context = {
        "title": page_title,
        "nodered_mqtt_client_data": nodered_mqtt_client_data,
        "thin_navbar": False,
    }
    return render(request, "users/nodered_open.html", context)


@login_required
def nodered_unavailable(request):
    if request.method == "POST":
        return redirect("nodered-manager")

    if not request.session.get("came_from_nodered_manager"):
        return redirect("nodered-manager")
    del request.session["came_from_nodered_manager"]
        
    page_title = "Node-RED Automation - Connect Devices, Control & Save Data"
    context = {
        "title": page_title,
        "thin_navbar": False,
    }
    return render(request, "users/nodered_unavailable.html", context)


@login_required
def nodered(request):
    if not request.session.get("came_from_nodered_manager"):
        messages.info(request, "Access Node-RED from here.")
        return redirect("nodered-manager")

    if not request.session.get("container_name"):
        messages.info(request, "Reloading Node-RED brings you back here.")
        return redirect("nodered-manager")

    container_name = request.session.get("container_name")
    del request.session["container_name"]
    page_title = "Node-RED Flows"
    context = {
        "container_name": container_name, 
        "title": page_title,
        "thin_navbar": True
        }
    return render(request, "users/nodered.html", context)


@login_required
def nodered_dashboard(request):
    page_title = "Node-RED Dashboard"

    try:
        nodered_data = NodeRedUserData.objects.get(user=request.user)
    except ObjectDoesNotExist:
        return redirect("nodered-manager")

    container_name = nodered_data.container_name  # request.session.get("container_name")

    if not container_name:
        messages.info(request, "Start Nodered and UI first.")
        return redirect("nodered-manager")

    context = {
        "container_name": container_name,
        "title": page_title,
        "thin_navbar": True,
        }
    return render(request, "users/nodered_dashboard.html", context)


def update_nodered_data_container_port(nodered_data, nodered_container):
    with transaction.atomic():  # protection against race condition (even though unlikely)
        # Identify and lock the conflicting row -> second protection against race condition (even though unlikely)
        conflicting_users = (
            NodeRedUserData.objects.select_for_update()
            .exclude(user=nodered_data.user)
            .filter(container_port=nodered_container.port)
        )

        for user_data in conflicting_users:
            user_data.container_port = (
                None  # Set to None to avoid UNIQUE constraint failure
            )
            user_data.save()

        # Now, safely update the current user's port
        if nodered_container.port is not None:
            nodered_data.container_port = nodered_container.port
        else:
            # Clear the port in nodered_data if the container is stopped or port is not available
            nodered_data.container_port = ""
        nodered_data.save()


@login_required
def nodered_flow_examples(request):

    examples_content = load_nodered_flow_examples()

    page_title = "Node-RED Example Flows"
    context = {
        "examples": examples_content,
        "title": page_title, 
        "thin_navbar": False,
        }
    return render(request, "users/nodered_flow_examples.html", context)


@login_required
def nodered_status_check(request):
    """Called by JS function checkNoderedStatus() in nodered_manager.html"""
    print("nodered_status_check: Started handling request")
    # Attempt to retrieve the container name from the session.
    container_name = request.session.get("container_name")
    print("after session.get")
    if not container_name:
        print("No container name")
        return redirect("nodered-manager")
    status = NoderedContainer.check_container_state_by_name(container_name)
    print("nodered_status_check: Finished handling request")
    return JsonResponse({"status": status})


@login_required
def data_explorer(request):
    context = {}

    # TODO: Implement

    page_title = "Data Explorer"
    context = {"title": page_title, "thin_navbar": False}
    return render(request, "users/data_explorer.html", context)


@login_required
def grafana(request):
    context = {}

    page_title = "Visualize Data with Grafana"
    context = {"title": page_title, "thin_navbar": True}
    return render(request, "users/grafana.html", context)

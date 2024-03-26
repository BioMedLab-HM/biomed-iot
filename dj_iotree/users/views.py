import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, UserLoginForm, MqttClientForm
from .models import NodeRedUserData, MqttMetaData, MqttClient
import docker
import secrets
from django.http import JsonResponse
from django.db import IntegrityError
import random
import string
from django.db import transaction
from django.conf import settings
from .services.nodered_utils import NoderedContainer, update_nodered_nginx_conf
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType
from .services.code_loader import load_code_examples

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                new_user = form.save()
                messages.success(request, f'Your account has been created! You are now able to log in')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account. Please try again.')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})
    

def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            # The 'username' field can be either a username or an email
            user = authenticate(request, 
                                username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('core-home')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        
        # p_form: Profile form commented out because contains only image which is currently not used
        # p_form = ProfileUpdateForm(request.POST,
        #                            request.FILES,
        #                            instance=request.user.profile) # FILES = Image
        if u_form.is_valid(): # and p_form.is_valid():
            u_form.save()
            # p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        # p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        # 'p_form': p_form
    }

    return render(request, 'users/profile.html', context)


# Prepare a map of common locations to timezone choices you wish to offer.
common_timezones = {
    "Berlin": "Europe/Berlin",
    "London": "Europe/London",
    "New York": "America/New_York",
}
timezones = [('New York', 'America/New_York'), ('London', 'Europe/London')]

# Experimental function
@login_required
def set_timezone(request):
    if request.method == "POST":
        request.session["django_timezone"] = request.POST["timezone"]
        return redirect("/")
    else:
         # Convert the dictionary to a list of tuples and sort by city name
        timezones_list = sorted(common_timezones.items(), key=lambda x: x[0])
        return render(request, "set_timezone.html", {"timezones": timezones_list})


@login_required
def devices(request):
    """ 
    For inexperienced user, MQTT-Clients are called devices since each client is usually linked to a device
    although theoretically, one could use more than one client on one device. 
    For technical correctness, the term client is used here.
    """
    print(f'in "devices view"')
    mqtt_client_manager = MqttClientManager(request.user)

    if request.method == 'POST':
        new_device_form = MqttClientForm(request.POST)
        if request.POST.get('action') == 'create':
            print(f'in "create"')
            if new_device_form.is_valid():
                print(f'form is valid')
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
            # Rename client logic
            pass

        elif request.POST.get('device_username'):
            client_username = request.POST.get('device_username')
            print(f'delete device ({client_username}) case')
            success = mqtt_client_manager.delete_client(client_username)
            print(success)
            if success:
                messages.success(request, f'Device with username "{client_username}" successfully deleted.')
                return redirect('devices')
            else:
                messages.error(request, 'Failed to delete the device. Please try again.')
                return redirect('devices')

    mqtt_meta_data_manager = MqttMetaDataManager(request.user)
    in_topic = f"in/{mqtt_meta_data_manager.metadata.user_topic_id}/#"
    out_topic = f"out/{mqtt_meta_data_manager.metadata.user_topic_id}/#"
    
    new_device_form = MqttClientForm()
    nodered_client_data = mqtt_client_manager.get_nodered_client()  # get Node-RED client credentials + textname
    device_clients_data = mqtt_client_manager.get_device_clients()  # get list of all device clients

    context = {'in_topic': in_topic, 
               'out_topic': out_topic, 
               'nodered_client': nodered_client_data, 
               'device_clients': device_clients_data, 
               'form': new_device_form,
               'title': "Devices"}
    return render(request, 'users/devices.html', context)


@login_required
def code_examples(request):
    examples_content = load_code_examples()

    context = {'examples': examples_content}
    return render(request, 'users/code_examples.html', context)


@login_required
def modify_client(request, client_username):
    client = get_object_or_404(MqttClient, pk=client_username)
    if request.method == 'POST':
        form = MqttClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client-list')
    else:
        form = MqttClientForm(instance=client)
    return render(request, 'users/modify_client.html', {'form': form, 'client': client})

@login_required
def delete_client(request, client_username):
    client = get_object_or_404(MqttClient, pk=client_username)
    if request.method == 'POST':
        # If the 'delete' action is confirmed
        if 'confirm_delete' in request.POST:
            client.delete()
            return redirect('client-list')
        else:
            # If any other action, just redirect back to the client list
            return redirect('client-list')
    else:
        # Render a confirmation page/template
        return render(request, 'users/delete_client.html', {'client': client})
        

@login_required
def nodered_manager(request):
    context = {}
    
    with transaction.atomic():
        try:
            # Attempt to create NodeRedUserData with a unique container name
            nodered_data, created = NodeRedUserData.objects.get_or_create(
                user=request.user,
                defaults={
                    'container_name': NodeRedUserData.generate_unique_container_name(),
                    'access_token': secrets.token_urlsafe(22)
                }
            )
        except IntegrityError:
            # TODO: log error
            pass

        nodered_container = NoderedContainer(nodered_data)
        nodered_container.determine_state()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'run':
            if nodered_container.state == 'running':
                nodered_container.determine_port()
                if nodered_data.container_port != nodered_container.port:
                    update_nodered_data_container_port(nodered_data, nodered_container)
                    update_nodered_nginx_conf(nodered_data)
                
                # Store the container name in the session.
                request.session['container_name'] = nodered_container.name

                return redirect('nodered-embedded')
            else:
                messages.info(request, f'Cannot start Node-RED. Node-RED is {nodered_container.state}.')
        
        elif action == 'create':
            if nodered_container.get_existing_container() is None:
                # Generate completely new data if no container is found
                nodered_data.container_name = NodeRedUserData.generate_unique_container_name()
                nodered_data.access_token = secrets.token_urlsafe(22)
                nodered_data.save()
            
                # Update the NoderedContainer instance with the new nodered_data
                nodered_container.name = nodered_data.container_name
                nodered_container.access_token = nodered_data.access_token
            # TODO: statt den Zeilen oben: if nodered_container.state == 'none':
                # Proceed to create the container
                nodered_container.create()

                # After creation, update the database with the new port
                update_nodered_data_container_port(nodered_data, nodered_container)
                update_nodered_nginx_conf(nodered_data)

                # Store the container name in the session.
                request.session['container_name'] = nodered_container.name
            else:
                messages.info(request, f'Node-RED is already created.')

        elif action == 'restart':
            if nodered_container.state == 'stopped':
                nodered_container.restart()
                update_nodered_data_container_port(nodered_data, nodered_container)
                update_nodered_nginx_conf(nodered_data)
                
                # Store the container name in the session.
                request.session['container_name'] = nodered_container.name
            else:
                messages.info(request, f'Cannot restart Node-RED. Node-RED is {nodered_container.state}.')

        elif action == 'stop':
            if nodered_container.state == 'running':
                update_nodered_data_container_port(nodered_data, nodered_container)
                update_nodered_nginx_conf(nodered_data)
                nodered_container.stop()
            else:
                messages.info(request, f'Cannot stop Node-RED. Node-RED is {nodered_container.state}.')
    
    nodered_container.determine_state()
    context['container_state'] = nodered_container.state

    if nodered_container.state == 'unavailable':
        messages.error(request, f'Unable to start Node-RED. Please try again or contact the site admin.')
        
    return render(request, 'users/nodered_manager.html', context)

def update_nodered_data_container_port(nodered_data, nodered_container):
    if nodered_container.port is not None:
        nodered_data.container_port = nodered_container.port
    else:
        # Clear the port in nodered_data if the container is stopped or port is not available
        nodered_data.container_port = ''
    nodered_data.save()

@login_required
def nodered_embedded(request):
    # Attempt to retrieve the container name from the session.
    container_name = request.session.get('container_name')
    # If no container name in session, redirect to manager view.
    if not container_name:
        messages.info(request, f'Reloading the Node-RED page brings you back to the Node-RED Manager page!')
        return redirect('nodered-manager')

    # Clear the container_name from the session after retrieving it
    # This ensures that direct access to 'nodered_embedded' without first
    # going through 'nodered_manager' will fail the container_name check next time
    del request.session['container_name']

    context = {'container_name': container_name}
    return render(request, 'users/nodered_embedded.html', context)

@login_required
def nodered_status_check(request):
    print('nodered_status_check: Started handling request')
    # Attempt to retrieve the container name from the session.
    container_name = request.session.get('container_name')
    print("after session.get")
    if not container_name:
        print("Not container name")
        return redirect('nodered-manager')
    status = NoderedContainer.check_container_state_by_name(container_name)
    print('nodered_status_check: Finished handling request')
    return JsonResponse({"status": status})


@login_required
def data_explorer(request):
    context = {}
    return render(request, 'users/data_explorer.html', context)

@login_required
def grafana_embedded(request):
    context = {}
    return render(request, 'users/grafana_embedded.html', context)

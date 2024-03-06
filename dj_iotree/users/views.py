import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, UserLoginForm, MQTTClientForm
from .models import NodeRedUserData, MQTTClient
import docker
import secrets
from django.http import JsonResponse
from django.db import IntegrityError
import random
import string
from django.db import transaction
from django.conf import settings
from .services.nodered_utils import update_nginx_nodered_conf


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'Your account has been created! You are now able to log in')
                return redirect('login')
            except Exception as e:
                # TODO?: Log the error for debugging
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
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile) # FILES = Image
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
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
def client_list(request):
    # Filter clients by the current user and pass to the template
    clients = MQTTClient.objects.filter(user=request.user)
    mock_clients = [
        {'client_username': 'user1', 'client_id': '001', 'textname': 'Client 1', 'textdescription': 'Description for Client 1'},
        {'client_username': 'user2', 'client_id': '002', 'textname': 'Client 2', 'textdescription': 'Description for Client 2'},
        {'client_username': 'user3', 'client_id': '003', 'textname': 'Client 3', 'textdescription': 'Description for Client 3'},
    ]
    context = {'clients': mock_clients}
    return render(request, 'users/client_list.html', context)

@login_required
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            # Instead of directly saving the form, save it to a model instance without committing to the database yet
            new_client = form.save(commit=False)
            # Set the user field to the currently logged-in user
            new_client.user = request.user
            # Now save the model instance to the database
            new_client.save()
            return redirect('client-list')
    else:
        form = ClientForm()
    return render(request, 'users/add_client.html', {'form': form})

@login_required
def modify_client(request, client_username):
    client = get_object_or_404(MQTTClient, pk=client_username)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client-list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'users/modify_client.html', {'form': form, 'client': client})

@login_required
def delete_client(request, client_username):
    client = get_object_or_404(MQTTClient, pk=client_username)
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
def nodered_manager(request):  # TODO: Refactor
    user = request.user
    container = None
    container_status = 'no-container'
    container_name = None
    access_token = ''
    
    # hole nodered daten aus DB. Wenn nicht klappt, status 'no-container'
    try: 
        nodered_data = NodeRedUserData.objects.get(user=user)
        container_name = nodered_data.container_name
        access_token = nodered_data.access_token
    ### Except "kein DB Eintrag": 
    except NodeRedUserData.DoesNotExist:
        container_status = 'no-container'
    
    if container_name is not None:
        # hole container wenn nicht None. Wenn nicht klappt, status 'no-container'
        docker_client = docker.from_env()
        try:
            container = docker_client.containers.get(container_name)
            container_status = container.status
        except docker.errors.NotFound:  # If the container does not exist
            container_status = 'no-container'
        # oder redirect errorseite
        except docker.errors.APIError as e:  # various reasons:  invalid parameters, issues with the Docker daemon, network problems, other Docker-related issues
            container_status = 'error'  # will lead to default case that renders nodered-unavailable page

    # Bearbeite POST requests
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            # neuen Container-Name generieren
            allowed_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
            new_name = ''.join(random.choice(allowed_chars) for _ in range(20))  # 20 random upper/lower case letters and digits
            # Access-Token generieren
            new_token = secrets.token_urlsafe(22)
            # Container-Name und Access-Token in DB speichern
            try:
                with transaction.atomic():
                    obj, created = NodeRedUserData.objects.get_or_create(user=user, defaults={
                        'container_name': new_name,
                        # 'container_port': 0,
                        'access_token': new_token
                    })
                    if not created:
                        # Need to update the existing object with the new values.
                        obj.container_name = new_name
                        # obj.container_port = 0
                        obj.access_token = new_token
                        obj.save()  # TODO: Check if name and token already exist
                        update_nginx_nodered_conf()
            except IntegrityError:
                # Handle the IntegrityError case, could log or re-raise with additional context
                pass

            container_volume_name = f'{new_name}-volume'
            docker_client = docker.from_env()
            try:  # TODO: for safety: possibly implement explicit rate limiting for running a new container
                container = docker_client.containers.run(
                    'nodered/node-red',
                    detach=True,
                    restart_policy={"Name": "always"}, 
                    # "always: restart the container automatically unless manually stopped; restarts with Docker deamon or if manually restarted. 
                    # (see: https://docs.docker.com/config/containers/start-containers-automatically/)
                    ports={'1880/tcp': None},
                    volumes={container_volume_name: {'bind': '/data', 'mode': 'rw'}},
                    name=new_name
                )
                # Hier war: container.reload()
                container_status = 'created' # container.status
            except docker.errors.ContainerError:
                pass  # --> hier NodeRed Baustellenseite anzeigen und nicht neu laden (Sackgasse)
            except docker.errors.ImageNotFound:
                pass  # --> hier NodeRed Baustellenseite anzeigen und nicht neu laden (Sackgasse)                                          
            # TODO: settings.js action für Authentication hier
            
        elif action == 'start':
            # start the container
            try:
                container.start()
            except docker.errors.APIError as e:
                container_status = 'error'  # will lead to default case that renders nodered-unavailable page
        
        else:
            container_status = 'error'  # will lead to default case that renders nodered-unavailable page

    # hole container status
    if container_status != 'no-container' and container_status != 'error':
        container_status = container.status

    # Rendere entsprechende Templates je Container Status
    match container_status:  # TODO: evtl container health statt status weil differenzierter
        case 'no-container':
            content_template = 'users/nodered_create_instance.html'
        case 'created':
            content_template = 'users/nodered_waiting.html'
        case 'restarting':  # alternativ "starting" bei Variante mit container health
            content_template = 'users/nodered_waiting.html'
        case 'exited':
            content_template = 'users/nodered_start_instance.html'
        case 'running':  # by container.status
            # Reload to get latest state and port information
            container.reload()
            container_health = container.attrs['State']['Health']['Status']

            # Node-RED is ready
            if container_health == 'healthy':
                content_template = 'users/nodered_embedded.html'
            else:
                # If Node-RED is not yet healthy, check and update the port if necessary
                container_port = container.attrs['NetworkSettings']['Ports']['1880/tcp'][0]['HostPort']
                if nodered_data.container_port != container_port:
                    nodered_data.container_port = container_port
                    nodered_data.save(update_fields=['container_port'])
                    update_nginx_nodered_conf()
                content_template = 'users/nodered_waiting.html'

        case _:
            content_template = 'users/nodered_unavailable.html'

    context = {'content_template': content_template, 'instance_name': container_name, 'status': container_status}
    return render(request, 'users/nodered_manager.html', context)  # TODO: make template name a variable



### Alt ###

@login_required
def check_container_status(request, username):
    client = docker.from_env()
    try:
        container = client.containers.get(username)
        is_running = container.status == 'running'
    except docker.errors.NotFound:
        is_running = False

    return JsonResponse({'is_running': is_running})

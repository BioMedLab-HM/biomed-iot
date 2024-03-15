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
from .services.nodered_utils import update_nodered_nginx_conf  # hier?
from .services.nodered_utils import NoderedContainer


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
        form = MQTTClientForm(request.POST)
        if form.is_valid():
            # Instead of directly saving the form, save it to a model instance without committing to the database yet
            new_client = form.save(commit=False)
            # Set the user field to the currently logged-in user
            new_client.user = request.user
            # Now save the model instance to the database
            new_client.save()
            return redirect('client-list')
    else:
        form = MQTTClientForm()
    return render(request, 'users/add_client.html', {'form': form})

@login_required
def modify_client(request, client_username):
    client = get_object_or_404(MQTTClient, pk=client_username)
    if request.method == 'POST':
        form = MQTTClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client-list')
    else:
        form = MQTTClientForm(instance=client)
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

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'run':
            #request.session['data'] = ...  # make the data available in the next view
            # TODO: Nodered soll nicht bei boot starten wenn vorher gestoppt. Start nur manuell oder bei Fehler
            return redirect('nodered-embedded')  # je nach restart-Dauer eher 'nodered-waiting'
        elif action == 'create':
            nodered_container.create()
            nodered_data.container_port = nodered_container.port
            nodered_data.save()
            update_nodered_nginx_conf(nodered_data)
        elif action == 'restart':
            nodered_container.restart()
            #return redirect('nodered-waiting')  # je nach restart-Dauer eher 'nodered-waiting'
        elif action == 'stop':
            nodered_container.stop()
    
    container_state = nodered_container.determine_state()  # default for new NodeRedUserData: 'no-container'
    context['container_state'] = container_state
    return render(request, 'users/nodered_manager.html', context)

    # get_nodered_data()

    # Wenn POST-request
        # Wenn POST-action "Create"
            # create_nodered(): run new container, save container data to db
            # redirect "nodered-waiting", dort nach warteschleife: redirect "nodered-embedded" 
        # Wenn POST-action "restart"
            # restart_nodered()
            # redirect "nodered-embedded"
        # Wenn POST-action "stop"
            # stop_nodered(): dort auch oben message einblenden
            # redirect "nodered-manager"

    # Wenn keine Daten vorhanden
        # context: Zeige Text "Nodered has not been started yet" und Button "Start (Create) Nodered"
    # wenn daten vorhanden
        # get_container_status()
        # Wenn Status "exited" 
            # context: Zeige Button "Restart Nodered"
        # Sonst wenn Status "Running"
            # context: Zeige Button "Stop Nodered"
    

@login_required
def nodered_manager_ALT_2(request):
    user = request.user
    container = None
    nodered_data = None
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

    context = {}
    return render(request, 'users/nodered_manager.html', context)


@login_required
def nodered_create_instance(request):
    if request.method == 'POST':
        new_name = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        new_token = secrets.token_urlsafe(22)  # TODO: implement authentication in nodered!
        # Update or create container name und access token in DB
        with transaction.atomic():
            nodered_data, created = NodeRedUserData.objects.update_or_create(
                user=request.user, defaults={'container_name': new_name, 'access_token': new_token}
            )
        docker_client = docker.from_env()
        try:  # TODO: for safety: possibly implement explicit rate limiting for running a new container
            container = docker_client.containers.run(
                'nodered/node-red',
                detach=True,
                restart_policy={"Name": "always"},
                # "always: restart the container automatically unless manually stopped; restarts with Docker deamon or if manually restarted.
                # (see: https://docs.docker.com/config/containers/start-containers-automatically/)
                ports={'1880/tcp': None},
                volumes={f'{new_name}-volume': {'bind': '/data', 'mode': 'rw'}},
                name=new_name
            )
            container.reload()
            nodered_data.container_port = container.attrs['NetworkSettings']['Ports']['1880/tcp'][0]['HostPort']
            nodered_data.save()
            update_nodered_nginx_conf(nodered_data)
            return redirect('nodered-waiting')
        except (docker.errors.ContainerError, docker.errors.ImageNotFound):
            return redirect('nodered-unavailable')
        
    return render(request, 'users/nodered_create_instance.html')

##########################
@login_required
def nodered_manager_ALT(request):
    user = request.user
    container = None
    nodered_data = None
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
                    nodered_data, created = NodeRedUserData.objects.get_or_create(user=user, defaults={
                        'container_name': new_name,
                        # 'container_port': 0,
                        'access_token': new_token
                    })
                    if not created:
                        # Need to update the existing object with the new values.
                        nodered_data.container_name = new_name
                        # nodered_data.container_port = 0
                        nodered_data.access_token = new_token
                        nodered_data.save()  # TODO: Check if name and token already exist
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
                nodered_data.container_port = 'blablabla'
                update_nodered_nginx_conf(nodered_data)
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
        case 'starting':  # 'restarting':  # alternativ "starting" bei Variante mit container health
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
                    update_nodered_nginx_conf(nodered_data)
                content_template = 'users/nodered_waiting.html'

        case _:
            content_template = 'users/nodered_unavailable.html'

    context = {'content_template': content_template, 'instance_name': container_name, 'status': container_status}
    return render(request, 'users/nodered_manager.html', context)

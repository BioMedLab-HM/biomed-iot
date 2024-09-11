# User-Simulation-Script

# Creates Users with Node-RED containers
# users request  URL every 10 seconds
# User Count is ingreased after each container startup
# RAM is measured with command 'free -m' after each container startup
# Average RAM with standard deviation + average Request durations with standard deviations are saved to a csv-file 
# Adjust the Values in the Section 'Constants'

import os
import django
import subprocess
import time
import secrets
import threading
import requests
import statistics
import csv
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction

# Suppress only the InsecureRequestWarning from urllib3
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biomed_iot.settings')
django.setup()

from users.services.nodered_utils import NoderedContainer
from users.models import NodeRedUserData

# Constants
CSV_FILE_NAME = 'ram_test_x86.csv'  # Choose a name for the csv-file
INITIAL_COUNT = 1
MAX_COUNT = 37
WARM_UP_DURATION = 60
DETERMINE_STATE_INTERVAL = 3
REQUEST_INTERVAL = 10
MIN_FRACTION_AVAILABLE_RAM = 0.03  # MIN_FRACTION_AVAILABLE_RAM = min. available RAM / total RAM
USER_PASSWORD = "****"  # define a Password for Test purposes
URLS = [
    "URL_1",  # Enter a URL for the Request. Use the same three times for constant request sizes.
    "URL_1",
    "URL_1",
]
MEMORY_MEASUREMENTS_INTERVAL = 0.5
NUMBER_OF_MEMORY_MEASUREMENTS = 20

User = get_user_model()
stop_event = threading.Event()
db_lock = threading.Lock()
request_durations = []
request_lock = threading.Lock()
container_ready_event = threading.Event()  # Event to track container readiness

def get_memory_values():
    """Get current memory values."""
    result = subprocess.run(['free', '--m'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8').splitlines()
    memory_line = output[1].split()
    total = int(memory_line[1])
    used = int(memory_line[2])
    free = int(memory_line[3])
    shared = int(memory_line[4])
    buff_cache = int(memory_line[5])
    available = int(memory_line[6])
    return total, used, free, shared, buff_cache, available

def measure_request_duration(url):
    """Measure HTTP request duration."""
    try:
        start_time = time.perf_counter()
        response = requests.get(url, verify=False)
        duration = time.perf_counter() - start_time
        with request_lock:
            request_durations.append(duration)
        print(f"Request to {url} took {duration:.4f} seconds, Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error requesting {url}: {e}")

def perform_warmup():
    """Perform warm-up phase by sending requests for a duration."""
    print(f"Warming up the server for {WARM_UP_DURATION} seconds...")
    warmup_end_time = time.time() + WARM_UP_DURATION

    while time.time() < warmup_end_time:
        for url in URLS:
            try:
                requests.get(url, verify=False)
                print(f"Warm-up request to {url} completed.")
            except requests.exceptions.RequestException as e:
                print(f"Error during warm-up requesting {url}: {e}")
            time.sleep(REQUEST_INTERVAL)

def take_measurements():
    """Take memory measurements and calculate averages and standard deviations."""
    measurements = []
    start_time = time.perf_counter()

    for _ in range(NUMBER_OF_MEMORY_MEASUREMENTS):
        if stop_event.is_set():
            return None, None
        measurements.append(get_memory_values())
        time.sleep(MEMORY_MEASUREMENTS_INTERVAL)

    measurement_duration = round(time.perf_counter() - start_time, 4)

    # Calculate averages and standard deviations in correct order
    total_avg, used_avg, free_avg, shared_avg, buff_cache_avg, available_avg = [
        round(sum(x) / NUMBER_OF_MEMORY_MEASUREMENTS) for x in zip(*measurements)
    ]
    total_std_dev, used_std_dev, free_std_dev, shared_std_dev, buff_cache_std_dev, available_std_dev = [
        round(statistics.stdev(x), 2) for x in zip(*measurements)
    ]

    with request_lock:
        num_requests = len(request_durations)
        if request_durations:
            avg_request_duration = round(sum(request_durations) / num_requests, 4)
            std_dev_request_duration = round(statistics.stdev(request_durations), 4) if num_requests > 1 else 0.0
        else:
            avg_request_duration = 0
            std_dev_request_duration = 0

        # Clear request durations after measurement
        request_durations.clear()

    # Combine the results in the correct order for the CSV
    combined_results = [
        total_avg, total_std_dev,
        used_avg, used_std_dev,
        free_avg, free_std_dev,
        shared_avg, shared_std_dev,
        buff_cache_avg, buff_cache_std_dev,
        available_avg, available_std_dev,
        avg_request_duration, std_dev_request_duration
    ]

    return combined_results

def create_and_login_user(count):
    """Register and log in a user in Django."""
    username = f"{str(count).zfill(2)}"
    email = f"{str(count).zfill(2)}@example.com"
    password = USER_PASSWORD

    with db_lock:
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            print(f"User {username} registered.")
        except IntegrityError:
            user = User.objects.get(username=username)

    user = authenticate(username=email, password=password)
    if user is not None:
        print(f"User {username} logged in.")
        return user
    else:
        print(f"Failed to log in user {username}.")
        return None

def get_or_create_nodered_user_data(user):
    """Get or create NodeRedUserData for the given user."""
    with db_lock:
        with transaction.atomic():
            try:
                nodered_data, created = NodeRedUserData.objects.get_or_create(
                    user=user,
                    defaults={'container_name': f"container_{user.username}", 'access_token': secrets.token_urlsafe(50)},
                )
            except IntegrityError:
                nodered_data = NodeRedUserData.objects.get(user=user)
    return nodered_data

def create_nodered_container(user, count):
    """Initiate the creation of a Node-RED container for the user."""
    nodered_data = get_or_create_nodered_user_data(user)
    container_name = f"container_{user.username}"
    nodered_data.container_name = container_name
    nodered_data.save()

    nodered_container = NoderedContainer(nodered_data)
    
    # Start timing the container creation
    container_start_time = time.perf_counter()
    nodered_container.create(user)
    print(f"Container creation initiated for {container_name}.")
    
    return nodered_container, container_start_time  # Return the start time

def wait_for_container_running(nodered_container, container_start_time, results_dict, result_lock):
    """Wait for the container to reach the 'running' state."""
    while nodered_container.state != 'running' and not stop_event.is_set():
        print(f"Waiting for container {nodered_container.name} to be fully running...")
        time.sleep(DETERMINE_STATE_INTERVAL)
        nodered_container.determine_state()

    if nodered_container.state == 'running':
        # Calculate the startup time
        container_startup_duration = round(time.perf_counter() - container_start_time, 4)
        print(f"Container {nodered_container.name} is fully running. Startup time: {container_startup_duration:.4f} seconds.")
        
        # Store the result safely in the shared dictionary
        with result_lock:
            results_dict['container_startup_duration'] = container_startup_duration
        
        container_ready_event.set()  # Signal that the container is ready
    else:
        print(f"Container {nodered_container.name} failed to start.")



def user_simulation(user, count, results_dict, result_lock):
    """Simulate user behavior: create containers and make HTTP requests."""
    nodered_container, container_start_time = create_nodered_container(user, count)  # Initiate container creation with timing

    # Signal main thread that the container creation has started
    container_ready_event.clear()

    # Start waiting for the container to run in a separate thread and measure the startup time
    wait_thread = threading.Thread(target=wait_for_container_running, args=(nodered_container, container_start_time, results_dict, result_lock))
    wait_thread.start()

    # Immediately start making HTTP requests without waiting for the container to be "running"
    while not stop_event.is_set():
        for url in URLS:
            measure_request_duration(url)
            time.sleep(REQUEST_INTERVAL)


def main():
    print("Node-RED container + RequestsRAM usage test started")

    # Warm-up phase
    perform_warmup()

    # Initial RAM and request duration measurement
    combined_results = take_measurements()
    if combined_results is None:
        print("Measurement interrupted due to low memory. Exiting.")
        return

    # Create the initial CSV file and save the initial measurements
    with open(CSV_FILE_NAME, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        header = [
            'count',
            'total_avg', 'total_std_dev',
            'used_avg', 'used_std_dev',
            'free_avg', 'free_std_dev',
            'shared_avg', 'shared_std_dev',
            'buff/cache_avg', 'buff/cache_std_dev',
            'available_avg', 'available_std_dev',
            'avg_request_duration', 'std_dev_request_duration',
            'container_startup_duration'
        ]
        csv_writer.writerow(header)
        csv_writer.writerow([0] + combined_results + [0])  # Initial entry with startup time = 0

    count = INITIAL_COUNT
    user = create_and_login_user(count)

    if not user:
        print("Failed to create and log in the first user.")
        return

    # Shared data structure and lock for communicating results
    results_dict = {}
    result_lock = threading.Lock()

    while not stop_event.is_set():
        user_thread = threading.Thread(target=user_simulation, args=(user, count, results_dict, result_lock))
        user_thread.start()

        # Wait for the container to be fully running
        container_ready_event.wait()

        # Retrieve the startup time from the dictionary
        with result_lock:
            container_startup_duration = results_dict.get('container_startup_duration', 0)

        combined_results = take_measurements()
        if combined_results is None:
            print("Measurement interrupted due to low memory. Exiting.")
            break

        with open(CSV_FILE_NAME, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([count] + combined_results + [container_startup_duration])

        # Reset the event for the next iteration
        container_ready_event.clear()

        total, used, free, shared, buff_cache, available = get_memory_values()
        if count == MAX_COUNT:  # available / total <= MIN_FRACTION_AVAILABLE_RAM:
            print(f"Reached limit with {count} users and {MIN_FRACTION_AVAILABLE_RAM * 100}% available RAM ")
            stop_event.set()
            break

        count += 1
        user = create_and_login_user(count)
        if not user:
            break



if __name__ == "__main__":
    # Record the start time of the script
    script_start_time = time.time()

    # Run the main function
    main()

    # Record the end time of the script
    script_end_time = time.time()

    # Calculate and display the total execution time
    total_execution_time = script_end_time - script_start_time
    print(f"\nTotal execution time of the script: {total_execution_time:.2f} seconds\n")

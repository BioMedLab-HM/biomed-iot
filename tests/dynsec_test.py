# Test for correct implementation of the mosquitto_dynsec module

import sys
from pathlib import Path

# Current script directory: iotree42/tests
script_dir = Path(__file__).resolve().parent

# Target package directory: iotree42/dj_iotree/users/services
# Navigate up to iotree42 then into dj_iotree/users/services
package_dir = script_dir.parent / 'dj_iotree' / 'users' / 'services'

# Append the directory containing the mosquitto_dynsec module to sys.path
sys.path.append(str(package_dir))

# Now you can import your module
import json
# import paho.mqtt.client as mqtt
from mosquitto_dynsec import MosquittoDynSec
from queue import Queue
import time


def handle_response(response):
    #print("Received response:", response)
    pass

def main():
    username = "admin"
    password = "testpass"  # TODO: neues PW festlegen
    host="localhost"
    port=1883

    response_queue = Queue()
    dynsec = MosquittoDynSec(username, password, host, port, response_queue=response_queue)

    # Test function here
    paho_result = dynsec.get_default_acl_access()

    # Print sending results from paho
    print(f'Paho result code: {paho_result}\n')

    # Print the response from Mosquitto Dynamic Security Plugin
    response = response_queue.get()  # Blocks until a response is available
    print("Received response:", response)

    time.sleep(2)

if __name__ == '__main__':
    main()
    

# Sucessfully tested:
    # dynsec.set_default_acl_access(False, False, False, False)
    # 
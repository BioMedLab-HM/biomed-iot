# Test for correct implementation of the mosquitto_dynsec module

import sys
from pathlib import Path
import time
import tomllib
import json

# Current script directory: iotree42/tests
script_dir = Path(__file__).resolve().parent

# Target package directory: iotree42/dj_iotree/users/services
# Navigate up to iotree42 then into dj_iotree/users/services
package_dir = script_dir.parent / 'dj_iotree' / 'users' / 'services'

# Add the project directory to the Python path
sys.path.append(str(package_dir))

from mosquitto_dynsec import MosquittoDynSec

with open("/etc/iotree/config.toml", "rb") as f:
    config = tomllib.load(f)

username = config['mosquitto']['DYNSEC_USER']
password = config['mosquitto']['DYNSEC_PASSWORD']

dynsec = MosquittoDynSec(username, password)

start_time = time.time()

# Dyn. Sec. Command to test 
success, response = dynsec.set_default_acl_access(False, False, False, False)

end_time = time.time()
duration = end_time - start_time

print(f"Function execution took: {duration} seconds.")
print(f"Success: {success}\nResponse: {response}")

# ruff: noqa: E402
import sys
import threading
import time
from pathlib import Path
import tomllib

# Current script directory: biomed-iot/tests
script_dir = Path(__file__).resolve().parent

# Target package directory: biomed-iot/biomed_iot/users/services
# Navigate up to biomed-iot then into biomed_iot/users/services
package_dir = script_dir.parent / 'biomed_iot' / 'users' / 'services'

# Add the project directory to the Python path
sys.path.append(str(package_dir))

from mosquitto_dynsec import MosquittoDynSec

with open('/etc/biomed-iot/config.toml', 'rb') as f:
	config = tomllib.load(f)

admin_username = config['mosquitto']['DYNSEC_ADMIN_USER']
admin_password = config['mosquitto']['DYNSEC_ADMIN_PW']

# Extract list of actual usernames from /var/lib/mosquitto/dynamic-security.json
usernames = [
	'2zvBsAiwqQKQebScq7At',
	'4xRnvhohqMfhGRGZM1bh',
	'8X2g9ZhnpTmFJ6tWIQcC',
	'ALlZgosr2GGTQ5J5nlYK',
	'CC6oxyz3lw5UQIeG9TtY',  # 5
	#     "EnIw9qj29yCcl1hoIOCI",
	#     "GeiaYHuhu7jV2Ws4IeAy",
	#     "I8qWG6SMi23id5vbJYGb",
	#     "IYHD5YdgvioVCqkx2cdq",
	#     "N4jtGOpv3Oba8877dOza", # 10
	#     "XXLkaI3oUDMKpZV8yomn",
	#     "Y696XjN1Ujp5UAYujsqZ",
	#     "YM05Qh8ogV1ZqcfV5FmL",
	#     "b4kaebjtcn47jOxQI3UF",
	#     "cupzEm1A8UtrrGLN2gV9", # 15
	#     "gEbe3UTCZGZgaZzi5LPs",
	#     "i92F7eOHIK62nR13GdSk",
	#     "jclga904BxqiWXPkGp1Y",
	#     "krEL3hTYvcgecluSf1mP",
	#     "mqmjDnmEiHVZU7ralbDt", # 20
	#     "qG4nTGN1tC8ESb1Dzgij",
	#     "shY20WIZPx7fVgppTjTL",
	#     "voSE1MxmpTHrn8isOHsH",
	#     "x7Tlb3ZId5RhWyJM6StK",
]  # 24 usernames in total


success_count = 0  # Counter for successful dynsec calls
total_calls = 0  # Counter for total dynsec calls
lock = threading.Lock()  # A lock to manage concurrent access to counters


class ClientGetterThread(threading.Thread):
	def __init__(self, username, stop_event):
		super().__init__()
		self.username = username
		self.stop_event = stop_event

	def run(self):
		global success_count, total_calls
		dynsec_credentials = (admin_username, admin_password)
		while not self.stop_event.is_set():
			try:
				dynsec = MosquittoDynSec(*dynsec_credentials)
				# Assuming get_client returns (success, response)
				success, response, send_code = dynsec.get_client(self.username)
				with lock:  # Ensure thread-safe increment of counters
					if success:
						success_count += 1
					total_calls += 1
				print(
					f'Thread for {self.username}: \nSuccess: {success},  \nResponse: {response},  \nCode: {send_code}\n\n'
				)
			finally:
				dynsec.disconnect()
			time.sleep(0.1)


def start_simulation(usernames):
	threads = []
	stop_events = []

	try:
		for username in usernames:
			stop_event = threading.Event()
			thread = ClientGetterThread(username, stop_event)
			threads.append(thread)
			stop_events.append(stop_event)
			thread.start()

		# Let the simulation run for some time (e.g., 30 seconds)
		time.sleep(10)
	finally:
		# Stop all threads
		for stop_event in stop_events:
			stop_event.set()

		for thread in threads:
			thread.join()

	# Calculate and print success rate
	if total_calls > 0:
		success_rate = (success_count / total_calls) * 100
		print(f'Total successes: {success_count}/{total_calls}, Success rate: {success_rate:.2f}%')
	else:
		print('No calls were made.')


if __name__ == '__main__':
	start_simulation(usernames)

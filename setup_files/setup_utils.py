import os
import subprocess


# Get the directory where this script is located
  # base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(setup_dir, "setup_files", "logs")

# Ensure the logs directory exists
os.makedirs(log_dir, exist_ok=True)

def log(message, log_file_name='main.log'):
        log_file_path = os.path.join(log_dir, log_file_name)
        with open(log_file_path, 'a') as file:
            file.write(message + '\n')

def run_bash(command, log_file_name='main.log'):
    """Execute a Bash command and log its output to a specified log file."""
    try:
        subprocess.run(command, shell=True, check=True, stdout=log_file, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        log(f"Error executing command: {e.cmd}\nOutput:\n{e.output}\n")
        raise

def get_linux_user():
    linux_user = os.getenv("SUDO_USER", default="")
    return linux_user

def get_setup_dir():
    setup_dir = f"/home/{linux_user}/iotree42"
    return setup_dir

def get_random_string(string_length):
    """
    Define the characters to include in the random string
    with no symbols for easy copy paste
    """
    characters = string.ascii_letters + string.digits  
    # Generate a random string of the specified length
    rand_str = ''.join(random.choice(characters) for _ in range(string_length))
    return rand_str

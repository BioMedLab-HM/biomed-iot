import os
import subprocess

# Define the service file path
file_path = '/lib/systemd/system/mosquitto.service'

# The lines we want to ensure exist in the [Unit] section
lines_to_add = [
    "After=docker.service network.target",
    "Wants=network.target",
    "Requires=docker.service"
]

def modify_service_file(file_path, lines_to_add):
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist")

    # Read the current content of the service file
    with open(file_path, 'r') as file:
        content = file.readlines()

    # Initialize flags
    in_unit_section = False
    updated_content = []
    after_modified = False
    wants_modified = False
    requires_modified = False

    # Process the file line by line
    for line in content:
        stripped_line = line.strip()

        # Check if we are in the [Unit] section
        if stripped_line == '[Unit]':
            in_unit_section = True
            updated_content.append(line)
            continue

        # If we're in the [Unit] section, modify the relevant lines
        if in_unit_section:
            if stripped_line.startswith('After='):
                # Replace the 'After' line
                updated_content.append(f"After=docker.service network.target\n")
                after_modified = True
            elif stripped_line.startswith('Wants='):
                # Replace the 'Wants' line
                updated_content.append(f"Wants=network.target\n")
                wants_modified = True
            elif stripped_line.startswith('Requires='):
                # Replace the 'Requires' line
                updated_content.append(f"Requires=docker.service\n")
                requires_modified = True
            else:
                updated_content.append(line)

            # Exit the [Unit] section after it's processed
            if stripped_line == '':
                in_unit_section = False

        else:
            updated_content.append(line)

    # If the lines were not found, add them to the [Unit] section
    if not after_modified:
        updated_content.insert(updated_content.index('[Unit]\n') + 1, f"After=docker.service network.target\n")
    if not wants_modified:
        updated_content.insert(updated_content.index('[Unit]\n') + 2, f"Wants=network.target\n")
    if not requires_modified:
        updated_content.insert(updated_content.index('[Unit]\n') + 3, f"Requires=docker.service\n")

    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.writelines(updated_content)

    print(f"Updated {file_path} successfully.")

def reload_systemd():
    try:
        # Reload systemd to apply the changes
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        print("Systemd daemon reloaded.")
    except subprocess.CalledProcessError as e:
        print(f"Error reloading systemd: {e}")
        raise

# Call the function to modify the service file and reload systemd
# IN OTHER SCRIPT
# try:
#     modify_service_file(service_file_path, lines_to_add)
#     reload_systemd()
# except Exception as e:
#     print(f"An error occurred: {e}")

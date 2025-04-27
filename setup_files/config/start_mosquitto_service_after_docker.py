import subprocess
from pathlib import Path

# Defaults for the service modification
SERVICE_FILE = Path('/lib/systemd/system/mosquitto.service')
DIRECTIVES = {
    'After': 'docker.service network.target',
    'Wants': 'network.target',
    'Requires': 'docker.service',
}


def _find_section_bounds(lines, section_name):
    """
    Find the start and end indices of a systemd section (e.g. 'Unit').
    Returns a tuple (start_index, end_index).
    """
    header = f'[{section_name}]'
    start = end = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i
            continue
        if start is not None and line.startswith('[') and i > start:
            end = i
            break
    return start, end or len(lines)


def _update_directives(lines, directives):
    """
    Given the lines inside a section (excluding the header), ensure each directive is present
    with the desired value. Existing ones are replaced; missing ones are added at the top.
    """
    seen = set()
    output = []

    # Replace existing directives
    for line in lines:
        stripped = line.strip()
        key, *_ = stripped.split('=', 1)
        if key in directives:
            output.append(f"{key}={directives[key]}\n")
            seen.add(key)
        else:
            output.append(line)

    # Prepend any missing directives
    missing = [f"{k}={v}\n" for k, v in directives.items() if k not in seen]
    return missing + output


def modify_service_file(
    file_path: Path = SERVICE_FILE,
    directives: dict = DIRECTIVES,
):
    """
    Ensure the mosquitto.service [Unit] section contains the correct directives.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")

    content = file_path.read_text().splitlines(keepends=True)
    start, end = _find_section_bounds(content, 'Unit')
    if start is None:
        raise ValueError("[Unit] section not found in service file")

    # Build updated content
    header = content[: start + 1]
    unit_body = content[start + 1 : end]
    trailer = content[end:]

    new_body = _update_directives(unit_body, directives)
    file_path.write_text(''.join(header + new_body + trailer))
    print(f"Updated {file_path} successfully.")


def reload_systemd():
    """
    Reload systemd daemon to pick up service changes.
    """
    try:
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        print("Systemd daemon reloaded.")
    except subprocess.CalledProcessError as e:
        print(f"Error reloading systemd: {e}")
        raise


# import os
# import subprocess

# # Define the service file path
# file_path = '/lib/systemd/system/mosquitto.service'

# def modify_service_file():
#     # Check if the file exists
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"{file_path} does not exist")

#     # Read the current content of the service file
#     with open(file_path, 'r') as file:
#         content = file.readlines()

#     # Initialize flags
#     in_unit_section = False
#     updated_content = []
#     after_modified = False
#     wants_modified = False
#     requires_modified = False

#     # Process the file line by line
#     for line in content:
#         stripped_line = line.strip()

#         # Check if we are in the [Unit] section
#         if stripped_line == '[Unit]':
#             in_unit_section = True
#             updated_content.append(line)
#             continue

#         # If we're in the [Unit] section, modify the relevant lines
#         if in_unit_section:
#             if stripped_line.startswith('After='):
#                 # Replace the 'After' line
#                 updated_content.append(f"After=docker.service network.target\n")
#                 after_modified = True
#             elif stripped_line.startswith('Wants='):
#                 # Replace the 'Wants' line
#                 updated_content.append(f"Wants=network.target\n")
#                 wants_modified = True
#             elif stripped_line.startswith('Requires='):
#                 # Replace the 'Requires' line
#                 updated_content.append(f"Requires=docker.service\n")
#                 requires_modified = True
#             else:
#                 updated_content.append(line)

#             # Exit the [Unit] section after it's processed
#             if stripped_line == '':
#                 in_unit_section = False

#         else:
#             updated_content.append(line)

#     # If the lines were not found, add them to the [Unit] section
#     if not after_modified:
#         updated_content.insert(updated_content.index('[Unit]\n') + 1, f"After=docker.service network.target\n")
#     if not wants_modified:
#         updated_content.insert(updated_content.index('[Unit]\n') + 2, f"Wants=network.target\n")
#     if not requires_modified:
#         updated_content.insert(updated_content.index('[Unit]\n') + 3, f"Requires=docker.service\n")

#     # Write the updated content back to the file
#     with open(file_path, 'w') as file:
#         file.writelines(updated_content)

#     print(f"Updated {file_path} successfully.")

# def reload_systemd():
#     try:
#         # Reload systemd to apply the changes
#         subprocess.run(['systemctl', 'daemon-reload'], check=True)
#         print("Systemd daemon reloaded.")
#     except subprocess.CalledProcessError as e:
#         print(f"Error reloading systemd: {e}")
#         raise

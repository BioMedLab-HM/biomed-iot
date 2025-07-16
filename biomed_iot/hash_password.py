# Hash a password using Django's default password hasher.
# This script is useful for creating hashed passwords for use in Django's
# admin interface for creating new users without self-registration.
# Usage:
#   cd ~/biomed-iot/biomed_iot
#   source venv/bin/activate
#   python hash_password.py
# Note: This script requires Django to be installed and configured.

import os
import sys
import django
from getpass import getpass
from django.contrib.auth.hashers import make_password

def main():
    # point at your settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biomed_iot.settings')
    # initialize Django
    django.setup()

    # read password (no echo)
    password = getpass('Password: ')
    if not password:
        sys.exit('Error: no password entered.')

    # hash it using Django's default hasher (PBKDF2 by default)
    hashed = make_password(password)
    print('\nYour hashed password is:\n    {}'.format(hashed))

if __name__ == '__main__':
    main()

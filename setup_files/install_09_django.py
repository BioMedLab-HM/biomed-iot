from .setup_utils import get_setup_dir, get_linux_user, run_bash, log, get_random_string

DJANGO_INSTALL_LOG_FILE_NAME = "install_09_django.log"


def install_django(django_admin_email, django_admin_name, django_admin_pass, auto_generate_django_admin_credentials):
    """
    Setup Django environment, including virtual environment creation, 
    dependencies installation, migrations, and superuser creation.
    """
    linux_user = get_linux_user()
    setup_dir = get_setup_dir()

    django_secret = get_random_string(50, incl_symbols=True)
    if auto_generate_django_admin_credentials:
        django_admin_name = "admin-" + get_random_string(4)
        django_admin_pass = (get_random_string(4) + "-" 
                            + get_random_string(4) + "-" 
                            + get_random_string(4))



    # Create the Django virtual environment
    output = run_bash(f"runuser -u {linux_user} -- python3 -m venv {setup_dir}/dj_iotree/dj_venv")
    log(output, DJANGO_INSTALL_LOG_FILE_NAME)

    # Install requirements (written in one command to keep venv active)
    requirements_command = (
        f"runuser -u {linux_user} -- bash -c 'source {setup_dir}/dj_iotree/dj_venv/bin/activate && "
        f"pip install -r {setup_dir}/dj_iotree/requirements.txt && "
        f"{setup_dir}/dj_iotree/dj_venv/bin/python {setup_dir}/dj_iotree/manage.py makemigrations && "
        f"{setup_dir}/dj_iotree/dj_venv/bin/python {setup_dir}/dj_iotree/manage.py migrate && "
        f"deactivate'"
    )
    requirements_install_output = run_bash(requirements_command)
    log(requirements_install_output, DJANGO_INSTALL_LOG_FILE_NAME)

    # Create Django superuser
    django_superuser_command = (
        f"echo \"from users.models import CustomUser; "
        f"CustomUser.objects.create_superuser('{django_admin_name}', '{django_admin_email}', '{django_admin_pass}')\" | "
        f"runuser -u {linux_user} -- {setup_dir}/dj_iotree/dj_venv/bin/python {setup_dir}/dj_iotree/manage.py shell"
    )
    run_bash(django_superuser_command)
    msg = "Django Superuser created"
    print(msg)
    log(msg, DJANGO_INSTALL_LOG_FILE_NAME)

    # Prepare static files directory and deploy static files
    # see: https://docs.djangoproject.com/en/5.0/howto/static-files/ 
    # and https://forum.djangoproject.com/t/django-and-nginx-permission-issue-on-ubuntu/26804
    out = run_bash("mkdir -p /var/www/iotree42/static/")
    log(out, DJANGO_INSTALL_LOG_FILE_NAME)
    out = run_bash("chown www-data:www-data /var/www/iotree42/static/")
    log(out, DJANGO_INSTALL_LOG_FILE_NAME)
    out = run_bash(f"usermod -aG www-data {linux_user}")
    log(out, DJANGO_INSTALL_LOG_FILE_NAME)
    out = run_bash("chmod 2775 /var/www/iotree42/static/")
    log(out, DJANGO_INSTALL_LOG_FILE_NAME)


    # Collect static files
    collect_static_command = (
        f"runuser -u www-data -- bash -c 'source {setup_dir}/dj_iotree/dj_venv/bin/activate && "
        f"{setup_dir}/dj_iotree/dj_venv/bin/python {setup_dir}/dj_iotree/manage.py collectstatic --noinput && "
        f"deactivate'"
    )
    collectstatic_output = run_bash(collect_static_command)
    log(collectstatic_output, DJANGO_INSTALL_LOG_FILE_NAME)
    
    config_data = {
        "DJANGO_SECRET_KEY": django_secret,
        "DJANGO_ADMIN_EMAIL": django_admin_email,
        "DJANGO_ADMIN_NAME": django_admin_name,
        "DJANGO_ADMIN_PASS": django_admin_pass,
    }

    log("Django setup done", DJANGO_INSTALL_LOG_FILE_NAME)
    return config_data

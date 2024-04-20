from .setup_utils import run_bash, log, get_random_string


POSTGRESS_INSTALL_LOG_FILE_NAME = "install_08_postgres.log"


def install_postgres():
    """
    install postgreSQL (https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-debian-11
    and https://forum.mattermost.com/t/pq-permission-denied-for-schema-public/14273)
    """

    db_name = "iotree_db_" + get_random_string(10)
    username = "iotree_user_" + get_random_string(10)
    password = get_random_string(50)

    output = run_bash("apt install -y libpq-dev postgresql postgresql-contrib")
    log(output, POSTGRESS_INSTALL_LOG_FILE_NAME)

    setup_commands = [
        f'sudo -u postgres psql -c "CREATE DATABASE {db_name};"',
        f"sudo -u postgres psql -c \"CREATE USER {username} WITH PASSWORD '{password}';\"",
        f"sudo -u postgres psql -c \"ALTER ROLE {username} SET client_encoding TO 'utf8';\"",
        f"sudo -u postgres psql -c \"ALTER ROLE {username} SET default_transaction_isolation TO 'read committed';\"",
        f"sudo -u postgres psql -c \"ALTER ROLE {username} SET timezone TO 'UTC';\"",
        f'sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username};"',
        f'sudo -u postgres psql -c "ALTER DATABASE {db_name} OWNER TO {username};"',
        f'sudo -u postgres psql -c "GRANT USAGE, CREATE ON SCHEMA public TO {username};"',
    ]

    for command in setup_commands:
        run_bash(command, show_output=False)
        msg = "Done: sudo -u postgres psql -c '...'"
        print(msg)
        log(msg, POSTGRESS_INSTALL_LOG_FILE_NAME)

    config_data = {
        "POSTGRES_NAME": db_name,
        "POSTGRES_USER": username,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "5432",
    }

    log(
        "postgress installation and setup commands executed",
        POSTGRESS_INSTALL_LOG_FILE_NAME,
    )
    return config_data

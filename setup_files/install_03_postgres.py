from .setup_utils import run_bash, get_random_string

LOG_03 = "install_postgres.log"
postgres_pass = get_random_string(50)

def install_postgres():
    """
    install postgreSQL (https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-debian-11
    and https://forum.mattermost.com/t/pq-permission-denied-for-schema-public/14273)
    """
    commands = [
        "apt install -y libpq-dev postgresql postgresql-contrib",
        'sudo -u postgres psql -c "CREATE DATABASE dj_iotree_db;"',
        
        f'sudo -u postgres psql -c "CREATE USER dj_iotree_user WITH PASSWORD \'{postgres_pass}\';"',
        'sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET client_encoding TO \'utf8\';"',
        'sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET default_transaction_isolation TO \'read committed\';"',
        'sudo -u postgres psql -c "ALTER ROLE dj_iotree_user SET timezone TO \'UTC\';"',
        'sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dj_iotree_db TO dj_iotree_user;"',
        'sudo -u postgres psql -c "ALTER DATABASE dj_iotree_db OWNER TO dj_iotree_user;"',
        'sudo -u postgres psql -c "GRANT USAGE, CREATE ON SCHEMA public TO dj_iotree_user;"'
    ]

    for command in commands:
        run_bash(command, LOG_03)


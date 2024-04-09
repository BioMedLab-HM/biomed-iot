def write_config_file(values, destination):
    """
    Substitutes variables in content with values (dict) and writes the content
    into the destination (/etc/iotree/config.toml).
    TODO: Vervollständigen!
    """
    content = """
        [mail]
        RES_EMAIL_HOST = "{RES_EMAIL_HOST}"
        RES_EMAIL_PORT = 587
        RES_EMAIL_ADDRESS = "{RES_EMAIL_ADDRESS}"
        RES_EMAIL_PASS = "{RES_EMAIL_PASS}"

        [django]
        DJANGO_SECRET_KEY = "{DJANGO_SECRET_KEY}"
        DJANGO_ADMIN_MAIL = "{DJANGO_ADMIN_MAIL}"

        [host]
        IP = "{IP}"
        DOMAIN = "{DOMAIN}"

        [postgres]
        POSTGRES_ENGINE = "django.db.backends.postgresql"
        POSTGRES_NAME = "{POSTGRES_NAME}"
        POSTGRES_USER = "{POSTGRES_USER}"
        POSTGRES_PASSWORD = "{POSTGRES_PASSWORD}"
        POSTGRES_HOST = "127.0.0.1"
        POSTGRES_PORT = "5432"

        [mosquitto]
        MOSQUITTO_HOST = "localhost"
        MOSQUITTO_PORT = 1883
        MOSQUITTO_DYNSEC_TOPIC = "$CONTROL/dynamic-security/v1"
        MOSQUITTO_DYNSEC_RESPONSE_TOPIC = "$CONTROL/dynamic-security/v1/response"
        MOSQUITTO_DYNSEC_ADMIN = "{MOSQUITTO_DYNSEC_ADMIN}"
        MOSQUITTO_DYNSEC_PASSWORD = "{MOSQUITTO_DYNSEC_PASSWORD}"

        [nodered]
        SERVERBLOCK_CREATE_SCRIPT_PATH = "{SERVERBLOCK_CREATE_SCRIPT_PATH}"

        [influxdb]
        INFLUX_ADMIN_USERNAME = "{INFLUX_ADMIN_USERNAME}"
        INFLUX_ADMIN_PASSWORD = "{INFLUX_ADMIN_PASSWORD}"
        INFLUX_ADMIN_BUCKET = "{INFLUX_ADMIN_BUCKET}"
        INFLUX_ORG_NAME = "{INFLUX_ORG_NAME}"
        INFLUX_ORG_ID = "{INFLUX_ORG_ID}"
        INFLUX_OPERATOR_TOKEN = "{INFLUX_OPERATOR_TOKEN}"
        INFLUX_ALL_ACCESS_TOKEN = "{INFLUX_ALL_ACCESS_TOKEN}"

        [grafana]
        GRAFANA_ORG_NAME = "{GRAFANA_ORG_NAME}"
        """.format(**values)

    with open(destination, 'w') as config_file:
        config_file.write(content)

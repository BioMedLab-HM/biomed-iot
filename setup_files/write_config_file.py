def write_config_file(all_config_data, destination):
    """
    Substitutes variables in content with values (dict) and writes the content
    into the destination (/etc/iotree/config.toml).
    
    TODO: Vervollständigen für Grafana!
    """
    content = """
        [mail]
        RES_EMAIL_HOST = "{RES_EMAIL_HOST}"
        RES_EMAIL_PORT = "{RES_EMAIL_PORT}"
        RES_EMAIL_ADDRESS = "{RES_EMAIL_ADDRESS}"
        RES_EMAIL_PASSWORD = "{RES_EMAIL_PASSWORD}"

        [django]
        DJANGO_SECRET_KEY = "{DJANGO_SECRET_KEY}"
        DJANGO_ADMIN_MAIL = "{DJANGO_ADMIN_MAIL}"
        DJANGO_ADMIN_NAME = "{DJANGO_ADMIN_NAME}"
        DJANGO_ADMIN_PASS = "{DJANGO_ADMIN_PASS}"

        [host]
        IP = "{IP}"
        HOSTNAME = "{HOSTNAME}"
        DOMAIN = "{DOMAIN}"

        [postgres]
        POSTGRES_NAME = "{POSTGRES_NAME}"
        POSTGRES_USER = "{POSTGRES_USER}"
        POSTGRES_PASSWORD = "{POSTGRES_PASSWORD}"
        POSTGRES_HOST = "{POSTGRES_HOST}"
        POSTGRES_PORT = "{POSTGRES_PORT}"

        [mosquitto]
        MOSQUITTO_HOST = "{MOSQUITTO_HOST}"
        MOSQUITTO_PORT = "{MOSQUITTO_PORT}"
        DYNSEC_TOPIC = "{DYNSEC_TOPIC}"
        DYNSEC_RESPONSE_TOPIC = "{DYNSEC_RESPONSE_TOPIC}"
        DYNSEC_ADMIN_USER = "{DYNSEC_ADMIN_USER}"
        DYNSEC_ADMIN_PW = "{DYNSEC_ADMIN_PW}"
        DYNSEC_CONTROL_USER = "{DYNSEC_CONTROL_USER}"
        DYNSEC_CONTROL_PW = "{DYNSEC_CONTROL_PW}"
        MQTT_IN_TO_DB_USER = "{MQTT_IN_TO_DB_USER}"
        MQTT_IN_TO_DB_PW = "{MQTT_IN_TO_DB_PW}"
        MQTT_OUT_TO_DB_USER = "{MQTT_OUT_TO_DB_USER}"
        MQTT_OUT_TO_DB_PW = "{MQTT_OUT_TO_DB_PW}"

        [nodered]
        SERVERBLOCK_CREATE_SCRIPT_PATH = "{SERVERBLOCK_CREATE_SCRIPT_PATH}"

        [influxdb]
        INFLUX_HOST: "{INFLUX_HOST}"
        INFLUX_PORT: "{INFLUX_PORT}"
        INFLUX_ADMIN_USERNAME = "{INFLUX_ADMIN_USERNAME}"
        INFLUX_ADMIN_PASSWORD = "{INFLUX_ADMIN_PASSWORD}"
        INFLUX_ADMIN_BUCKET = "{INFLUX_ADMIN_BUCKET}"
        INFLUX_ORG_NAME = "{INFLUX_ORG_NAME}"
        INFLUX_ORG_ID = "{INFLUX_ORG_ID}"
        INFLUX_OPERATOR_TOKEN = "{INFLUX_OPERATOR_TOKEN}"
        INFLUX_ALL_ACCESS_TOKEN = "{INFLUX_ALL_ACCESS_TOKEN}"

        [grafana]
        GRAFANA_HOST: "{GRAFANA_HOST}"
        GRAFANA_PORT: "{GRAFANA_PORT}"
        GRAFANA_ORG_NAME = "{GRAFANA_ORG_NAME}"
        """.format(**all_config_data)

    with open(destination, 'w') as config_file:
        config_file.write(content)

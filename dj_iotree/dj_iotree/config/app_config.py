import tomllib

class AppConfig:
    """
    Advantages of having a separate class that abstracts the config.toml file
        Improved Readability: Accessing configuration values using attribute 
        access can make the code more readable and easier to understand at a 
        glance, especially for those unfamiliar with the configuration's 
        structure.
    
        Enhanced Error Handling: With a class, you can implement custom error 
        handling, default values, and validation logic, making your 
        configuration more robust.

        Encapsulation: Encapsulates configuration logic in one place, 
        potentially reducing repetitive code and making it easier to update 
        configuration logic or structure.

        Autocompletion and Refactoring: Many IDEs offer better support for 
        autocompletion and refactoring with attribute access compared to 
        dictionary keys, improving developer productivity.
    """
    def __init__(self, config_path="etc/iotree/config.toml"):
        self.config_data = tomllib.load(config_path)

    ### MAIL ###

    @property
    def reset_email_host(self):
        return self.config_data['mail']['RES_EMAIL_HOST']

    @property
    def reset_email_port(self):
        return self.config_data['mail']['RES_EMAIL_PORT']

    @property
    def reset_email_address(self):
        return self.config_data['mail']['RES_EMAIL_ADDRESS']

    @property
    def reset_email_password(self):
        return self.config_data['mail']['RES_EMAIL_PASSWORD']


    ### DJANGO ###

    @property
    def django_secret_key(self):
        return self.config_data['django']['DJANGO_SECRET_KEY']

    @property
    def django_admin_mail(self):
        return self.config_data['django']['DJANGO_ADMIN_MAIL']

    @property
    def django_admin_name(self):
        return self.config_data['django']['DJANGO_ADMIN_NAME']

    @property
    def django_admin_pass(self):
        return self.config_data['django']['DJANGO_ADMIN_PASS']


    ### HOST ###

    @property
    def ip(self):
        return self.config_data['host']['IP']

    @property
    def hostname(self):
        return self.config_data['host']['HOSTNAME']

    @property
    def domain(self):
        return self.config_data['host']['DOMAIN']


    ### POSTGRES ###

    @property
    def postgres_name(self):
        return self.config_data['postgres']['POSTGRES_NAME']

    @property
    def postgres_host(self):
        return self.config_data['postgres']['POSTGRES_HOST']

    @property
    def postgres_port(self):
        return self.config_data['postgres']['POSTGRES_PORT']

    @property
    def postgres_user(self):
        return self.config_data['postgres']['POSTGRES_USER']

    @property
    def postgres_password(self):
        return self.config_data['postgres']['POSTGRES_PASSWORD']


    ### MOSQUITTO ###

    @property
    def mosquitto_host(self):
        return self.config_data['mosquitto']['MOSQUITTO_HOST']

    @property
    def mosquitto_port(self):
        return self.config_data['mosquitto']['MOSQUITTO_PORT']

    @property
    def dynsec_topic(self):
        return self.config_data['mosquitto']['DYNSEC_TOPIC']

    @property
    def dynsec_response_topic(self):
        return self.config_data['mosquitto']['DYNSEC_RESPONSE_TOPIC']

    @property
    def dynsec_admin_user(self):
        return self.config_data['mosquitto']['DYNSEC_ADMIN_USER']

    @property
    def dynsec_admin_pw(self):
        return self.config_data['mosquitto']['DYNSEC_ADMIN_PW']

    @property
    def dynsec_control_user(self):
        return self.config_data['mosquitto']['DYNSEC_CONTROL_USER']

    @property
    def dynsec_control_pw(self):
        return self.config_data['mosquitto']['DYNSEC_CONTROL_PW']

    @property
    def mqtt_in_to_db_user(self):
        return self.config_data['mosquitto']['MQTT_IN_TO_DB_USER']

    @property
    def mqtt_in_to_db_pw(self):
        return self.config_data['mosquitto']['MQTT_IN_TO_DB_PW']

    @property
    def mqtt_out_to_db_user(self):
        return self.config_data['mosquitto']['MQTT_OUT_TO_DB_USER']

    @property
    def mqtt_out_to_db_pw(self):
        return self.config_data['mosquitto']['MQTT_OUT_TO_DB_PW']


    @property
    def serverblock_create_script_path(self):
        return self.config_data['nodered']['SERVERBLOCK_CREATE_SCRIPT_PATH']


    ### INFLUX DB ###

    @property
    def influx_host(self):
        return self.config_data['influxdb']['INFLUX_HOST']

    @property
    def influx_port(self):
        return self.config_data['influxdb']['INFLUX_PORT']
    
    @property
    def influx_admin_username(self):
        return self.config_data['influxdb']['INFLUX_ADMIN_USERNAME']

    @property
    def influx_admin_password(self):
        return self.config_data['influxdb']['INFLUX_ADMIN_PASSWORD']

    @property
    def influx_admin_bucket(self):
        return self.config_data['influxdb']['INFLUX_ADMIN_BUCKET']

    @property
    def influx_org_name(self):
        return self.config_data['influxdb']['INFLUX_ORG_NAME']

    @property
    def influx_org_id(self):
        return self.config_data['influxdb']['INFLUX_ORG_ID']

    @property
    def influx_operator_token(self):
        return self.config_data['influxdb']['INFLUX_OPERATOR_TOKEN']

    @property
    def influx_all_access_token(self):
        return self.config_data['influxdb']['INFLUX_ALL_ACCESS_TOKEN']


    ### GRAFANA ###

    @property
    def grafana_host(self):
        return self.config_data['grafana']['GRAFANA_HOST']

    @property
    def grafana_port(self):
        return self.config_data['grafana']['GRAFANA_PORT']
    
    @property
    def grafana_org_name(self):
        return self.config_data['grafana']['GRAFANA_ORG_NAME']


import logging
from django.db.models.signals import post_save, pre_delete  # noqa
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .models import Profile, NodeRedUserData  # noqa
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType  # noqa
from .services.nodered_utils import NoderedContainer, del_nodered_nginx_conf
from .services.influx_utils import InfluxUserManager
from .services.grafana_utils import GrafanaUserManager

logger = logging.getLogger(__name__)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_mqtt_setup(sender, instance, created, **kwargs):
    if created:
        # Initialize MQTT meta data and create MQTT client access roles
        mqtt_metadata_manager = MqttMetaDataManager(user=instance)
        try:
            mqtt_metadata_manager.create_nodered_role()
        except Exception as e:
            logger.error(f"Error creating Node-RED role: {e}")
        try:
            mqtt_metadata_manager.create_device_role()
        except Exception as e:
            logger.error(f"Error creating device role: {e}")

        # Initialize MQTT clients for Node-RED and an example device
        mqtt_client_manager = MqttClientManager(user=instance)
        try:
            mqtt_client_manager.create_client(textname="Automation Tool Credentials", role_type=RoleType.NODERED.value)
        except Exception as e:
            logger.error(f"Error creating MQTT Node-RED client: {e}")
        try:
            mqtt_client_manager.create_client(textname="Example Device", role_type=RoleType.DEVICE.value)
        except Exception as e:
            logger.error(f"Error creating MQTT device client: {e}")

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_influxdb_and_grafana_setup(sender, instance, created, **kwargs):
    if created:
        try:
            influx_user_manager = InfluxUserManager(user=instance)
            influx_user_manager.create_new_influx_user_resources()
        except Exception as e:
            logger.error(f"Error setting up InfluxDB resources: {e}")

        # Create Grafana user account
        logger.info('Signals.py > user_influxdb_and_grafana_setup: after InfluxDB Setup')
        try:
            grafana_user_manager = GrafanaUserManager(user=instance)
            grafana_user_manager.create_user()
        except Exception as e:
            logger.error(f"Error creating Grafana user: {e}")
        logger.info('Signals.py > user_influxdb_and_grafana_setup: after grafana_user_manager.create_user()')

@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_user_service_accounts_and_data(sender, instance, **kwargs):
    user = instance
    delete_mosquitto_user_data(user)
    delete_grafana_user_account(user)
    delete_influxdb_user_resources(user)
    stop_and_delete_nodered_container_and_config(user)

def delete_mosquitto_user_data(user):
    try:
        mosquitto_metadata_manager = MqttMetaDataManager(user)
        mosquitto_metadata_manager.delete_nodered_role()
        mosquitto_metadata_manager.delete_device_role()
    except Exception as e:
        logger.error(f"Error deleting Mosquitto roles: {e}")

    try:
        mosquitto_client_manager = MqttClientManager(user)
        mosquitto_client_manager.delete_all_clients_for_user()
    except Exception as e:
        logger.error(f"Error deleting Mosquitto clients: {e}")

def delete_grafana_user_account(user):
    try:
        grafana_user_manager = GrafanaUserManager(user)
        grafana_user_manager.delete_user()
    except Exception as e:
        logger.error(f"Error deleting Grafana user: {e}")

def delete_influxdb_user_resources(user):
    try:
        influx_user_manager = InfluxUserManager(user)
        influx_user_manager.delete_influx_user_resources()
    except Exception as e:
        logger.error(f"Error deleting InfluxDB resources: {e}")

def stop_and_delete_nodered_container_and_config(user):
    try:
        nodered_user_data = user.nodereduserdata
        nodered_container = NoderedContainer(nodered_user_data)
        nodered_container.delete_container()
        del_nodered_nginx_conf(nodered_user_data)
    except ObjectDoesNotExist:
        logger.info(f"No NodeRedUserData found for user {user}")
    except Exception as e:
        logger.error(f"Error stopping and deleting Node-RED container and config: {e}")

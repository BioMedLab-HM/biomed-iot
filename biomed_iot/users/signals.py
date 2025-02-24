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
    # Delete Mosquitto user data
    try:
        mqtt_metadata_manager = MqttMetaDataManager(user=instance)
        try:
            mqtt_metadata_manager.delete_nodered_role()
        except Exception as e:
            logger.error(f"Error deleting Node-RED role: {e}")
        try:
            mqtt_metadata_manager.delete_device_role()
        except Exception as e:
            logger.error(f"Error deleting device role: {e}")
    except Exception as e:
        logger.error(f"Error initializing MqttMetaDataManager: {e}")

    try:
        mqtt_client_manager = MqttClientManager(user=instance)
        try:
            mqtt_client_manager.delete_all_clients_for_user()
        except Exception as e:
            logger.error(f"Error deleting MQTT clients: {e}")
    except Exception as e:
        logger.error(f"Error initializing MqttClientManager: {e}")

    # Delete Grafana user account
    try:
        grafana_user_manager = GrafanaUserManager(user=instance)
        try:
            grafana_user_manager.delete_user()
        except Exception as e:
            logger.error(f"Error deleting Grafana user: {e}")
    except Exception as e:
        logger.error(f"Error initializing GrafanaUserManager: {e}")

    # Delete InfluxDB user data
    try:
        influx_user_manager = InfluxUserManager(user=instance)
        try:
            influx_user_manager.delete_influx_user_resources()
        except Exception as e:
            logger.error(f"Error deleting InfluxDB user resources: {e}")
    except Exception as e:
        logger.error(f"Error initializing InfluxUserManager: {e}")

    # Stop and Delete the user's Node-RED Container and its nginx config
    try:
        try:
            nodered_user_data = NodeRedUserData.objects.get(user=instance)
        except ObjectDoesNotExist:
            nodered_user_data = None

        if nodered_user_data:
            try:
                nodered_container = NoderedContainer(nodered_user_data)
                nodered_container.delete_container()
            except Exception as e:
                logger.error(f"Error deleting Node-RED container: {e}")
            try:
                del_nodered_nginx_conf(instance)
            except Exception as e:
                logger.error(f"Error deleting Node-RED nginx configuration: {e}")
    except Exception as e:
        logger.error(f"Error handling NodeRedUserData deletion: {e}")

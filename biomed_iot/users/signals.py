import logging
from django.db.models.signals import post_save, pre_delete  # noqa
# settings.AUTH_USER_MODEL instead of importing the user model directly
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .models import Profile, NodeRedUserData  # noqa
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType  # noqa
from .services.nodered_utils import NoderedContainer
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
        mqtt_metadata_manager.create_nodered_role()
        mqtt_metadata_manager.create_device_role()

        # Initialize MQTT clients for Node-RED and an example device
        mqtt_client_manager = MqttClientManager(user=instance)
        mqtt_client_manager.create_client(textname="Automation Tool Credentials", role_type=RoleType.NODERED.value)
        mqtt_client_manager.create_client(textname="Example Device", role_type=RoleType.DEVICE.value)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_influxdb_and_grafana_setup(sender, instance, created, **kwargs):
    if created:
        influx_user_manager = InfluxUserManager(user=instance)
        influx_user_manager.create_new_influx_user_resources()

        # Create Grafana user account
        logger.info('Signals.py > user_influxdb_and_grafana_setup: after InfluxDB Setup')
        print('Signals.py > user_influxdb_and_grafana_setup: after InfluxDB Setup')
        grafana_user_manager = GrafanaUserManager(user=instance)
        logger.info('Signals.py > user_influxdb_and_grafana_setup: created grafana_user_manager instance')
        print('Signals.py > user_influxdb_and_grafana_setup: created grafana_user_manager instance')
        grafana_user_manager.create_user()
        logger.info('Signals.py > user_influxdb_and_grafana_setup: after grafana_user_manager.create_user()')
        print('Signals.py > user_influxdb_and_grafana_setup: after grafana_user_manager.create_user()')


# TODO: Better?: Instead of signals, overwrite delete() method in models (same for create())
@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_user_service_accounts_and_data(sender, instance, **kwargs):
    # Delete Mosquitto user data
    mqtt_metadata_manager = MqttMetaDataManager(user=instance)
    mqtt_metadata_manager.delete_nodered_role()
    mqtt_metadata_manager.delete_device_role()

    mqtt_client_manager = MqttClientManager(user=instance)
    mqtt_client_manager.delete_all_clients_for_user()

    # Delete Grafana user account
    grafana_user_manager = GrafanaUserManager(user=instance)
    grafana_user_manager.delete_user()

    # Delete InfluxDB user data
    influx_user_manager = InfluxUserManager(user=instance)
    influx_user_manager.delete_influx_user_resources()

    # Stop and Delete the user's Nodered Container
    try:
        nodered_user_data = NodeRedUserData.objects.get(user=instance)
    except ObjectDoesNotExist:
        pass  # If no NodeRedUserData exists, do nothing
    else:
        # If NodeRedUserData exists, delete the associated container
        nodered_container = NoderedContainer(nodered_user_data)
        nodered_container.delete_container()


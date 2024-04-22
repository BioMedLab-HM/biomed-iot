from django.db.models.signals import post_save, pre_delete
# from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomUser, Profile, NodeRedUserData  # settings.AUTH_USER_MODEL instead of writing the class name directly
# from .services.nodered_utils import update_nginx_nodered_conf
from django.conf import settings
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType
from .services.nodered_utils import NoderedContainer
from .services.influx_utils import InfluxUserManager

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
    

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_mqtt_setup(sender, instance, created, **kwargs):
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
def create_user_mqtt_setup(sender, instance, created, **kwargs):
    if created:
        influx_user_manager = InfluxUserManager(user=instance)
        influx_user_manager.create_new_influx_user_resources()
        

@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def user_delete(sender, instance, **kwargs):
    # Delete Mosquitto user data
    mqtt_metadata_manager = MqttMetaDataManager(user=instance)
    mqtt_metadata_manager.delete_nodered_role()
    mqtt_metadata_manager.delete_device_role()

    mqtt_client_manager = MqttClientManager(user=instance)
    mqtt_client_manager.delete_all_clients_for_user()

    # Delete Grafana user data
    # TODO: Implement # TODO: Implement # TODO: Implement # TODO: Implement # TODO: Implement # TODO: Implement 
    # grafana_user_manager = GrafanaUserManager(user=instance)
    # grafana_user_manager.delete_user()

    # Delete InfluxDB user data
    influx_user_manager = InfluxUserManager(user=instance)
    influx_user_manager.create_new_influx_user_resources()
    
    # Stop and Delete the user's Nodered Container
    nodered_user_data = NodeRedUserData.objects.get(user=instance)
    nodered_container = NoderedContainer(nodered_user_data)
    nodered_container.delete_container()


    
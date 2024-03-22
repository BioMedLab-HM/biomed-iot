from django.db.models.signals import post_save, pre_delete
# from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomUser, Profile, NodeRedUserData  # settings.AUTH_USER_MODEL instead of writing the class name directly
# from .services.nodered_utils import update_nginx_nodered_conf
from django.conf import settings
from .services.mosquitto_utils import MqttMetaDataManager, MqttClientManager, RoleType

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)  # TODO: acreate?


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


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def user_delete(sender, instance, **kwargs):
    # TODO: implement.
    pass
    # stop and delete Nodered Container

    # username = str(instance)
    # IDs = instance.last_name
    # userID, bucketID = IDs.split(",")
    # del_mqtt_client = DelMqttClient(username)
    # del_mqtt_client.deldel()
    # del del_mqtt_client
    # del_flux_client = DelInfluxAll(userID, bucketID)
    # del_flux_client.run()
    # del del_flux_client
    # del_grafa_client = DelGrafaAll(username)
    # del_grafa_client.run()
    # del del_grafa_client

from django.db.models.signals import post_save, pre_delete
# from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomUser, Profile, NodeRedUserData  # settings.AUTH_USER_MODEL instead of writing the class name directly
from .utils import update_nginx_configuration
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)  # TODO: acreate?


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
    

@receiver(post_save, sender=NodeRedUserData)
def update_nodered_config(sender, instance, **kwargs):
    if kwargs.get('update_fields') and 'container_port' in kwargs['update_fields']:
        # The 'container_port' field was updated
        print("Jetzt kommt die Updatefunction")  # TODO: Später entfernen bzw durch log ersetzen
        update_nginx_configuration(instance)
            

@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def user_delete(sender, instance, **kwargs):
    # TODO: implement
    pass
    # TODO: stop and delete Nodered Container

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

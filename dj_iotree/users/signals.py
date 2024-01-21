from django.db.models.signals import post_save
# from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomUser, Profile, NodeRedUserData
from .utils import update_nginx_configuration


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)  # TODO: acreate?


@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
    

@receiver(post_save, sender=NodeRedUserData)
def update_nodered_config(sender, instance, **kwargs):
    if kwargs.get('update_fields') and 'container_port' in kwargs['update_fields']:
        # The 'container_port' field was updated
        print("Jetzt kommt die Updatefunction")  # TODO: Später entfernen bzw durch log ersetzen
        update_nginx_configuration(instance)
            
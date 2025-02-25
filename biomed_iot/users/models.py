import secrets
import random
import string
import logging
from PIL import Image
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _  # for automatic translation in case if it is implemented later
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_random_readable_string(length, secure=True):
    allowed_chars = ''.join(c for c in string.ascii_letters + string.digits if c not in "OIl01")
    if secure:
        return ''.join(secrets.choice(allowed_chars) for _ in range(length))
    else:
        return ''.join(random.choice(allowed_chars) for _ in range(length))


class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError(_('The username field must be set'))
        if not email:
            raise ValueError(_('The email field must be set'))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(username=username, email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    """
    About custom user models:
    https://medium.com/@akshatgadodia/the-power-of-customising-django-user-why-you-should-start-early-e9036eae8c6d
    username, first_name, last_name, email, is_staff, is_active, date_joined are already present in AbstractUser.
    If you want to unset any of these fields just do <fieldname> = None
    """
    objects = CustomUserManager()
    email = models.EmailField(unique=True)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.email)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        # save function overridden to resize large images
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


class NodeRedUserData(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    container_name = models.CharField(max_length=100, unique=True)
    # container_port can be set to null (None in code) to avoid integrity error due to UNIQUE constraint failure
    # default=0 for container_port creates conflicts with other users who still have default 0
    container_port = models.CharField(
        max_length=5, unique=True, null=True, blank=True
    )  # highest possible port number has five digits (65535)
    access_token = models.CharField(max_length=120)
    username = models.CharField(max_length=120, null=True)
    password = models.CharField(max_length=120, null=True)
    is_configured = models.BooleanField(default=False)
    # idea: add data from the container like flows, dashboards and list of installed nodered plugins

    def __str__(self):
        return self.container_name

    @staticmethod
    def generate_unique_container_name():
        logger.debug('Generate unique container name function started')
        max_attempts = 1000
        for attempt in range(max_attempts):
            logger.debug(f'Attempt {attempt+1} to generate unique container name')
            new_name = generate_random_readable_string(20, secure=True)
            if not NodeRedUserData.objects.filter(container_name=new_name).exists():
                logger.debug(f'Unique container name generated: {new_name}')
                return new_name
        logger.error('Failed to generate a unique container name after maximum attempts')
        return None

    @staticmethod
    def generate_credentials():
        new_username = generate_random_readable_string(10, secure=True)
        new_password = generate_random_readable_string(20, secure=True)
        return new_username, new_password


class MqttMetaData(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    user_topic_id = models.CharField(max_length=12, unique=True)
    nodered_role_name = models.CharField(max_length=14, unique=True)
    device_role_name = models.CharField(max_length=14, unique=True)

    def __str__(self):
        return self.user_topic_id

    @staticmethod
    def generate_unique_mqtt_metadata():
        max_attempts = 1000
        for attempt in range(max_attempts):
            new_user_topic_id = generate_random_readable_string(12, secure=True)
            new_nodered_role_name = 'nodered-' + new_user_topic_id
            new_device_role_name = 'device-' + new_user_topic_id
            if not MqttMetaData.objects.filter(user_topic_id=new_user_topic_id).exists():
                return new_user_topic_id, new_nodered_role_name, new_device_role_name
        logger.error('Failed to generate unique MQTT metadata after maximum attempts')
        return None, None, None


class MqttClient(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=30, default='')
    textname = models.CharField(max_length=30, blank=True, default='')
    rolename = models.CharField(max_length=14, blank=True, default='')

    def __str__(self):
        return self.username

    @staticmethod
    def generate_unique_username():
        max_attempts = 1000
        for attempt in range(max_attempts):
            new_name = generate_random_readable_string(20, secure=True)
            if not MqttClient.objects.filter(username=new_name).exists():
                return new_name
        logger.error('Failed to generate unique MQTT client username after maximum attempts')
        return None

    @staticmethod
    def generate_password():
        new_password = generate_random_readable_string(length = 30, secure=True)
        return new_password


class InfluxUserData(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # TODO: OneToOneField
    bucket_name = models.CharField(max_length=20, unique=True)
    bucket_id = models.CharField(max_length=50)
    bucket_token = models.CharField(max_length=50)
    bucket_token_id = models.CharField(max_length=50)

    def __str__(self):
        return self.bucket_name

    @staticmethod
    def generate_unique_bucket_name():
        max_attempts = 1000
        for attempt in range(max_attempts):
            new_name = generate_random_readable_string(name_length = 20, secure=True)
            if not InfluxUserData.objects.filter(bucket_name=new_name).exists():
                return new_name
        logger.error('Failed to generate unique bucket name after maximum attempts')
        return None

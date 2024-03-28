import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager  # User (if Django standard User model shall be used)
from PIL import Image
from django.utils.translation import gettext_lazy as _  # This is for automatic translation in case if it is implemented later
import os
import subprocess
from django.conf import settings
import random
import string


class CustomUserManager(BaseUserManager):
    """
    About custom user models: https://medium.com/@akshatgadodia/the-power-of-customising-django-user-why-you-should-start-early-e9036eae8c6d
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a user with the given username, email and password.
        """
        if not username:
            raise ValueError(_('The username field must be set'))
        if not email:
            raise ValueError(_('The email field must be set'))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()  # user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given username, email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        # As you're making username a required field, we add it as an argument.
        # You can further enforce other required fields in a similar manner.
        return self.create_user(username=username, email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    """
    About custom user models: https://medium.com/@akshatgadodia/the-power-of-customising-django-user-why-you-should-start-early-e9036eae8c6d
    username, first_name, last_name, email, is_staff, is_active, date_joined are already present in Abstract User.
    If you want to unset any of these fields just do <fieldname> = None
    """

    # Add your custom fields here
    objects = CustomUserManager()  # Use CustomUserManager instead of UserManager
    email = models.EmailField(unique=True)  # Only one account per email address
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']

    def __str__(self):
        return str(self.email)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):  # save function overridden to resize large images
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


class NodeRedUserData(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    container_name = models.CharField(max_length=30, unique=True)
    container_port = models.CharField(max_length=5, default=0, unique=True)  # since highest possible port number has five digits (65535)
    access_token = models.CharField(max_length=100)
    # later maybe add data from the container like flows, dashboards and list of installed nodered plugins

    def __str__(self):
        return self.container_name

    @staticmethod
    def generate_unique_container_name():
        max_attempts = 1000
        for _ in range(max_attempts):
            new_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
            if not NodeRedUserData.objects.filter(container_name=new_name).exists():
                return new_name


class MqttMetaData(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    user_topic_id = models.CharField(max_length=6, unique=True)
    nodered_role_name = models.CharField(max_length=14, unique=True)
    device_role_name = models.CharField(max_length=14, unique=True)

    def __str__(self):
        return self.user_topic_id
    
    @staticmethod
    def generate_unique_mqtt_metadata():
        max_attempts = 1000
        for _ in range(max_attempts):
            new_user_topic_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))  # change to lowercase and numbers
            new_nodered_role_name = 'nodered-' + new_user_topic_id
            new_device_role_name = 'device-' + new_user_topic_id
            if not MqttMetaData.objects.filter(user_topic_id=new_user_topic_id).exists():
                return new_user_topic_id,  new_nodered_role_name, new_device_role_name


class MqttClient(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=30, default="")
    textname = models.CharField(max_length=30, blank=True, default="")
    rolename = models.CharField(max_length=14, blank=True, default="")

    def __str__(self):
        return self.username

    @staticmethod
    def generate_unique_username():
        max_attempts = 1000
        for _ in range(max_attempts):
            new_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
            if not MqttClient.objects.filter(username=new_name).exists():
                return new_name
        return None

    @staticmethod
    def generate_password(length=30):
        # Define the characters to use in the password
        characters = string.ascii_letters + string.digits # This includes uppercase, lowercase, and digits
        # Generate the password using a list comprehension and join it into a string
        new_password = ''.join(secrets.choice(characters) for _ in range(length))
        return new_password
    
    # not using this version anymore since it also uses "-" symbols 
    # which make it harder to highlight with double-click in the password field 
    # @staticmethod
    # def generate_password():
    #     new_password = secrets.token_urlsafe(22)  # equals approx. 20 characters
    #     return new_password

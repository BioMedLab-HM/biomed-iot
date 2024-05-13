# Run this in your Django shell
from django.core.mail import send_mail
from django.conf import settings

send_mail('Test Email','This is a test email from Django.',settings.EMAIL_HOST_USER,['rene.sesgoer@gmail.com'],fail_silently=False)

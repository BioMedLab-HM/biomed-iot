# Send an Email from Django using the SMTP Mailserver 
# Run this in your Django shell
from django.core.mail import send_mail
from django.conf import settings

subject = 'Test Email'
message = 'This is a test email from Django.'
email_address = 'ADD_EMAIL_FOR_TEST'
send_mail(subject,message,settings.EMAIL_HOST_USER,[email_address],fail_silently=False)

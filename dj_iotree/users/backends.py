from django.contrib.auth.backends import ModelBackend
from .models import CustomUser
# TODO: logger nach Debugging entfernen
import logging
logger = logging.getLogger(__name__)
logger.debug("This is a test debug message.")

class UsernameAuthBackend(ModelBackend):
    """
    Custom authentication backend. Allows users to log in using their username.
    Created because of CustomUser model.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Overrides the authenticate method
        """
        #logger.debug("before try: %s", user)
        try:
            # Try to fetch the user by searching the username field
            #TODO: warum hier nicht .first() bzw. warum unten mit??
            user = CustomUser.objects.get(username=username)
            logger.debug("User fetched: %s", user)
            if user and user.check_password(password):
                return user
            return None
        except CustomUser.DoesNotExist:
            logger.debug("No User :-(%s")
            return None

    def get_user(self, user_id):
        """
        Overrides the get_user method
        """
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            logger.debug("User does not exist for user_id: %s", user_id)
            return None
        

class EmailAuthBackend(ModelBackend):
    """
    Custom authentication backend. Allows users to log in using their email address.
    Also created because of CustomUser model.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by searching the username field
            user = CustomUser.objects.filter(email=username).first()
            logger.debug("User fetched: %s", user)
            # TODO: oder nachfolgende Zeile von dev.to/...
            # user = CustomUser.objects.get(email=username)
            if user and user.check_password(password):
                return user
            return None
        except CustomUser.DoesNotExist:
            logger.debug("User does not exist for username: %s", username)
            return None
        
    def get_user(self, user_id):
        """
        Overrides the get_user method
        """
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
        
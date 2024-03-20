from users.models import MqttUserMetaData, MqttClients
from .mosquitto_dynsec import MosquittoDynSec as dynsec
from django.db import transaction
from django.db import IntegrityError
import secrets
from django.contrib import messages


class MqttMetaDataManager():
    """
    Manages MQTT metadata for users.

    This class is responsible for creating and managing MQTT user metadata,
    including unique topic IDs and roles for Node-RED and device communication.
    It should be used during user registration to initialize MQTT metadata.
    """

    def __init__(self, request):
        self.django_user = request.user
        self.metadata = self.get_or_create_mqtt_meta_data()

    def get_or_create_mqtt_meta_data(self):
        """
        Returns the MqttUserMetaData instance for the current user,
        creating it if it does not exist.
        """
        meta_data = None

        with transaction.atomic():
            try:
                user_topic_id, nodered_role_name, device_role_name = MqttUserMetaData.generate_unique_mqtt_metadata()
                meta_data, created = MqttUserMetaData.objects.get_or_create(
                    user=self.django_user,
                    defaults={
                        'user_topic_id': user_topic_id,
                        'nodered_role_name': nodered_role_name,
                        'device_role_name': device_role_name
                    }
                )
            except IntegrityError:
                print("Integrity-Error while trying to create MqttUserMetaData. Check if MqttUserMetaData already exists")

        return meta_data
    
    def create_nodered_role(self):
        """
        Creates the Node-RED role based on the user's MQTT metadata.
        Returns True if the role creation was successful, False otherwise.
        """
        if self.metadata != None:
            nodered_sub_topic = f"in/{self.metadata.user_topic_id}/#"
            nodered_pub_topic = f"out/{self.metadata.user_topic_id}/#"

            success, _ = dynsec.create_role(self.metadata.nodered_role_name, 
                                            acls=[{"acltype": "subscribePattern", "topic": nodered_sub_topic, "priority": -1, "allow": True}, 
                                                  {"acltype": "publishClientSend", "topic": nodered_pub_topic, "priority": -1, "allow": True}
                                                ])
        return success

    def create_device_role(self):
        """
        Creates a device role based on the user's MQTT metadata.
        Returns True if the role creation was successful, False otherwise.
        """
        if self.metadata != None:
            device_sub_topic = f"out/{self.metadata.user_topic_id}/#"
            device_pub_topic = f"in/{self.metadata.user_topic_id}/#"

            success, _ = dynsec.create_role(self.metadata.device_role_name, 
                                            acls=[{"acltype": "subscribePattern", "topic": device_sub_topic, "priority": -1, "allow": True}, 
                                                  {"acltype": "publishClientSend", "topic": device_pub_topic, "priority": -1, "allow": True}
                                                ])
        return success

    def delete_nodered_role(self):
        """
        Deletes the Node-RED role based on the nodered_role_name in the user's MQTT metadata.
        Returns True if the role deletion was successful, False otherwise.
        """
        if self.metadata != None:
            nodered_role_name = self.metadata.nodered_role_name
            success, _ = dynsec.delete_role(nodered_role_name)
        return success

    def delete_device_role(self):
        """
        Deletes a device role based on the device_role_name in the user's MQTT metadata.
        Returns True if the role deletion was successful, False otherwise.
        """
        if self.metadata != None:
            device_role_name = self.metadata.device_role_name
            success, _ = dynsec.delete_role(device_role_name)
        return success
    

class MqttClientManager():
    def __init__(self, request):
        self.django_user = request.user
        # self.mqtt_client = siehe MqttMetaDataManager

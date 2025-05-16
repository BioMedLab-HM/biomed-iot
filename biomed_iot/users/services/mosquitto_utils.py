import users.models
from .mosquitto_dynsec import MosquittoDynSec
from django.db import transaction, IntegrityError
from enum import Enum, unique
from biomed_iot.config_loader import config
import logging

logger = logging.getLogger(__name__)

@unique
class RoleType(Enum):
    DEVICE = 'device'
    NODERED = 'nodered'
    INOUT = 'inout'

class MqttMetaDataManager:
    def __init__(self, user):
        self.user = user
        self.metadata = self._get_or_create_mqtt_meta_data()
        self.dynsec_username = config.mosquitto.DYNSEC_ADMIN_USER
        self.dynsec_password = config.mosquitto.DYNSEC_ADMIN_PW

    def _get_or_create_mqtt_meta_data(self):
        meta_data = None
        with transaction.atomic():
            try:
                user_topic_id, nodered_role_name, device_role_name, inout_role_name = (
                    users.models.MqttMetaData.generate_unique_mqtt_metadata()
                )
                meta_data, created = users.models.MqttMetaData.objects.get_or_create(
                    user=self.user,
                    defaults={
                        'user_topic_id': user_topic_id,
                        'nodered_role_name': nodered_role_name,
                        'device_role_name': device_role_name,
                        'inout_role_name': inout_role_name,
                    },
                )
            except IntegrityError:
                logger.error('IntegrityError while creating MqttMetaData. Check if it already exists.')
        return meta_data

    def create_nodered_role(self):
        success = False
        if self.metadata:
            nodered_sub_topic = f'in/{self.metadata.user_topic_id}/#'
            nodered_pub_topic = f'out/{self.metadata.user_topic_id}/#'
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.create_role(
                        self.metadata.nodered_role_name,
                        acls=[
                            {
                                'acltype': 'subscribePattern',
                                'topic': nodered_sub_topic,
                                'priority': -1,
                                'allow': True,
                            },
                            {
                                'acltype': 'publishClientSend',
                                'topic': nodered_pub_topic,
                                'priority': -1,
                                'allow': True,
                            },
                        ],
                    )
                    if not success:
                        logger.error(f"Failed to create Node-RED role: {self.metadata.nodered_role_name}")
                except Exception as e:
                    logger.error(f"Exception during Node-RED role creation: {e}")
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for Node-RED role creation: {e}")
        return success

    def create_device_role(self):
        success = False
        if self.metadata:
            device_sub_topic = f'out/{self.metadata.user_topic_id}/#'
            device_pub_topic = f'in/{self.metadata.user_topic_id}/#'
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.create_role(
                        self.metadata.device_role_name,
                        acls=[
                            {
                                'acltype': 'subscribePattern',
                                'topic': device_sub_topic,
                                'priority': -1,
                                'allow': True,
                            },
                            {
                                'acltype': 'publishClientSend',
                                'topic': device_pub_topic,
                                'priority': -1,
                                'allow': True,
                            },
                        ],
                    )
                    if not success:
                        logger.error(f"Failed to create device role: {self.metadata.device_role_name}")
                except Exception as e:
                    logger.error(f"Exception during device role creation: {e}")
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for device role creation: {e}")
        return success

    def create_inout_role(self):
        success = False
        if self.metadata:
            inout_topic = f'inout/{self.metadata.user_topic_id}/#'
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.create_role(
                        self.metadata.inout_role_name,
                        acls=[
                            {
                                'acltype': 'publishClientSend',
                                'topic': inout_topic,
                                'priority': -1,
                                'allow': True,
                            },
                            {
                                'acltype': 'subscribePattern',
                                'topic': inout_topic,
                                'priority': -1,
                                'allow': True,
                            },
                        ],
                    )
                    if not success:
                        logger.error(f"Failed to create in/out role: {self.metadata.inout_role_name}")
                except Exception as e:
                    logger.error(f"Exception during in/out role creation: {e}")
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for in/out role creation: {e}")
        return success

    def delete_inout_role(self):
        success = False
        if self.metadata:
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.delete_role(self.metadata.inout_role_name)
                    if not success:
                        logger.error(f"Failed to delete in/out role: {self.metadata.inout_role_name}")
                except Exception as e:
                    logger.error(f"Exception during delete_role for in/out: {e}")
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for in/out role deletion: {e}")
        return success


    def delete_nodered_role(self):
        success = False
        if self.metadata:
            nodered_role_name = self.metadata.nodered_role_name
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.delete_role(nodered_role_name)
                    if not success:
                        logger.error(f"Failed to delete Node-RED role: {nodered_role_name}")
                except Exception as e:
                    logger.error(f"Exception during delete_role for Node-RED: {e}")
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for Node-RED role deletion: {e}")
        return success

    def delete_device_role(self):
        success = False
        if self.metadata:
            device_role_name = self.metadata.device_role_name
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.delete_role(device_role_name)
                    if not success:
                        logger.error(f"Failed to delete device role: {device_role_name}")
                except Exception as e:
                    logger.error(f"Exception during delete_role for device: {e}")
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for device role deletion: {e}")
        return success

class MqttClientManager:
    def __init__(self, user):
        self.user = user
        self.dynsec_username = config.mosquitto.DYNSEC_ADMIN_USER
        self.dynsec_password = config.mosquitto.DYNSEC_ADMIN_PW

    def create_client(self, textname='New Device', role_type=None):
        new_username = users.models.MqttClient.generate_unique_username()
        new_password = users.models.MqttClient.generate_password()
        success = False

        try:
            mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
            meta_manager = MqttMetaDataManager(self.user)

            if role_type == RoleType.INOUT.value:
                meta_manager.create_inout_role()
                rolename = mqtt_meta_data.inout_role_name
            elif role_type == RoleType.DEVICE.value:
                meta_manager.create_device_role()
                rolename = mqtt_meta_data.device_role_name
            else:
                textname = 'Node-RED MQTT Credentials'
                meta_manager.create_nodered_role()
                rolename = mqtt_meta_data.nodered_role_name

            dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
            try:
                success = dynsec.create_client(
                    new_username,
                    new_password,
                    textname=textname,
                    roles=[{'rolename': rolename, 'priority': -1}]
                )
            except Exception as e:
                logger.error(f"Exception during create_client in MosquittoDynSec: {e}")
            finally:
                dynsec.disconnect()

        except users.models.MqttMetaData.DoesNotExist:
            logger.error('MqttMetaData does not exist for the user.')
        except IntegrityError as e:
            logger.error(f'Database error when creating MQTT client: {e}')

        if success:
            users.models.MqttClient.objects.create(
                user=self.user,
                username=new_username,
                password=new_password,
                textname=textname,
                rolename=rolename,
            )

    # def create_client(self, textname='New Device', role_type=None):
    #     new_username = users.models.MqttClient.generate_unique_username()
    #     new_password = users.models.MqttClient.generate_password()

    #     try:
    #         mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
    #         if role_type == RoleType.DEVICE.value:
    #             rolename = mqtt_meta_data.device_role_name
    #         elif role_type == RoleType.NODERED.value:
    #             textname = 'Node-RED MQTT Credentials'
    #             rolename = mqtt_meta_data.nodered_role_name
    #         roles = [{'rolename': rolename, 'priority': -1}]

    #         try:
    #             dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
    #             try:
    #                 success = dynsec.create_client(new_username, new_password, textname=textname, roles=roles)
    #             except Exception as e:
    #                 logger.error(f"Exception during create_client in MosquittoDynSec: {e}")
    #                 success = False
    #             finally:
    #                 dynsec.disconnect()
    #         except Exception as e:
    #             logger.error(f"Error initializing MosquittoDynSec for client creation: {e}")
    #             success = False

    #         if success:
    #             users.models.MqttClient.objects.create(
    #                 user=self.user,
    #                 username=new_username,
    #                 password=new_password,
    #                 textname=textname,
    #                 rolename=rolename,
    #             )
    #         else:
    #             logger.error('Failed to create MQTT client in dynamic security system.')
    #     except users.models.MqttMetaData.DoesNotExist:
    #         logger.error('MqttMetaData does not exist for the user.')
    #     except IntegrityError as e:
    #         logger.error(f'Database error when creating MQTT client: {e}')

    def modify_client(self, client_username, textname='New MQTT Device'):
        try:
            mqtt_client = users.models.MqttClient.objects.get(username=client_username, user=self.user)
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.modify_client(client_username, textname=textname)
                except Exception as e:
                    logger.error(f"Exception during modify_client in MosquittoDynSec: {e}")
                    success = False
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for modifying client: {e}")
                success = False

            if success:
                mqtt_client.textname = textname
                mqtt_client.save()
                logger.info(f"MQTT client {client_username}'s textname updated to '{textname}' successfully.")
            else:
                logger.error(f'Failed to modify MQTT client {client_username} in dynamic security system.')
        except users.models.MqttClient.DoesNotExist:
            logger.error(f'MQTT client {client_username} not found for the user.')

    def delete_client(self, client_username):
        try:
            mqtt_client = users.models.MqttClient.objects.get(username=client_username, user=self.user)
            try:
                dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
                try:
                    success = dynsec.delete_client(client_username)
                except Exception as e:
                    logger.error(f"Exception during delete_client in MosquittoDynSec: {e}")
                    success = False
                finally:
                    dynsec.disconnect()
            except Exception as e:
                logger.error(f"Error initializing MosquittoDynSec for client deletion: {e}")
                success = False

            if success:
                mqtt_client.delete()
                logger.info(f'MQTT client {client_username} deleted successfully.')
                return True
            else:
                logger.error(f'Failed to delete MQTT client {client_username} from dynamic security system.')
        except users.models.MqttClient.DoesNotExist:
            logger.error(f'MQTT client {client_username} not found for the user.')
        return False

    def delete_all_clients_for_user(self):
        all_clients = users.models.MqttClient.objects.filter(user=self.user)
        try:
            dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
            for client in all_clients:
                try:
                    success = dynsec.delete_client(client.username)
                    if success:
                        logger.info(f'MQTT client {client.username} deleted from dynamic security system successfully.')
                    else:
                        logger.error(f'Failed to delete MQTT client {client.username} from dynamic security system.')
                except Exception as e:
                    logger.error(f"Exception during deletion of client {client.username}: {e}")
            dynsec.disconnect()
        except Exception as e:
            logger.error(f"Error initializing MosquittoDynSec for deleting all clients: {e}")

    def get_device_clients(self):
        try:
            mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
            device_role_name = mqtt_meta_data.device_role_name
            device_clients = users.models.MqttClient.objects.filter(user=self.user, rolename=device_role_name)
            inout_role_name = mqtt_meta_data.inout_role_name
            inout_clients = users.models.MqttClient.objects.filter(user=self.user, rolename=inout_role_name)
            return device_clients.union(inout_clients)
        except users.models.MqttMetaData.DoesNotExist:
            logger.error('MqttMetaData not found for the user.')
            return []

    def get_nodered_client(self):
        try:
            mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
            nodered_role_name = mqtt_meta_data.nodered_role_name
            client = users.models.MqttClient.objects.filter(user=self.user, rolename=nodered_role_name).first()
            return client
        except users.models.MqttMetaData.DoesNotExist:
            logger.error('MqttMetaData not found for the user.')
            return None

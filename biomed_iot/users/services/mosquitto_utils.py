import users.models
from .mosquitto_dynsec import MosquittoDynSec
from django.db import transaction
from django.db import IntegrityError
from enum import Enum, unique
from biomed_iot.config_loader import config
import logging


logger = logging.getLogger(__name__)


@unique
class RoleType(Enum):
	"""
	Used for MqttClientManager. Prevents the use of 'magic values' in various functions.
	Example usage in a view:
	    mqtt_client_manager = MqttClientManager(request.user)
	    mqtt_client_manager.create_client(self, textname="New MQTT Device", role_type=RoleType.DEVICE.value)
	"""

	DEVICE = 'device'
	NODERED = 'nodered'


class MqttMetaDataManager:
	"""
	Manages MQTT metadata for users.

	This class is responsible for creating and managing MQTT user metadata,
	including unique topic IDs and roles for Node-RED and device communication.
	It should be used during user registration to initialize MQTT metadata.
	"""

	def __init__(self, user):
		self.user = user
		self.metadata = self._get_or_create_mqtt_meta_data()
		self.dynsec_username = config.mosquitto.DYNSEC_ADMIN_USER
		self.dynsec_password = config.mosquitto.DYNSEC_ADMIN_PW

	def _get_or_create_mqtt_meta_data(self):
		"""
		Returns the MqttMetaData instance for the current user,
		creating it if it does not exist.
		"""
		meta_data = None
		with transaction.atomic():
			try:
				user_topic_id, nodered_role_name, device_role_name = (
					users.models.MqttMetaData.generate_unique_mqtt_metadata()
				)
				meta_data, created = users.models.MqttMetaData.objects.get_or_create(
					user=self.user,
					defaults={
						'user_topic_id': user_topic_id,
						'nodered_role_name': nodered_role_name,
						'device_role_name': device_role_name,
					},
				)
			except IntegrityError:
				print('Integrity-Error while trying to create MqttMetaData. Check if MqttMetaData already exists')

		return meta_data

	def create_nodered_role(self):
		"""
		Creates the Node-RED role based on the user's MQTT metadata.
		Returns True if the role creation was successful, False otherwise.
		"""
		success = False
		if self.metadata is not None:
			nodered_sub_topic = f'in/{self.metadata.user_topic_id}/#'
			nodered_pub_topic = f'out/{self.metadata.user_topic_id}/#'

			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
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
			finally:
				dynsec.disconnect()

		return success

	def create_device_role(self):
		"""
		Creates a device role based on the user's MQTT metadata.
		Returns True if the role creation was successful, False otherwise.
		"""
		success = False
		if self.metadata is not None:
			device_sub_topic = f'out/{self.metadata.user_topic_id}/#'
			device_pub_topic = f'in/{self.metadata.user_topic_id}/#'
			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
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
			finally:
				dynsec.disconnect()

		return success

	def delete_nodered_role(self):
		"""
		Deletes the Node-RED role based on the nodered_role_name in the user's MQTT metadata.
		Returns True if the role deletion was successful, False otherwise.
		"""
		success = False
		if self.metadata is not None:
			nodered_role_name = self.metadata.nodered_role_name
			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
				success = dynsec.delete_role(nodered_role_name)
			finally:
				dynsec.disconnect()

		return success

	def delete_device_role(self):
		"""
		Deletes a device role based on the device_role_name in the user's MQTT metadata.
		Returns True if the role deletion was successful, False otherwise.
		"""
		success = False
		if self.metadata is not None:
			device_role_name = self.metadata.device_role_name
			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
				success = dynsec.delete_role(device_role_name)
			finally:
				dynsec.disconnect()

		return success


class MqttClientManager:
	"""
	Requires MqttMetaData already to be set.
	"""

	def __init__(self, user):
		self.user = user
		self.dynsec_username = config.mosquitto.DYNSEC_ADMIN_USER
		self.dynsec_password = config.mosquitto.DYNSEC_ADMIN_PW

	def create_client(self, textname='New Device', role_type=None):
		# Generate a unique username and password for the MQTT client
		new_username = users.models.MqttClient.generate_unique_username()
		new_password = users.models.MqttClient.generate_password()

		# Retrieve the MQTT meta data for the user to get the device role name
		try:
			mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
			if role_type == RoleType.DEVICE.value:
				rolename = mqtt_meta_data.device_role_name
			elif role_type == RoleType.NODERED.value:
				textname = 'Node-RED MQTT Credentials'
				rolename = mqtt_meta_data.nodered_role_name

			roles = [{'rolename': rolename, 'priority': -1}]

			# Create the MQTT client in the mosquitto dynamic security plugin
			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
				success = dynsec.create_client(new_username, new_password, textname=textname, roles=roles)
			finally:
				dynsec.disconnect()

			if success:
				# If the MQTT client was successfully created in the dynsec system, save it to the database
				users.models.MqttClient.objects.create(
					user=self.user,
					username=new_username,
					password=new_password,
					textname=textname,
					rolename=rolename,
				)
				# print(f"MQTT client {new_username} created successfully.")
				# TODO: prints erscheinen auch in setup-script --> Umstellung auf Logging
			else:
				print('Failed to create MQTT client in dynamic security system.')
		except users.models.MqttMetaData.DoesNotExist:
			print('MqttMetaData does not exist for the user.')
		except IntegrityError as e:
			print(f'Database error when creating MQTT client: {e}')

	def modify_client(self, client_username, textname='New MQTT Device'):
		"""
		Modifies the textname of an existing MQTT client in both the database and the dynamic security system,
		ensuring that changes are only committed to the database after successful modification in the dynamic security system.
		"""
		try:
			# Attempt to find the MQTT client in the database
			mqtt_client = users.models.MqttClient.objects.get(username=client_username, user=self.user)

			# Next, attempt to modify the client in the dynamic security system
			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
				success = dynsec.modify_client(client_username, textname=textname)
			finally:
				dynsec.disconnect()

			if success:
				# If modification in the dynamic security system is successful, update the database
				mqtt_client.textname = textname
				mqtt_client.save()
				print(f"MQTT client {client_username}'s textname updated to '{textname}' successfully.")
			else:
				print(f'Failed to modify MQTT client {client_username} in dynamic security system.')
		except users.models.MqttClient.DoesNotExist:
			print(f'MQTT client {client_username} not found for the user.')

	def delete_client(self, client_username):
		"""
		Deletes an MQTT client from both the database and the dynamic security system.
		"""
		try:
			mqtt_client = users.models.MqttClient.objects.get(username=client_username, user=self.user)

			# Attempt to delete the client from the dynamic security system
			try:
				dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)
				success = dynsec.delete_client(client_username)
			finally:
				dynsec.disconnect()

			if success:
				mqtt_client.delete()  # from database
				print(f'MQTT client {client_username} deleted successfully.')
				return True
			else:
				print(f'Failed to delete MQTT client {client_username} from dynamic security system.')
		except users.models.MqttClient.DoesNotExist:
			print(f'MQTT client {client_username} not found for the user.')

		return False

	def delete_all_clients_for_user(self):
		"""
		Deletes all MQTT clients for the user from the Mosquitto Dynamic Security Plugin.
		"""
		# Retrieve all MQTT clients for the user
		all_clients = users.models.MqttClient.objects.filter(user=self.user)

		# Initialize the Mosquitto Dynamic Security client
		dynsec = MosquittoDynSec(self.dynsec_username, self.dynsec_password)

		try:
			for client in all_clients:
				# Attempt to delete each client from the dynamic security system
				success = dynsec.delete_client(client.username)
				if success:
					print(f'MQTT client {client.username} deleted from dynamic security system successfully.')
				else:
					print(f'Failed to delete MQTT client {client.username} from dynamic security system.')
		finally:
			dynsec.disconnect()

	def get_device_clients(self):
		"""
		Retrieves a list of MQTT device clients associated with the user's device role.
		"""
		try:
			mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
			device_role_name = mqtt_meta_data.device_role_name
			# Filter the clients based on the users 'device_role_name'
			clients = users.models.MqttClient.objects.filter(user=self.user, rolename=device_role_name)
			return clients
		except users.models.MqttMetaData.DoesNotExist:
			print('MqttMetaData not found for the user.')
			return []

	def get_nodered_client(self):
		"""
		Retrieves the MQTT Node-RED client associated with the user's nodered role.
		"""
		try:
			mqtt_meta_data = users.models.MqttMetaData.objects.get(user=self.user)
			nodered_role_name = mqtt_meta_data.nodered_role_name
			# Filter the clients based on the users 'nodered_role_name'
			client = users.models.MqttClient.objects.filter(user=self.user, rolename=nodered_role_name).first()
			return client
		except users.models.MqttMetaData.DoesNotExist:
			print('MqttMetaData not found for the user.')
			return None

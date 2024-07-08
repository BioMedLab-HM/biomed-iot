import threading
import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTT_ERR_SUCCESS
from biomed_iot.config_loader import config


class MosquittoDynSec:
	"""
	Based on commands at https://github.com/eclipse/mosquitto/blob/master/plugins/dynamic-security/README.md
	About Mosquitto Dynamic Security Plugin (DSP): https://mosquitto.org/documentation/dynamic-security/

	A Python interface for interacting with the Mosquitto MQTT broker's Dynamic Security Plugin (DSP).
	This class abstracts the MQTT communication and command sending to the Dynamic Security Plugin,
	facilitating the management of ACLs, clients, groups, and roles within the broker.

	The class provides setter and getter functions for various configurations supported by the
	Dynamic Security Plugin. Setter functions are used to configure or modify settings, while
	getter functions are used to retrieve current configurations from the broker.

	SETTER functions return a tuple of (success, response), where 'success' is a boolean indicating
	the operation's success, and 'response' is a dictionary containing the broker's response.

	GETTER functions similarly return a tuple of (success, response) where 'response' in this case
	contains the requested configuration data.

	Example usage:
	    mosquitto_dyn_sec = MosquittoDynSec(dynsec_user, dynsec_user_password)
	    success, response = mosquitto_dyn_sec.set_default_acl_access(False, False, False, False)

	Attributes:
	    username (str): Username used to interact with the Mosquitto Dynamic Security Plugin.
	    password (str): Password used for above user.
	    host (str): Hostname or IP address of the MQTT broker.
	    port (int): Network port of the MQTT broker.
	"""

	def __init__(self, username, password, host=config.mosquitto.MOSQUITTO_HOST, port=config.mosquitto.MOSQUITTO_PORT):
		"""
		Initializes a new instance of the MosquittoDynSec class.

		Establishes an MQTT client with the specified credentials and connects to the MQTT broker.
		Sets up necessary MQTT topics for sending commands to and receiving responses from the
		Dynamic Security Plugin. Starts the MQTT client loop to listen for responses.

		Parameters:
		    username (str): The username of the client that writes to the '$CONTROL/dynamic-security/v1' topic.
		    password (str): The password of the client that writes to the '$CONTROL/dynamic-security/v1' topic.
		    host (str): The hostname or IP address of the MQTT broker. Defaults to "localhost".
		    port (int): The network port of the MQTT server. Defaults to 1883.
		"""
		self.username = username
		self.password = password
		self.host = host
		self.port = port

		# MQTT topics
		self.send_command_topic = '$CONTROL/dynamic-security/v1'
		self.response_topic = '$CONTROL/dynamic-security/v1/response'
		self.response_msg = None

		# Create MQTT client instance
		# Changes since paho-mqtt 2.0: https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html
		# TODO: Change callbacks to new paho-mqtt 2.0 standard.
		# Old callback structure still supported for CallbackAPIVersion.VERSION1
		self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

		# Set username and password
		self.client.username_pw_set(self.username, self.password)
		self.client.reconnect_delay_set(min_delay=1, max_delay=2)

		# Events and timeouts
		self.subscription_event = threading.Event()
		self.message_received_event = threading.Event()
		self.sub_event_timeout_seconds = 5
		self.msg_received_timeout_seconds = 10

		# Assign callback functions
		self.client.on_connect = self.on_connect
		self.client.on_subscribe = self.on_subscribe
		self.client.on_message = self.on_message
		self.client.on_publish = self.on_publish

		# Connect and start MQTT client
		self.client.connect(self.host, self.port, 60)
		self.client.loop_start()

	def disconnect(self):
		self.client.loop_stop()
		self.client.disconnect()
		# print("Disconnected MQTT client.")

	"""
    Internal-use functions and callbacks (only used by the class itself)
    """

	def on_publish(self, client, userdata, mid):
		# print(f"Message published with message-id {mid}")
		pass

	def on_message(self, client, userdata, msg):
		# print(f"Topic: `{msg.topic}`\nPayload: `{json.loads(msg.payload.decode('utf-8'))}`")
		self.response_msg = json.loads(msg.payload.decode('utf-8'))
		# print(f"on_message: self.response_msg = {self.response_msg}")
		self.message_received_event.set()  # must be last line to make sure, the message is stored in self.response_msg

	def on_connect(self, client, userdata, flags, rc):
		self.client.subscribe(self.response_topic, qos=2)
		if rc == 0:
			# print("Connected with result code " + str(rc))
			pass
		else:
			# print(f"Failed to connect, return code: {rc}\n")
			pass

	def on_subscribe(self, client, userdata, mid, granted_qos):
		# print("Subscribed to topic")
		# Signal successful subscription
		self.subscription_event.set()

	def _send_command(self, command):
		# print("_send_command called")
		# Construct and send a command to the control topic
		payload = json.dumps(command)
		# Wait for the subscription to be successful
		self.subscription_event.wait(self.sub_event_timeout_seconds)
		# print("Now publishing after successful subscription")
		send_code = self.client.publish(self.send_command_topic, payload, qos=2)
		# print(f'in _send_command: published". send_code = {send_code}')

		return send_code

	def _get_response(self):
		response = self.response_msg
		# warte bis response message gekommen
		event_set = self.message_received_event.wait(self.msg_received_timeout_seconds)
		if event_set:
			response = self.response_msg
			# print(f"Message received: self.response_msg = {self.response_msg}")
			# After processing the message, clear the event and reset self.reply_message
			self.message_received_event.clear()
			self.response_msg = None  # reset the variable for next request to the Dynamic Security Plugin
		else:
			# print(f"No message received: self.response_msg = {self.response_msg}")
			self.response_msg = None
			response = self.response_msg

		return response

	def _is_response_successful(self, command, response, send_code):
		# print(f"In '_is_response_successful'. command: {command}, response: {response}")
		# Response codes for Mosquitto on GitHub:
		# https://github.com/search?q=repo%3Aeclipse%2Fmosquitto++%7B%27responses%27&type=code
		successful = False
		if response is not None and send_code.rc == MQTT_ERR_SUCCESS:
			# Get command name of the command sent and command in response
			command_name = command['commands'][0]['command']  # only one command is expected per function call
			response_command_name = response['responses'][0]['command']

			if command_name == response_command_name:  # Check if the expected command is present in the response
				successful = True
			if 'error' in response['responses'][0]:
				# print(f"In 'error' in response['responses'][0]'. Response: {response['responses'][0]}")
				successful = False
				if 'already' in response['responses'][0]['error']:
					# print('"already" in response["responses"][0]["error"]')
					# caveat: prone to minterpretation if response messages change in the future
					# Known responses containing 'already' on April 16., 2024:
					# 'Role already exists'
					# 'Group already exists'
					# 'Group is already in this role'
					# 'Client is already in this group'
					# 'ACL with this topic already exists'
					successful = True  # since the DSP configuration already matches the desired state

		return successful

	def _execute_command(self, command):
		# print(f"In '_execute_command'. command: {command}")
		send_code = self._send_command(command)  # send_code for debugging
		# print(f"In '_execute_command'. send_code: {send_code}")
		response = self._get_response()
		# print(f"In '_execute_command'. response: {response}")
		success = self._is_response_successful(command, response, send_code)
		# print(f"In '_execute_command'. success: {success}")
		return success, response, send_code

	"""
    External-use getter- and setter-functions (use these to interact with the Mosquitto Dynamic Security Plugin)
    """

	def set_default_acl_access(
		self,
		publish_client_send_allow,
		publish_client_receive_allow,
		subscribe_allow,
		unsubscribe_allow,
	):
		"""
		Configures default ACL permissions for MQTT clients (actions, clients can perform if no specific ACLs apply).

		:param publish_client_send_allow: Allow clients to publish messages (True/False).
		:param publish_client_receive_allow: Allow clients to receive messages (True/False).
		:param subscribe_allow: Allow clients to subscribe to topics (True/False).
		:param unsubscribe_allow: Allow clients to unsubscribe from topics (True/False).
		:return: see "SETTER-functions return values in Class description"
		"""
		command = {
			'commands': [
				{
					'command': 'setDefaultACLAccess',
					'acls': [
						{
							'acltype': 'publishClientSend',
							'allow': publish_client_send_allow,
						},
						{
							'acltype': 'publishClientReceive',
							'allow': publish_client_receive_allow,
						},
						{'acltype': 'subscribe', 'allow': subscribe_allow},
						{'acltype': 'unsubscribe', 'allow': unsubscribe_allow},
					],
				}
			]
		}

		return self._execute_command(command)

	def get_default_acl_access(self):
		"""
		Retrieves the current default ACL access settings from the MQTT broker.

		:return: see "GETTER-functions return values in Class description"
		"""
		command = {'commands': [{'command': 'getDefaultACLAccess'}]}

		return self._execute_command(command)

	def create_client(
		self,
		username,
		password,
		clientid=None,
		textname=None,
		textdescription=None,
		groups=None,
		roles=None,
	):
		"""
		Creates a new client in the MQTT broker's dynamic security system
		with specified credentials, and optionally assigns it client ID, name, description, groups, and roles.

		:param username: Username for the new client.
		:param password: Password for the new client.
		:param clientid: Optional MQTT client ID. If not provided or empty, the client ID is not set.
		:param textname: Optional human-readable name for the client.
		:param textdescription: Optional description for the client.
		:param groups: Optional list of groups to assign the client to. Group must exist.
		:param roles: Optional list of roles to assign to the client. Role must exist.
		:return: see "SETTER-functions return values in Class description"
		"""
		command = {'commands': [{'command': 'createClient', 'username': username, 'password': password}]}

		# Add optional fields if provided
		if clientid is not None:
			command['commands'][0]['clientid'] = clientid
		if textname is not None:
			command['commands'][0]['textname'] = textname
		if textdescription is not None:
			command['commands'][0]['textdescription'] = textdescription
		if groups:
			command['commands'][0]['groups'] = [
				{'groupname': group['groupname'], 'priority': group['priority']} for group in groups
			]
		if roles:
			command['commands'][0]['roles'] = [
				{'rolename': role['rolename'], 'priority': role['priority']} for role in roles
			]

		return self._execute_command(command)

	def delete_client(self, username):
		"""
		Deletes an existing client from the MQTT broker's dynamic security system.

		:param username: The username of the client to delete.
		:return: see "SETTER-functions return values in Class description"
		"""
		command = {'commands': [{'command': 'deleteClient', 'username': username}]}

		return self._execute_command(command)

	def enable_client(self, username):
		"""
		Allow client to connect (default when new client is created).

		param username: The username of the client to enable.
		:return: see "SETTER-functions return values in Class description"

		"""
		command = {'commands': [{'command': 'enableClient', 'username': username}]}

		return self._execute_command(command)

	def disable_client(self, username):
		"""
		Stop a client from being able to log in, and kick any clients with
		matching username that are currently connected.

		param username: The username of the client to disable.
		:return: see "SETTER-functions return values in Class description"

		"""
		command = {'commands': [{'command': 'disableClient', 'username': username}]}

		return self._execute_command(command)

	def get_client(self, username):
		"""
		Retrieves information about a specific client from the MQTT broker's dynamic security system.

		:param username: The username of the client to retrieve information about.
		:return: see "GETTER-functions return values in Class description"
		"""
		command = {'commands': [{'command': 'getClient', 'username': username}]}

		return self._execute_command(command)

	def list_clients(self, verbose=False, count=-1, offset=0):
		"""
		Lists clients with options for verbosity, count, and offset.

		:param verbose: If True, returns detailed information about each client. If False, returns only usernames.
		:param count: The maximum number of clients to return. Set to -1 to return all clients.
		:param offset: The starting index from which to return clients.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    list_clients(verbose=True)
		"""
		command = {
			'commands': [
				{
					'command': 'listClients',
					'verbose': verbose,
					'count': count,
					'offset': offset,
				}
			]
		}

		return self._execute_command(command)

	def modify_client(
		self,
		username,
		clientid=None,
		password=None,
		textname=None,
		textdescription=None,
		roles=None,
		groups=None,
	):
		"""
		Updates the properties and permissions of an existing client in the MQTT broker's dynamic security system.

		:param username: The username of the client to modify.
		:param clientid: Optional new client ID for the client. If None, the client ID is not modified.
		:param password: Optional new password for the client. If None, the password is not modified.
		:param textname: Optional new human-readable name for the client.
		:param textdescription: Optional new description for the client.
		:param roles: Optional list of roles to assign to the client. Role: dictionary with 'rolename' and 'priority'.
		:param groups: Optional list of groups to add the client to. Group: dictionary with 'groupname' and 'priority'.
		:return: see "SETTER-functions return values in Class description"
		"""

		command = {'commands': [{'command': 'modifyClient', 'username': username}]}
		# Add optional fields if provided
		if clientid is not None:
			command['commands'][0]['clientid'] = clientid
		if password is not None:
			command['commands'][0]['password'] = password
		if textname is not None:
			command['commands'][0]['textname'] = textname
		if textdescription is not None:
			command['commands'][0]['textdescription'] = textdescription
		if roles:
			command['commands'][0]['roles'] = [
				{'rolename': role['rolename'], 'priority': role['priority']} for role in roles
			]
		if groups:
			command['commands'][0]['groups'] = [
				{'groupname': group['groupname'], 'priority': group['priority']} for group in groups
			]

		return self._execute_command(command)

	def set_client_id(self, username, clientid=''):
		"""
		Assigns or clears a client ID for a specific client in the MQTT broker's dynamic security system.

		:param username: The username of the client whose client ID is to be set or cleared.
		:param clientid: The new client ID to assign to the client. If empty string is provided, client's ID is cleared.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    # Assign a new client ID to a user
		    set_client_id("john_doe", "johns_device_123")

		    # Clear an existing client ID from a user
		    set_client_id("jane_doe", "")
		"""

		command = {'commands': [{'command': 'setClientId', 'username': username, 'clientid': clientid}]}

		return self._execute_command(command)

	def set_client_password(self, username, password):
		"""
		Updates the password for a specific client in the MQTT broker's dynamic security system.

		:param username: The username of the client whose password is to be updated.
		:param password: The new password for the client.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    # Change password for a user
		    set_client_password("john_doe", "new_secure_password")
		"""

		command = {
			'commands': [
				{
					'command': 'setClientPassword',
					'username': username,
					'password': password,
				}
			]
		}

		return self._execute_command(command)

	def add_client_role(self, username, rolename, priority=-1):
		"""
		Assigns a role to a specific client, optionally with a specified priority.

		:param username: The username of the client to which the role is to be assigned.
		:param rolename: The name of the role to assign to the client.
		:param priority: The priority of the role for this client. Defaults to -1, indicating lowest priority.
		:return: see "SETTER-functions return values in Class description"

		This method is useful for dynamically managing client permissions by
		assigning roles that define a set of access control lists (ACLs).

		Example:
		    # Assign a 'Publisher' role to 'jane_doe' with a higher priority
		    add_client_role("jane_doe", "Publisher", priority=10)
		"""

		command = {
			'commands': [
				{
					'command': 'addClientRole',
					'username': username,
					'rolename': rolename,
					'priority': priority,
				}
			]
		}

		return self._execute_command(command)

	def remove_client_role(self, username, rolename):
		"""
		Removes a previously assigned role from a specific client.

		:param username: The username of the client from which the role is to be removed.
		:param rolename: The name of the role to remove from the client.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    # Remove the 'Publisher' role from 'jane_doe'
		    remove_client_role("jane_doe", "Publisher")
		"""

		command = {
			'commands': [
				{
					'command': 'removeClientRole',
					'username': username,
					'rolename': rolename,
				}
			]
		}

		return self._execute_command(command)

	def add_group_client(self, groupname, username, priority=-1):
		"""
		Adds a client to a specified group with an optional priority level.

		:param groupname: The name of the group to which the client will be added.
		:param username: The username of the client to add to the group.
		:param priority: The priority of the client within the group. Defaults to -1 for lowest priority.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    # Add 'john_doe' to the 'Engineering' group with default priority
		    add_group_client("Engineering", "john_doe")
		"""

		command = {
			'commands': [
				{
					'command': 'addGroupClient',
					'groupname': groupname,
					'username': username,
					'priority': priority,
				}
			]
		}

		return self._execute_command(command)

	def create_group(self, groupname, roles=None):
		"""
		Creates a new group with the specified name and optionally assigns roles to it.

		:param groupname: The name of the group to be created.
		:param roles: A list of dictionaries, each representing a role to assign to the group.
		            Each dictionary in the list should have the following format:
		            {"rolename": "name_of_the_role", "priority": priority_value}
		            The "priority" is optional and defaults to -1 if not specified.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    create_group("EngineeringTeam", roles=[{"rolename": "Developer", "priority": 1},
		                                           {"rolename": "Reviewer", "priority": 2}])
		"""
		command = {'commands': [{'command': 'createGroup', 'groupname': groupname}]}
		if roles:
			command['commands'][0]['roles'] = [
				{'rolename': role['rolename'], 'priority': role['priority']} for role in roles
			]

		return self._execute_command(command)

	def delete_group(self, groupname):
		"""
		Deletes a group with the specified name.

		:param groupname: The name of the group to be deleted.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    delete_group("EngineeringTeam")
		"""
		command = {'commands': [{'command': 'deleteGroup', 'groupname': groupname}]}

		return self._execute_command(command)

	def get_group(self, groupname):
		"""
		Retrieves information about a specified group.

		:param groupname: The name of the group to retrieve information about.
		:return: see "GETTER-functions return values in Class description"

		Example:
		    get_group("EngineeringTeam")
		"""
		command = {'commands': [{'command': 'getGroup', 'groupname': groupname}]}

		return self._execute_command(command)

	def list_groups(self, verbose=False, count=-1, offset=0):
		"""
		Lists groups with options for verbosity, count, and offset.

		:param verbose: If True, returns detailed information about each group. If False, returns less detail.
		:param count: The maximum number of groups to return. Set to -1 to return all groups.
		:param offset: The starting index from which to return groups.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    list_groups(verbose=True, count=10, offset=0)
		"""
		command = {
			'commands': [
				{
					'command': 'listGroups',
					'verbose': verbose,
					'count': count,
					'offset': offset,
				}
			]
		}

		return self._execute_command(command)

	def modify_group(self, groupname, textname=None, textdescription=None, roles=None, clients=None):
		"""
		Modifies an existing group with new properties, roles, and clients.

		:param groupname: The name of the group to modify.
		:param textname: Optional new name for the group.
		:param textdescription: Optional new description for the group.
		:param roles: Optional list of roles to assign to the group. Role: dictionary with 'rolename' and 'priority'.
		:param clients: Optional list of clients to add to the group. Client: dictionary with 'username' and 'priority'.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    modify_group("EngineeringTeam", textname="New Engineering Team", textdescription="Updated description",
		                roles=[{"rolename": "LeadEngineer", "priority": 1}],
		                clients=[{"username": "engineer1", "priority": 1}])
		"""
		command = {'commands': [{'command': 'modifyGroup', 'groupname': groupname}]}
		if textname is not None:
			command['commands'][0]['textname'] = textname
		if textdescription is not None:
			command['commands'][0]['textdescription'] = textdescription
		if roles:
			command['commands'][0]['roles'] = [
				{'rolename': role['rolename'], 'priority': role['priority']} for role in roles
			]
		if clients:
			command['commands'][0]['clients'] = [
				{'username': client['username'], 'priority': client['priority']} for client in clients
			]

		return self._execute_command(command)

	def remove_group_client(self, groupname, username):
		"""
		Removes a client from a specified group.

		:param groupname: The name of the group from which the client should be removed.
		:param username: The username of the client to remove from the group.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    remove_group_client("EngineeringTeam", "engineer1")
		"""
		command = {
			'commands': [
				{
					'command': 'removeGroupClient',
					'groupname': groupname,
					'username': username,
				}
			]
		}

		return self._execute_command(command)

	def add_group_role(self, groupname, rolename, priority=-1):
		"""
		Adds a role to a specified group with an optional priority.

		:param groupname: The name of the group to which the role should be added.
		:param rolename: The name of the role to add to the group.
		:param priority: The priority of the role within the group. Defaults to -1.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    add_group_role("EngineeringTeam", "LeadEngineer", 1)
		"""
		command = {
			'commands': [
				{
					'command': 'addGroupRole',
					'groupname': groupname,
					'rolename': rolename,
					'priority': priority,
				}
			]
		}

		return self._execute_command(command)

	def remove_group_role(self, groupname, rolename):
		"""
		Removes a role from a specified group.

		:param groupname: The name of the group from which the role should be removed.
		:param rolename: The name of the role to remove from the group.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    remove_group_role("EngineeringTeam", "LeadEngineer")
		"""
		command = {
			'commands': [
				{
					'command': 'removeGroupRole',
					'groupname': groupname,
					'rolename': rolename,
				}
			]
		}

		return self._execute_command(command)

	def set_anonymous_group(self, groupname):
		"""
		Sets the specified group as the anonymous group. Anonymous clients will inherit the permissions of this group.

		:param groupname: The name of the group to set as the anonymous group.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    set_anonymous_group("AnonymousUsers")
		"""
		command = {'commands': [{'command': 'setAnonymousGroup', 'groupname': groupname}]}

		return self._execute_command(command)

	def get_anonymous_group(self):
		"""
		Retrieves the name of the group set as the anonymous group.

		:return: see "GETTER-functions return values in Class description"

		Example:
		    get_anonymous_group()
		"""
		command = {'commands': [{'command': 'getAnonymousGroup'}]}

		return self._execute_command(command)

	def create_role(self, rolename, textname=None, textdescription=None, acls=None):
		"""
		Creates a new role with an optional description, name, and set of ACLs.

		:param rolename: The name of the role to create.
		:param textname: Optional human-readable name for the role.
		:param textdescription: Optional description of the role.
		:param acls: Optional list of ACLs to assign to the role. Each ACL should be a dictionary
		            specifying 'acltype', 'topic', 'priority', and 'allow'.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    create_role("BasicSubscriber", textname="Subscriber Role", textdescription="Can subscribe to topics",
		                acls=[{"acltype": "subscribePattern", "topic": "topic/#", "priority": -1, "allow": True}])
		"""
		command = {'commands': [{'command': 'createRole', 'rolename': rolename}]}
		if textname is not None:
			command['commands'][0]['textname'] = textname
		if textdescription is not None:
			command['commands'][0]['textdescription'] = textdescription
		if acls:
			command['commands'][0]['acls'] = acls

		return self._execute_command(command)

	def get_role(self, rolename):
		"""
		Retrieves information about a specified role.

		:param rolename: The name of the role to retrieve information about.
		:return: see "GETTER-functions return values in Class description"

		Example:
		    get_role("BasicSubscriber")
		"""
		command = {'commands': [{'command': 'getRole', 'rolename': rolename}]}

		return self._execute_command(command)

	def list_roles(self, verbose=False, count=-1, offset=0):
		"""
		Lists roles with options for verbosity, count, and offset.

		:param verbose: If True, returns detailed information about each role. If False, returns role name only.
		:param count: The maximum number of roles to return. Set to -1 to return all roles.
		:param offset: The starting index from which to return roles.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    list_roles(verbose=True, count=10, offset=0)
		"""
		command = {
			'commands': [
				{
					'command': 'listRoles',
					'verbose': verbose,
					'count': count,
					'offset': offset,
				}
			]
		}

		return self._execute_command(command)

	def modify_role(self, rolename, textname=None, textdescription=None, acls=None):
		"""
		Modifies an existing role with new properties and/or a set of ACLs.

		:param rolename: The name of the role to modify.
		:param textname: Optional new name for the role.
		:param textdescription: Optional new description for the role.
		:param acls: Optional list of ACLs to assign to the role. Each ACL should be a dictionary
		            specifying 'acltype', 'topic', 'priority', and 'allow'.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    modify_role("BasicSubscriber", textname="Advanced Subscriber", textdescription="Subscribes to more topics",
		            acls=[{"acltype": "subscribePattern", "topic": "advanced/topic/#", "priority": -1, "allow": True}])
		"""
		command = {'commands': [{'command': 'modifyRole', 'rolename': rolename}]}
		if textname is not None:
			command['commands'][0]['textname'] = textname
		if textdescription is not None:
			command['commands'][0]['textdescription'] = textdescription
		if acls:
			command['commands'][0].setdefault('acls', []).extend(acls)

		return self._execute_command(command)

	def delete_role(self, rolename):
		"""
		Deletes a role with the specified name.

		:param rolename: The name of the role to be deleted.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    delete_role("BasicSubscriber")
		"""
		command = {'commands': [{'command': 'deleteRole', 'rolename': rolename}]}

		return self._execute_command(command)

	def add_role_acl(self, rolename, acltype, topic, priority=-1, allow=True):
		"""
		Adds an ACL to a specified role.

		:param rolename: The name of the role to add the ACL to.
		:param acltype: The type of ACL, e.g., "subscribePattern".
		:param topic: The MQTT topic pattern the ACL applies to.
		:param priority: The priority of the ACL within the role. Defaults to -1.
		:param allow: Whether the ACL allows (True) or denies (False) access. Defaults to True.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    add_role_acl("BasicSubscriber", "subscribePattern", "topic/#", -1, True)
		"""
		command = {
			'commands': [
				{
					'command': 'addRoleACL',
					'rolename': rolename,
					'acltype': acltype,
					'topic': topic,
					'priority': priority,
					'allow': allow,
				}
			]
		}

		return self._execute_command(command)

	def remove_role_acl(self, rolename, acltype, topic):
		"""
		Removes an ACL from a specified role.

		:param rolename: The name of the role to remove the ACL from.
		:param acltype: The type of ACL, e.g., "subscribePattern".
		:param topic: The MQTT topic pattern of the ACL to be removed.
		:return: see "SETTER-functions return values in Class description"

		Example:
		    remove_role_acl("BasicSubscriber", "subscribePattern", "topic/#")
		"""
		command = {
			'commands': [
				{
					'command': 'removeRoleACL',
					'rolename': rolename,
					'acltype': acltype,
					'topic': topic,
				}
			]
		}

		return self._execute_command(command)

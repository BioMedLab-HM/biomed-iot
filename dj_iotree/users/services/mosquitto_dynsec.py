import json
# import paho.mqtt.client as mqtt
import asyncio
import aiomqtt
from queue import Queue
import time

# TODO: docstrings vervollständigen/komprimieren, Returnwerte analysieren


class MosquittoDynSec:
    '''
    Based on commands at https://github.com/eclipse/mosquitto/blob/master/plugins/dynamic-security/README.md
    '''

    def __init__(self, username, password, host="localhost", port=1883, response_queue=None):
        """
        Initializes the MosquittoDynSec class with connection details to the MQTT broker.

        :param username: The username of the Client that writes to the topic '$CONTROL/dynamic-security/v1'
        :param password: The password of the Client that writes to the topic '$CONTROL/dynamic-security/v1'
        :param host: The hostname or IP address of the MQTT broker. Defaults to "localhost".
        :param port: The network port of the MQTT server. Defaults to 1883.
        
        Upon initialization, this method creates an MQTT client, sets up authentication if username
        and password are provided, and establishes a connection to the MQTT broker. The on_response callback 
        needs to be implemented by the caller. The callback passes the received mqtt response to the caller.
        """
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        # self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        # Assign callbacks
        # self.client.on_connect = self.on_connect
        # self.client.on_message = self.on_message

        #self.on_response = on_response  # Callback function to pass the response to the caller
        self.response_queue = response_queue

        # Set up authentication if username and password are provided
        # if username and password:
        #     self.client.username_pw_set(username, password)

        # Connect to the MQTT broker
        # self.client.connect(host, port, 60)
        # self.client.loop_start()

    # def on_connect(self, client, userdata, flags, rc, properties):
    #     # Subscribe to the response topic
    #     self.client.subscribe("$CONTROL/dynamic-security/v1/response", qos=2)
    #     print(f"Paho Client Return code: {rc}\n", )

    # def on_message(self, client, userdata, msg):
    #     try:
    #         #print(f"Response01: {msg.topic} {message.payload.decode('utf-8')}\n")
    #         # Handle the message, possibly decoding JSON
    #         response = json.loads(message.payload.decode('utf-8'))
    #         #print(f"{response}\n")
    #         # if self.on_response is not None:
    #         #     self.on_response(response)
    #         if self.response_queue is not None:
    #             self.response_queue.put(response)
    #     except Exception as e:
    #         print(f"Error handling message: {e}")
        

    async def _send_command(self, command):
        # Construct and send a command to the control topic
        topic = "$CONTROL/dynamic-security/v1"
        payload = json.dumps(command)
        async with aiomqtt.Client(self.hostname, self.port, self.username, self.password, keepalive=60) as client:
            await client.subscribe("$CONTROL/dynamic-security/v1/#")
            async for message in client.messages:
                print(message.payload)
                return json.loads(message.payload.decode('utf-8'))
            await client.publish(topic, payload)

        # success = self.client.publish(topic, payload)
        # return await success  # success code: "MQTT_ERR_SUCCESS". For list of codes see: https://github.com/eclipse/paho.mqtt.python/blob/master/src/paho/mqtt/client.py

    async def set_default_acl_access(self, publish_client_send_allow, publish_client_receive_allow, subscribe_allow, unsubscribe_allow):
        """
        Configures default ACL permissions for MQTT clients.

        :param publish_client_send_allow: Allow clients to publish messages (True/False).
        :param publish_client_receive_allow: Allow clients to receive messages (True/False).
        :param subscribe_allow: Allow clients to subscribe to topics (True/False).
        :param unsubscribe_allow: Allow clients to unsubscribe from topics (True/False).
        :return: Result of the command operation.

        Sets the default actions clients can perform if no specific ACLs apply.
        """
        command = {
            "commands": [
                {
                    "command": "setDefaultACLAccess",
                    "acls": [
                        {"acltype": "publishClientSend", "allow": publish_client_send_allow},
                        {"acltype": "publishClientReceive", "allow": publish_client_receive_allow},
                        {"acltype": "subscribe", "allow": subscribe_allow},
                        {"acltype": "unsubscribe", "allow": unsubscribe_allow}
                    ]
                }
            ]
        }
        return await self._send_command(command)

    async def  get_default_acl_access(self):
        """
    Retrieves the current default ACL access settings from the MQTT broker.

    :return: The default ACL access configuration as set in the MQTT broker.
    """
        command = {
            "commands": [
                {
                    "command": "getDefaultACLAccess"
                }
            ]
        }
        return await self._send_command(command)

    async def  create_client(self, username, password, clientid=None, textname=None, textdescription=None, groups=None, roles=None):
        """
        Creates a new client in the MQTT broker's dynamic security system 
        with specified credentials, and optionally assigns it client ID, name, description, groups, and roles.

        :param username: Username for the new client.
        :param password: Password for the new client.
        :param clientid: Optional MQTT client ID. If not provided or empty, the client ID is not set.
        :param textname: Optional human-readable name for the client.
        :param textdescription: Optional description for the client.
        :param groups: Optional list of groups to assign the client to, each a dict with 'groupname' and 'priority'.
        :param roles: Optional list of roles to assign to the client, each a dict with 'rolename' and 'priority'.
        :return: Result of the operation.
        """
        command = {
            "commands": [
                {
                    "command": "createClient",
                    "username": username,
                    "password": password
                }
            ]
        }

        # Add optional fields if provided
        if clientid is not None:
            command["commands"][0]["clientid"] = clientid
        if textname is not None:
            command["commands"][0]["textname"] = textname
        if textdescription is not None:
            command["commands"][0]["textdescription"] = textdescription
        if groups:
            command["commands"][0]["groups"] = [{"groupname": group["groupname"], "priority": group["priority"]} for group in groups]
        if roles:
            command["commands"][0]["roles"] = [{"rolename": role["rolename"], "priority": role["priority"]} for role in roles]

        return await self._send_command(command)
    
    async def  delete_client(self, username):
        """
        Deletes an existing client from the MQTT broker's dynamic security system.

        :param username: The username of the client to delete.
        :return: Result of the operation.
        """
        command = {
            "commands": [
                {
                    "command": "deleteClient",
                    "username": username
                }
            ]
        }
        return await self._send_command(command)

    async def  enable_client(self, username):
        """
        Allow client to connect (default when new client is created).

        param username: The username of the client to enable.
        :return: Result of the operation. Success indicates the client was enabled.

        """
        command = {
            "commands": [
                {
                    "command": "enableClient",
                    "username": username
                }
            ]
        }
        return await self._send_command(command)

    async def  disable_client(self, username):
        """
        Stop a client from being able to log in, and kick any clients with matching username that are currently connected.

        param username: The username of the client to disable.
        :return: Result of the operation. Success indicates the client was disabled and any active connections were terminated.

        """
        command = {
            "commands": [
                {
                    "command": "disableClient",
                    "username": username
                }
            ]
        }
        return await self._send_command(command)

    async def  get_client(self, username):
        """
        Retrieves information about a specific client from the MQTT broker's dynamic security system.

        :param username: The username of the client to retrieve information about.
        :return: A dictionary containing the client's details, including username, client ID, status, and associated roles and groups, based on the MQTT broker's response.
        """
        command = {
            "commands": [
                {
                    "command": "getClient",
                    "username": username
                }
            ]
        }
        return await self._send_command(command)

    async def  list_clients(self, verbose=False, count=-1, offset=0):
        """
        Lists clients with options for verbosity, count, and offset.

        :param verbose: If True, returns detailed information about each client. If False, returns less detail.
        :param count: The maximum number of clients to return. Set to -1 to return all clients.
        :param offset: The starting index from which to return clients.
        :return: The result of the command sent to the MQTT broker, typically including
                a list of clients and possibly their details based on the verbosity.

        Example:
            list_clients(verbose=True, count=10, offset=0)
        """
        command = {
            "commands": [
                {
                    "command": "listClients",
                    "verbose": verbose,
                    "count": count,
                    "offset": offset
                }
            ]
        }
        return await self._send_command(command)

    async def  modify_client(self, username, clientid=None, password=None, textname=None, textdescription=None, roles=None, groups=None):
        """
        Updates the properties and permissions of an existing client in the MQTT broker's dynamic security system.

        :param username: The username of the client to modify.
        :param clientid: Optional new client ID for the client. If None, the client ID is not modified.
        :param password: Optional new password for the client. If None, the password is not modified.
        :param textname: Optional new human-readable name for the client.
        :param textdescription: Optional new description for the client.
        :param roles: Optional list of roles to assign to the client. Each role should be specified as a dictionary with 'rolename' and 'priority'.
        :param groups: Optional list of groups to add the client to. Each group should be specified as a dictionary with 'groupname' and 'priority'.
        :return: Result of the operation, indicating success or failure.
        """

        command = {
            "commands": [
                {
                    "command": "modifyClient",
                    "username": username
                }
            ]
        }
        # Add optional fields if provided
        if clientid is not None:
            command["commands"][0]["clientid"] = clientid
        if password is not None:
            command["commands"][0]["password"] = password
        if textname is not None:
            command["commands"][0]["textname"] = textname
        if textdescription is not None:
            command["commands"][0]["textdescription"] = textdescription
        if roles:
            command["commands"][0]["roles"] = [{"rolename": role["rolename"], "priority": role["priority"]} for role in roles]
        if groups:
            command["commands"][0]["groups"] = [{"groupname": group["groupname"], "priority": group["priority"]} for group in groups]

        return await self._send_command(command)

    async def  set_client_id(self, username, clientid=""):
        """
        Assigns or clears a client ID for a specific client in the MQTT broker's dynamic security system.

        :param username: The username of the client whose client ID is to be set or cleared.
        :param clientid: The new client ID to assign to the client. If an empty string is provided, the client's ID is cleared.
        :return: Result of the operation, indicating success or failure.

        Example:
            # Assign a new client ID to a user
            set_client_id("john_doe", "johns_device_123")
            
            # Clear an existing client ID from a user
            set_client_id("jane_doe", "")
        """

        command = {
            "commands": [
                {
                    "command": "setClientId",
                    "username": username,
                    "clientid": clientid
                }
            ]
        }
        return await self._send_command(command)

    async def  set_client_password(self, username, password):
        """
        Updates the password for a specific client in the MQTT broker's dynamic security system.

        :param username: The username of the client whose password is to be updated.
        :param password: The new password for the client.
        :return: Result of the operation, indicating success or failure.

        Example:
            # Change password for a user
            set_client_password("john_doe", "new_secure_password")
        """

        command = {
            "commands": [
                {
                    "command": "setClientPassword",
                    "username": username,
                    "password": password
                }
            ]
        }
        return await self._send_command(command)

    async def  add_client_role(self, username, rolename, priority=-1):
        """
        Assigns a role to a specific client, optionally with a specified priority.

        :param username: The username of the client to which the role is to be assigned.
        :param rolename: The name of the role to assign to the client.
        :param priority: The priority of the role for this client. Defaults to -1, indicating lowest priority.
        :return: Result of the operation, indicating success or failure.

        This method is useful for dynamically managing client permissions by assigning roles that define a set of access control lists (ACLs).

        Example:            
            # Assign a 'Publisher' role to 'jane_doe' with a higher priority
            add_client_role("jane_doe", "Publisher", priority=10)
        """

        command = {
            "commands": [
                {
                    "command": "addClientRole",
                    "username": username,
                    "rolename": rolename,
                    "priority": priority
                }
            ]
        }
        return await self._send_command(command)

    async def  remove_client_role(self, username, rolename):
        """
        Removes a previously assigned role from a specific client.

        :param username: The username of the client from which the role is to be removed.
        :param rolename: The name of the role to remove from the client.
        :return: Result of the operation, indicating success or failure.

        Example:
            # Remove the 'Publisher' role from 'jane_doe'
            remove_client_role("jane_doe", "Publisher")
        """

        command = {
            "commands": [
                {
                    "command": "removeClientRole",
                    "username": username,
                    "rolename": rolename
                }
            ]
        }
        return await self._send_command(command)

    async def  add_group_client(self, groupname, username, priority=-1):
        """
        Adds a client to a specified group with an optional priority level.

        :param groupname: The name of the group to which the client will be added.
        :param username: The username of the client to add to the group.
        :param priority: The priority of the client within the group. Defaults to -1 for lowest priority.
        :return: Result of the operation, indicating success or failure.

        Example:
            # Add 'john_doe' to the 'Engineering' group with default priority
            add_group_client("Engineering", "john_doe")
        """

        command = {
            "commands": [
                {
                    "command": "addGroupClient",
                    "groupname": groupname,
                    "username": username,
                    "priority": priority
                }
            ]
        }
        return await self._send_command(command)

    async def  create_group(self, groupname, roles=None):
        """
        Creates a new group with the specified name and optionally assigns roles to it.

        :param groupname: The name of the group to be created.
        :param roles: A list of dictionaries, each representing a role to assign to the group.
                    Each dictionary in the list should have the following format:
                    {"rolename": "name_of_the_role", "priority": priority_value}
                    The "priority" is optional and defaults to -1 if not specified.
        :return: The result of the command sent to the MQTT broker.

        Example:
            create_group("EngineeringTeam", roles=[{"rolename": "Developer", "priority": 1},
                                                   {"rolename": "Reviewer", "priority": 2}])
        """
        command = {
            "commands": [
                {
                    "command": "createGroup",
                    "groupname": groupname
                }
            ]
        }
        if roles:
            command["commands"][0]["roles"] = [{"rolename": role["rolename"], "priority": role["priority"]} for role in roles]

        return await self._send_command(command)

    async def  delete_group(self, groupname):
        """
        Deletes a group with the specified name.

        :param groupname: The name of the group to be deleted.
        :return: The result of the command sent to the MQTT broker.

        Example:
            delete_group("EngineeringTeam")
        """
        command = {
            "commands": [
                {
                    "command": "deleteGroup",
                    "groupname": groupname
                }
            ]
        }
        return await self._send_command(command)

    async def  get_group(self, groupname):
        """
        Retrieves information about a specified group.

        :param groupname: The name of the group to retrieve information about.
        :return: The result of the command sent to the MQTT broker, typically including
                the group's details such as assigned roles and members.

        Example:
            get_group("EngineeringTeam")
        """
        command = {
            "commands": [
                {
                    "command": "getGroup",
                    "groupname": groupname
                }
            ]
        }
        return await self._send_command(command)

    async def  list_groups(self, verbose=False, count=-1, offset=0):
        """
        Lists groups with options for verbosity, count, and offset.

        :param verbose: If True, returns detailed information about each group. If False, returns less detail.
        :param count: The maximum number of groups to return. Set to -1 to return all groups.
        :param offset: The starting index from which to return groups.
        :return: The result of the command sent to the MQTT broker, typically including
                a list of groups and possibly their details based on the verbosity.

        Example:
            list_groups(verbose=True, count=10, offset=0)
        """
        command = {
            "commands": [
                {
                    "command": "listGroups",
                    "verbose": verbose,
                    "count": count,
                    "offset": offset
                }
            ]
        }
        return await self._send_command(command)

    async def  modify_group(self, groupname, textname=None, textdescription=None, roles=None, clients=None):
        """
        Modifies an existing group with new properties, roles, and clients.

        :param groupname: The name of the group to modify.
        :param textname: Optional new name for the group.
        :param textdescription: Optional new description for the group.
        :param roles: Optional list of roles to assign to the group, each as a dictionary with 'rolename' and 'priority'.
        :param clients: Optional list of clients to add to the group, each as a dictionary with 'username' and 'priority'.
        :return: The result of the command sent to the MQTT broker.

        Example:
            modify_group("EngineeringTeam", textname="New Engineering Team", textdescription="Updated description",
                        roles=[{"rolename": "LeadEngineer", "priority": 1}],
                        clients=[{"username": "engineer1", "priority": 1}])
        """
        command = {
            "commands": [
                {
                    "command": "modifyGroup",
                    "groupname": groupname
                }
            ]
        }
        if textname is not None:
            command["commands"][0]["textname"] = textname
        if textdescription is not None:
            command["commands"][0]["textdescription"] = textdescription
        if roles:
            command["commands"][0]["roles"] = [{"rolename": role["rolename"], "priority": role["priority"]} for role in roles]
        if clients:
            command["commands"][0]["clients"] = [{"username": client["username"], "priority": client["priority"]} for client in clients]

        return await self._send_command(command)

    async def  remove_group_client(self, groupname, username):
        """
        Removes a client from a specified group.

        :param groupname: The name of the group from which the client should be removed.
        :param username: The username of the client to remove from the group.
        :return: The result of the command sent to the MQTT broker.

        Example:
            remove_group_client("EngineeringTeam", "engineer1")
        """
        command = {
            "commands": [
                {
                    "command": "removeGroupClient",
                    "groupname": groupname,
                    "username": username
                }
            ]
        }
        return await self._send_command(command)

    async def  add_group_role(self, groupname, rolename, priority=-1):
        """
        Adds a role to a specified group with an optional priority.

        :param groupname: The name of the group to which the role should be added.
        :param rolename: The name of the role to add to the group.
        :param priority: The priority of the role within the group. Defaults to -1.
        :return: The result of the command sent to the MQTT broker.

        Example:
            add_group_role("EngineeringTeam", "LeadEngineer", 1)
        """
        command = {
            "commands": [
                {
                    "command": "addGroupRole",
                    "groupname": groupname,
                    "rolename": rolename,
                    "priority": priority
                }
            ]
        }
        return await self._send_command(command)

    async def  remove_group_role(self, groupname, rolename):
        """
        Removes a role from a specified group.

        :param groupname: The name of the group from which the role should be removed.
        :param rolename: The name of the role to remove from the group.
        :return: The result of the command sent to the MQTT broker.

        Example:
            remove_group_role("EngineeringTeam", "LeadEngineer")
        """
        command = {
            "commands": [
                {
                    "command": "removeGroupRole",
                    "groupname": groupname,
                    "rolename": rolename
                }
            ]
        }
        return await self._send_command(command)

    async def  set_anonymous_group(self, groupname):
        """
        Sets the specified group as the anonymous group. Anonymous clients will inherit the permissions of this group.

        :param groupname: The name of the group to set as the anonymous group.
        :return: The result of the command sent to the MQTT broker.

        Example:
            set_anonymous_group("AnonymousUsers")
        """
        command = {
            "commands": [
                {
                    "command": "setAnonymousGroup",
                    "groupname": groupname
                }
            ]
        }
        return await self._send_command(command)

    async def  get_anonymous_group(self):
        """
        Retrieves the name of the group set as the anonymous group.

        :return: The result of the command sent to the MQTT broker, typically including
                the name of the group set as the anonymous group.

        Example:
            get_anonymous_group()
        """
        command = {
            "commands": [
                {
                    "command": "getAnonymousGroup"
                }
            ]
        }
        return await self._send_command(command)

    async def  create_role(self, rolename, textname=None, textdescription=None, acls=None):
        """
        Creates a new role with an optional description, name, and set of ACLs.

        :param rolename: The name of the role to create.
        :param textname: Optional human-readable name for the role.
        :param textdescription: Optional description of the role.
        :param acls: Optional list of ACLs to assign to the role. Each ACL should be a dictionary
                    specifying 'acltype', 'topic', 'priority', and 'allow'.
        :return: The result of the command sent to the MQTT broker.

        Example:
            create_role("BasicSubscriber", textname="Subscriber Role", textdescription="Can subscribe to topics",
                        acls=[{"acltype": "subscribePattern", "topic": "topic/#", "priority": -1, "allow": True}])
        """
        command = {
            "commands": [
                {
                    "command": "createRole",
                    "rolename": rolename
                }
            ]
        }
        if textname is not None:
            command["commands"][0]["textname"] = textname
        if textdescription is not None:
            command["commands"][0]["textdescription"] = textdescription
        if acls:
            command["commands"][0]["acls"] = acls

        return await self._send_command(command)

    async def  get_role(self, rolename):
        """
        Retrieves information about a specified role.

        :param rolename: The name of the role to retrieve information about.
        :return: The result of the command sent to the MQTT broker, typically including
                the details of the specified role.

        Example:
            get_role("BasicSubscriber")
        """
        command = {
            "commands": [
                {
                    "command": "getRole",
                    "rolename": rolename
                }
            ]
        }
        return await self._send_command(command)

    async def  list_roles(self, verbose=False, count=-1, offset=0):
        """
        Lists roles with options for verbosity, count, and offset.

        :param verbose: If True, returns detailed information about each role. If False, returns less detail.
        :param count: The maximum number of roles to return. Set to -1 to return all roles.
        :param offset: The starting index from which to return roles.
        :return: The result of the command sent to the MQTT broker, typically including
                a list of roles and possibly their details based on the verbosity.

        Example:
            list_roles(verbose=True, count=10, offset=0)
        """
        command = {
            "commands": [
                {
                    "command": "listRoles",
                    "verbose": verbose,
                    "count": count,
                    "offset": offset
                }
            ]
        }
        return await self._send_command(command)

    async def  modify_role(self, rolename, textname=None, textdescription=None, acls=None):
        """
        Modifies an existing role with new properties and/or a set of ACLs.

        :param rolename: The name of the role to modify.
        :param textname: Optional new name for the role.
        :param textdescription: Optional new description for the role.
        :param acls: Optional list of ACLs to assign to the role. Each ACL should be a dictionary
                    specifying 'acltype', 'topic', 'priority', and 'allow'.
        :return: The result of the command sent to the MQTT broker.

        Example:
            modify_role("BasicSubscriber", textname="Advanced Subscriber", textdescription="Can subscribe to more topics",
                        acls=[{"acltype": "subscribePattern", "topic": "advanced/topic/#", "priority": -1, "allow": True}])
        """
        command = {
            "commands": [
                {
                    "command": "modifyRole",
                    "rolename": rolename
                }
            ]
        }
        if textname is not None:
            command["commands"][0]["textname"] = textname
        if textdescription is not None:
            command["commands"][0]["textdescription"] = textdescription
        if acls:
            command["commands"][0].setdefault("acls", []).extend(acls)

        return await self._send_command(command)

    async def  delete_role(self, rolename):
        """
        Deletes a role with the specified name.

        :param rolename: The name of the role to be deleted.
        :return: The result of the command sent to the MQTT broker.

        Example:
            delete_role("BasicSubscriber")
        """
        command = {
            "commands": [
                {
                    "command": "deleteRole",
                    "rolename": rolename
                }
            ]
        }
        return await self._send_command(command)

    async def  add_role_acl(self, rolename, acltype, topic, priority=-1, allow=True):
        """
        Adds an ACL to a specified role.

        :param rolename: The name of the role to add the ACL to.
        :param acltype: The type of ACL, e.g., "subscribePattern".
        :param topic: The MQTT topic pattern the ACL applies to.
        :param priority: The priority of the ACL within the role. Defaults to -1.
        :param allow: Whether the ACL allows (True) or denies (False) access. Defaults to True.
        :return: The result of the command sent to the MQTT broker.

        Example:
            add_role_acl("BasicSubscriber", "subscribePattern", "topic/#", -1, True)
        """
        command = {
            "commands": [
                {
                    "command": "addRoleACL",
                    "rolename": rolename,
                    "acltype": acltype,
                    "topic": topic,
                    "priority": priority,
                    "allow": allow
                }
            ]
        }
        return await self._send_command(command)

    async def  remove_role_acl(self, rolename, acltype, topic):
        """
        Removes an ACL from a specified role.

        :param rolename: The name of the role to remove the ACL from.
        :param acltype: The type of ACL, e.g., "subscribePattern".
        :param topic: The MQTT topic pattern of the ACL to be removed.
        :return: The result of the command sent to the MQTT broker.

        Example:
            remove_role_acl("BasicSubscriber", "subscribePattern", "topic/#")
        """
        command = {
            "commands": [
                {
                    "command": "removeRoleACL",
                    "rolename": rolename,
                    "acltype": acltype,
                    "topic": topic
                }
            ]
        }
        return await self._send_command(command)

    def __del__(self):
        pass
        # Clean up and disconnect
        # self.client.loop_stop()
        # self.client.disconnect()

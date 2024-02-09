import json
import paho.mqtt.client as mqtt

class MosquittoDynSec:
    '''Based on commands at https://github.com/eclipse/mosquitto/blob/master/plugins/dynamic-security/README.md'''

    def __init__(self, username, password, host="localhost", port=1883):
        """
        Initializes the MosquittoDynSec class with connection details to the MQTT broker.

        :param username: The username of the Client that writes to the topic '$CONTROL/dynamic-security/v1'
        :param password: The password of the Client that writes to the topic '$CONTROL/dynamic-security/v1'
        :param host: The hostname or IP address of the MQTT broker. Defaults to "localhost".
        :param port: The network port of the MQTT server. Defaults to 1883.
        
        Upon initialization, this method creates an MQTT client, sets up authentication if username
        and password are provided, and establishes a connection to the MQTT broker.
        """
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.client = mqtt.Client()
        if username and password:
            self.client.username_pw_set(username, password)

        # Connect to the MQTT broker
        self.client.connect(host, port, 60)
        self.client.loop_start()

    def _send_command(self, command):
        # Construct and send a command to the control topic
        topic = "$CONTROL/dynamic-security/v1"
        payload = json.dumps(command)
        result = self.client.publish(topic, payload)
        return result

    def set_default_acl_access(self, publish_client_send_allow, publish_client_receive_allow, subscribe_allow, unsubscribe_allow):
        """
        Sets the default ACL access for the MQTT broker.

        This method configures the default access control list (ACL) settings for clients connecting
        to the MQTT broker. It determines what actions (publishing or subscribing) are allowed or
        denied by default if no specific ACL rules match a client's request.

        :param publish_client_send_allow: A boolean indicating whether clients are allowed to publish
                                        messages by default (True) or not (False).
        :param publish_client_receive_allow: A boolean indicating whether clients are allowed to receive
                                            published messages by default (True) or not (False).
        :param subscribe_allow: A boolean indicating whether clients are allowed to subscribe to topics
                                by default (True) or not (False).
        :param unsubscribe_allow: A boolean indicating whether clients are allowed to unsubscribe from
                                topics by default (True) or not (False).
        :return: The result of sending the command to the MQTT broker, typically indicating success or
                failure of the operation.

        Example:
            set_default_acl_access(True, False, True, False)
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
        return self._send_command(command)

    def get_default_acl_access(self):
        command = {
            "commands": [
                {
                    "command": "getDefaultACLAccess"
                }
            ]
        }
        return self._send_command(command)

    def create_client(self, username, password, clientid=None, textname=None, textdescription=None, groups=None, roles=None):
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

        return self._send_command(command)
    
    def delete_client(self, username):
        command = {
            "commands": [
                {
                    "command": "deleteClient",
                    "username": username
                }
            ]
        }
        return self._send_command(command)

    def enable_client(self, username):
        command = {
            "commands": [
                {
                    "command": "enableClient",
                    "username": username
                }
            ]
        }
        return self._send_command(command)

    def disable_client(self, username):
        command = {
            "commands": [
                {
                    "command": "disableClient",
                    "username": username
                }
            ]
        }
        return self._send_command(command)

    def get_client(self, username):
        command = {
            "commands": [
                {
                    "command": "getClient",
                    "username": username
                }
            ]
        }
        return self._send_command(command)

    def list_clients(self, verbose=False, count=-1, offset=0):
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
        return self._send_command(command)

    def modify_client(self, username, clientid=None, password=None, textname=None, textdescription=None, roles=None, groups=None):
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

        return self._send_command(command)

    def set_client_id(self, username, clientid=""):
        command = {
            "commands": [
                {
                    "command": "setClientId",
                    "username": username,
                    "clientid": clientid
                }
            ]
        }
        return self._send_command(command)

    def set_client_password(self, username, password):
        command = {
            "commands": [
                {
                    "command": "setClientPassword",
                    "username": username,
                    "password": password
                }
            ]
        }
        return self._send_command(command)

    def add_client_role(self, username, rolename, priority=-1):
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
        return self._send_command(command)

    def remove_client_role(self, username, rolename):
        command = {
            "commands": [
                {
                    "command": "removeClientRole",
                    "username": username,
                    "rolename": rolename
                }
            ]
        }
        return self._send_command(command)

    def add_group_client(self, groupname, username, priority=-1):
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
        return self._send_command(command)

    def create_group(self, groupname, roles=None):
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

        return self._send_command(command)

    def delete_group(self, groupname):
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
        return self._send_command(command)

    def get_group(self, groupname):
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
        return self._send_command(command)

    def list_groups(self, verbose=False, count=-1, offset=0):
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
        return self._send_command(command)

    def modify_group(self, groupname, textname=None, textdescription=None, roles=None, clients=None):
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

        return self._send_command(command)

    def remove_group_client(self, groupname, username):
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
        return self._send_command(command)

    def add_group_role(self, groupname, rolename, priority=-1):
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
        return self._send_command(command)

    def remove_group_role(self, groupname, rolename):
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
        return self._send_command(command)

    def set_anonymous_group(self, groupname):
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
        return self._send_command(command)

    def get_anonymous_group(self):
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
        return self._send_command(command)

    def create_role(self, rolename, textname=None, textdescription=None, acls=None):
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

        return self._send_command(command)

    def get_role(self, rolename):
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
        return self._send_command(command)

    def list_roles(self, verbose=False, count=-1, offset=0):
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
        return self._send_command(command)

    def modify_role(self, rolename, textname=None, textdescription=None, acls=None):
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

        return self._send_command(command)

    def delete_role(self, rolename):
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
        return self._send_command(command)

    def add_role_acl(self, rolename, acltype, topic, priority=-1, allow=True):
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
        return self._send_command(command)

    def remove_role_acl(self, rolename, acltype, topic):
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
        return self._send_command(command)

    def __del__(self):
        # Clean up and disconnect
        self.client.loop_stop()
        self.client.disconnect()

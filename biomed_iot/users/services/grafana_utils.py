import json
import requests
import logging
from biomed_iot.config_loader import config

logger = logging.getLogger(__name__)


class GrafanaUserManager:
    def __init__(self, user):
        self.username = user.username
        self.user_pword = user.password
        self.user_email = user.email
        self.influx_token = user.influxuserdata.bucket_token
        self.influx_bucket_name = user.influxuserdata.bucket_name
        self.influx_org_name = config.influxdb.INFLUX_ORG_NAME
        self.influx_host = config.influxdb.INFLUX_HOST
        self.influx_port = config.influxdb.INFLUX_PORT
        self.hostname = config.grafana.GRAFANA_HOST
        self.port = config.grafana.GRAFANA_PORT
        self.admin_username = config.grafana.GRAFANA_ADMIN_USERNAME
        self.admin_password = config.grafana.GRAFANA_ADMIN_PASSWORD
        # All Grafana API calls are made with admin credentials.
        self.grafana_origin = f"http://{self.admin_username}:{self.admin_password}@{self.hostname}:{self.port}"

    def _make_org(self):
        payload = {"name": self.username}
        url = f"{self.grafana_origin}/api/orgs"
        headers = {'content-type': 'application/json'}
        return requests.post(url, data=json.dumps(payload), headers=headers)

    def _get_org_id(self):
        url = f"{self.grafana_origin}/api/orgs/name/{self.username}"
        headers = {'content-type': 'application/json'}
        r = requests.get(url, headers=headers)
        try:
            content = r.json()
            return content.get("id")
        except Exception as e:
            logger.error(f"Error parsing organization ID: {e}")
        return None

    def _switch_org(self, orgid):
        url = f"{self.grafana_origin}/api/user/using/{orgid}"
        headers = {'content-type': 'application/json'}
        return requests.post(url, headers=headers)

    def _switch_org_main(self):
        # Switch to the default admin organization (org id 1)
        url = f"{self.grafana_origin}/api/user/using/1"
        headers = {'content-type': 'application/json'}
        return requests.post(url, headers=headers)

    def _make_user(self):
        payload = {
            "name": self.username,
            "email": self.user_email,
            "login": self.username,
            "password": self.user_pword
        }
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users"
        return requests.post(url, data=json.dumps(payload), headers=headers)

    def _add_user_to_org(self, orgid):
        # Adds the custom user to their own organization.
        payload = {"role": "Editor", "loginOrEmail": self.username}
        url = f"{self.grafana_origin}/api/orgs/{orgid}/users"
        headers = {'content-type': 'application/json'}
        return requests.post(url, data=json.dumps(payload), headers=headers)

    def _add_data_sources(self):
        common_secure_json_data = {
            "httpHeaderValue1": f"Token {self.influx_token}",
            "token": self.influx_token
        }
        common_json_data = {
            "httpMode": "GET",
            "httpHeaderName1": "Authorization",
            "organization": self.influx_org_name
        }
        influxql_payload = {
            "access": "proxy",
            "database": self.influx_bucket_name,
            "name": self.username,
            "type": "influxdb",
            "url": f"http://{self.influx_host}:{self.influx_port}",
            "secureJsonData": common_secure_json_data,
            "jsonData": {**common_json_data, "version": "InfluxQL"},
            "isDefault": True,
            "version": 1,
            "readOnly": False
        }
        flux_payload = {
            "access": "proxy",
            "database": self.influx_bucket_name,
            "name": f"{self.username}Flux",
            "type": "influxdb",
            "url": f"http://{self.influx_host}:{self.influx_port}",
            "secureJsonData": common_secure_json_data,
            "jsonData": {**common_json_data, "version": "Flux", "httpMode": "POST"},
            "isDefault": False,
            "version": 1,
            "readOnly": False
        }
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/datasources"
        response1 = requests.post(url, data=json.dumps(influxql_payload), headers=headers)
        response2 = requests.post(url, data=json.dumps(flux_payload), headers=headers)
        return response1, response2

    def _switch_user_org(self, userid, orgid):
        url = f"{self.grafana_origin}/api/users/{userid}/using/{orgid}"
        headers = {'content-type': 'application/json'}
        return requests.post(url, headers=headers)

    def _remove_user_from_main_org(self, userid):
        # Removes the custom user from the default organization (org id 1)
        url = f"{self.grafana_origin}/api/orgs/1/users/{userid}"
        headers = {'content-type': 'application/json'}
        return requests.delete(url, headers=headers)

    def _get_user_id(self):
        url = f"{self.grafana_origin}/api/users/lookup?loginOrEmail={self.username}"
        headers = {'content-type': 'application/json'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                content = response.json()
                return content.get('id')
            except Exception as e:
                logger.error(f"Error parsing user ID: {e}")
        else:
            logger.error(f"Error getting user ID: {response.status_code} {response.text}")
        return None

    def _del_user(self, userid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users/{userid}"
        return requests.delete(url, headers=headers)

    def _del_org(self, orgid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/orgs/{orgid}"
        return requests.delete(url, headers=headers)

    def create_user(self):
        # Create the custom organization for the user.
        org_resp = self._make_org()
        if org_resp.status_code not in [200, 204]:
            logger.error(f"Failed to create org: {org_resp.status_code} {org_resp.text}")
            return False

        orgid = self._get_org_id()
        if not orgid:
            logger.error("Organization ID not retrieved after org creation.")
            return False

        # Switch to the newly created organization.
        switch_resp = self._switch_org(orgid)
        if switch_resp.status_code not in [200, 204]:
            logger.error(f"Failed to switch to user org: {switch_resp.status_code} {switch_resp.text}")
            return False

        # Create the custom user account.
        user_resp = self._make_user()
        if user_resp.status_code not in [200, 204]:
            logger.error(f"Failed to create user: {user_resp.status_code} {user_resp.text}")
            return False

        # Add the user to their own organization.
        add_resp = self._add_user_to_org(orgid)
        if add_resp.status_code not in [200, 204]:
            logger.error(f"Failed to add user to org: {add_resp.status_code} {add_resp.text}")
            return False

        # Add data sources for the user.
        self._add_data_sources()

        userid = self._get_user_id()
        if userid:
            # Switch the user's context to the custom organization.
            self._switch_user_org(userid, orgid)
            # Remove the custom user from the main org (org id 1).
            self._remove_user_from_main_org(userid)
            return True
        else:
            logger.error("User ID not retrieved after creation.")
            return False

    def delete_user(self):
        try:
            userid = self._get_user_id()
            if userid is None:
                logger.error("Grafana delete_user: _get_user_id returned None")
                return False

            orgid = self._get_org_id()
            if orgid is None:
                logger.error("Grafana delete_user: _get_org_id returned None")
                return False

            # Delete the custom user from Grafana.
            r1 = self._del_user(userid)
            if r1.status_code not in [200, 204]:
                logger.error(f"Failed to delete Grafana user: status code {r1.status_code} {r1.text}")
                return False

            # IMPORTANT:
            # The default admin user cannot be removed from an organization when using its own credentials.
            # Therefore, before deleting the org, switch the active org to the main org (org id 1).
            r_switch = self._switch_org_main()
            if r_switch.status_code not in [200, 204]:
                logger.error(f"Failed to switch to main org: status code {r_switch.status_code} {r_switch.text}")
                return False

            # Now delete the user's custom organization.
            r2 = self._del_org(orgid)
            if r2.status_code not in [200, 204]:
                logger.error(f"Failed to delete Grafana org: status code {r2.status_code} {r2.text}")
                return False

            return True
        except Exception as e:
            logger.error(f"Exception in Grafana delete_user: {e}")
            return False

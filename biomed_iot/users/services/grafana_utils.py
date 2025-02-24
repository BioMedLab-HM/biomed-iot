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

    def _switch_user_org(self, userid, orgid):
        url = f"{self.grafana_origin}/api/users/{userid}/using/{orgid}"
        headers = {'content-type': 'application/json'}
        return requests.post(url, headers=headers)

    def _remove_user_from_main_org(self, userid):
        # Removes the custom user from the default organization (org id 1)
        url = f"{self.grafana_origin}/api/orgs/1/users/{userid}"
        headers = {'content-type': 'application/json'}
        return requests.delete(url, headers=headers)

    def _switch_org_main(self):
        url = f"{self.grafana_origin}/api/user/using/1"
        headers = {'content-type': 'application/json'}
        return requests.post(url, headers=headers)

    def create_user(self):
        self._make_org()
        orgid = self._get_org_id()
        if orgid:
            self._switch_org(orgid)
            self._make_user()
            self._add_user_to_org(orgid)
            self._add_data_sources()
            userid = self._get_user_id()
            if userid:
                self._switch_user_org(userid, orgid)
                self._remove_user_from_main_org(userid)
                return True
            else:
                logger.error("User ID not retrieved after creation.")
        else:
            logger.error("Organization ID not retrieved after org creation.")
        return False

    def _del_user(self, userid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users/{userid}"
        return requests.delete(url, headers=headers)

    def _del_org(self, orgid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/orgs/{orgid}"
        return requests.delete(url, headers=headers)

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

            # Delete the custom Grafana user.
            r1 = self._del_user(userid)
            # Delete the custom organization.
            r2 = self._del_org(orgid)
            self._switch_org_main()  # Switch back to the default organization

            if r1.status_code in [200, 204] and r2.status_code in [200, 204]:
                return True
            else:
                logger.error(f"Grafana deletion failed: delete user status {r1.status_code}, delete org status {r2.status_code}")
                return False
        except Exception as e:
            logger.error(f"Exception in Grafana delete_user: {e}")
            return False

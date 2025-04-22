import requests
import logging
from biomed_iot.config_loader import config

logger = logging.getLogger(__name__)

class GrafanaUserManager:
    def __init__(self, user):
        self.username        = user.username
        self.user_pword      = user.password
        self.user_email      = user.email
        self.influx_token    = user.influxuserdata.bucket_token
        self.influx_bucket_name = user.influxuserdata.bucket_name
        self.influx_org_name = config.influxdb.INFLUX_ORG_NAME
        self.influx_host     = config.influxdb.INFLUX_HOST
        self.influx_port     = config.influxdb.INFLUX_PORT
        self.hostname        = config.grafana.GRAFANA_HOST
        self.port            = config.grafana.GRAFANA_PORT
        self.admin_username  = config.grafana.GRAFANA_ADMIN_USERNAME
        self.admin_password  = config.grafana.GRAFANA_ADMIN_PASSWORD
        # Use HTTP Basic Auth for admin API calls
        self.auth    = (self.admin_username, self.admin_password)
        self.headers = {'Content-Type': 'application/json'}

    def _make_org(self):
        url     = f"http://{self.hostname}:{self.port}/api/orgs"
        payload = {"name": self.username}
        return requests.post(url, json=payload, headers=self.headers, auth=self.auth)

    def _get_org_id(self):
        url = f"http://{self.hostname}:{self.port}/api/orgs/name/{self.username}"
        r   = requests.get(url, headers=self.headers, auth=self.auth)
        try:
            return r.json().get("id")
        except Exception as e:
            logger.error(f"Error parsing organization ID: {e}")
            return None

    def _switch_org(self, orgid):
        url = f"http://{self.hostname}:{self.port}/api/user/using/{orgid}"
        return requests.post(url, headers=self.headers, auth=self.auth)

    def _switch_org_main(self):
        url = f"http://{self.hostname}:{self.port}/api/user/using/1"
        return requests.post(url, headers=self.headers, auth=self.auth)

    def _make_user(self):
        url = f"http://{self.hostname}:{self.port}/api/admin/users"
        payload = {
            "name": self.username,
            "email": self.user_email,
            "login": self.username,
            "password": self.user_pword
        }
        return requests.post(url, json=payload, headers=self.headers, auth=self.auth)

    def _add_user_to_org(self, orgid):
        url = f"http://{self.hostname}:{self.port}/api/orgs/{orgid}/users"
        payload = {"role": "Editor", "loginOrEmail": self.username}
        return requests.post(url, json=payload, headers=self.headers, auth=self.auth)

    def _add_data_sources(self):
        url = f"http://{self.hostname}:{self.port}/api/datasources"
        common_secure = {
            "httpHeaderValue1": f"Token {self.influx_token}",
            "token": self.influx_token
        }
        common_json = {
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
            "secureJsonData": common_secure,
            "jsonData": {**common_json, "version": "InfluxQL"},
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
            "secureJsonData": common_secure,
            "jsonData": {**common_json, "version": "Flux", "httpMode": "POST"},
            "isDefault": False,
            "version": 1,
            "readOnly": False
        }
        r1 = requests.post(url, json=influxql_payload, headers=self.headers, auth=self.auth)
        r2 = requests.post(url, json=flux_payload,   headers=self.headers, auth=self.auth)
        return r1, r2

    def _switch_user_org(self, userid, orgid):
        url = f"http://{self.hostname}:{self.port}/api/users/{userid}/using/{orgid}"
        return requests.post(url, headers=self.headers, auth=self.auth)

    def _remove_user_from_main_org(self, userid):
        url = f"http://{self.hostname}:{self.port}/api/orgs/1/users/{userid}"
        return requests.delete(url, headers=self.headers, auth=self.auth)

    def _get_user_id(self):
        url = f"http://{self.hostname}:{self.port}/api/users/lookup?loginOrEmail={self.username}"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        if response.status_code == 200:
            try:
                return response.json().get('id')
            except Exception as e:
                logger.error(f"Error parsing user ID: {e}")
        else:
            logger.error(f"Error getting user ID: {response.status_code} {response.text}")
        return None

    def _del_user(self, userid):
        url = f"http://{self.hostname}:{self.port}/api/admin/users/{userid}"
        return requests.delete(url, headers=self.headers, auth=self.auth)

    def _del_org(self, orgid):
        url = f"http://{self.hostname}:{self.port}/api/orgs/{orgid}"
        return requests.delete(url, headers=self.headers, auth=self.auth)

    def create_user(self):
        org_resp = self._make_org()
        if org_resp.status_code not in (200, 204):
            logger.error(f"Failed to create org: {org_resp.status_code} {org_resp.text}")
            return False

        orgid = self._get_org_id()
        if not orgid:
            logger.error("Organization ID not retrieved after org creation.")
            return False

        switch_resp = self._switch_org(orgid)
        if switch_resp.status_code not in (200, 204):
            logger.error(f"Failed to switch to user org: {switch_resp.status_code} {switch_resp.text}")
            return False

        user_resp = self._make_user()
        if user_resp.status_code not in (200, 204):
            logger.error(f"Failed to create user: {user_resp.status_code} {user_resp.text}")
            return False

        add_resp = self._add_user_to_org(orgid)
        if add_resp.status_code not in (200, 204):
            logger.error(f"Failed to add user to org: {add_resp.status_code} {add_resp.text}")
            return False

        self._add_data_sources()

        userid = self._get_user_id()
        if userid:
            self._switch_user_org(userid, orgid)
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

            r1 = self._del_user(userid)
            if r1.status_code not in (200, 204):
                logger.error(f"Failed to delete Grafana user: {r1.status_code} {r1.text}")
                return False

            r_switch = self._switch_org_main()
            if r_switch.status_code not in (200, 204):
                logger.error(f"Failed to switch to main org: {r_switch.status_code} {r_switch.text}")
                return False

            r2 = self._del_org(orgid)
            if r2.status_code not in (200, 204):
                logger.error(f"Failed to delete Grafana org: {r2.status_code} {r2.text}")
                return False

            return True
        except Exception as e:
            logger.error(f"Exception in Grafana delete_user: {e}")
            return False

import json
import requests
import logging
from biomed_iot.config_loader import config


logger = logging.getLogger(__name__)


class GrafanaUserManager:
    '''Grafana Manager...'''

    def __init__(self, user):
        self.username = user.username
        self.user_pword = user.password  # Oder selbst generiertes PW?
        self.user_email = user.email  # braucht Grafana das?
        self.influx_token = user.influxuserdata.bucket_token
        self.influx_bucket_name = user.influxuserdata.bucket_name
        self.influx_org_name = config.influxdb.INFLUX_ORG_NAME
        self.influx_host = config.influxdb.INFLUX_HOST
        self.influx_port = config.influxdb.INFLUX_PORT
        self.hostname = config.grafana.GRAFANA_HOST
        self.port = config.grafana.GRAFANA_PORT
        self.admin_username = config.grafana.GRAFANA_ADMIN_USERNAME
        self.admin_password = config.grafana.GRAFANA_ADMIN_PASSWORD
        self.grafana_origin = f"http://{self.admin_username}:{self.admin_password}@{self.hostname}:{self.port}"

    def _make_org(self):
        payload = {
            "name": self.username
        }
        url = f"{self.grafana_origin}/api/orgs"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r

    def _get_org_id(self):
        url = f"{self.grafana_origin}/api/orgs/name/{self.username}"
        headers = {'content-type': 'application/json'}
        r = requests.get(url, headers=headers)
        content = json.loads(r.text)
        orgid = content["id"]
        return orgid

    def _switch_org(self, orgid):
        url = f"{self.grafana_origin}/api/user/using/{orgid}"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, headers=headers)
        return r

    def _make_user(self):
        payload = {
            "name": self.username,
            "email": self.user_email,
            "login": self.username,
            "password": self.user_pword
        }
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users"
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r

    def _add_user_to_org(self, orgid):
        payload = {
            "role": "Editor",
            "loginOrEmail": self.username
        }
        url = f"{self.grafana_origin}/api/orgs/{orgid}/users"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r

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

        # First payload for InfluxQL
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

        # Second payload for Flux
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

        # Make the first request for InfluxQL
        response1 = requests.post(url, data=json.dumps(influxql_payload), headers=headers)

        response2 = requests.post(url, data=json.dumps(flux_payload), headers=headers)

        return response1, response2

    def _get_user_id(self):
        url = f"{self.grafana_origin}/api/users/lookup?loginOrEmail={self.username}"
        headers = {'content-type': 'application/json'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = json.loads(response.text)
            if 'id' in content:
                return content['id']
            else:
                logger.error("ID not found in response: " + content)
        else:
            logger.error("Error from API: " + response.status_code + "  " + response.text)
        return None

    def _switch_user_org(self, userid, orgid):
        url = f"{self.grafana_origin}/api/users/{userid}/using/{orgid}"
        headers = {'content-type': 'application/json'}
        response = requests.post(url,  headers=headers)
        return response

    def _remove_user_from_main_org(self, userid):
        url = f"{self.grafana_origin}/api/orgs/1/users/{userid}"
        headers = {'content-type': 'application/json'}
        response = requests.delete(url, headers=headers)
        return response

    def _switch_org_main(self):
        url = f"{self.grafana_origin}/api/user/using/1"
        headers = {'content-type': 'application/json'}
        response = requests.post(url, headers=headers)
        return response

    def create_user(self):
        self._make_org()
        try:
            orgid = self._get_org_id()
            self._switch_org(orgid)
            self._make_user()
            self._add_user_to_org(orgid)
            self._add_data_sources()
            userid = self._get_user_id()
            self._switch_user_org(userid, orgid)
            self._remove_user_from_main_org(userid)
            # self._switch_org_main()
            return True
        except FileExistsError:
            logger.error('grafana: FileExistsError')
            return False

    def _del_user(self, userid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users/{userid}"
        r = requests.delete(url, headers=headers)
        return r

    def _del_org(self, orgid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/orgs/{orgid}"
        r = requests.delete(url, headers=headers)
        return r

    def delete_user(self):
        try:
            userid = self._get_user_id()
            self._del_user(userid)
            orgid = self._get_org_id()
            self._del_org(orgid)
            self._switch_org_main()  # TODO: test if this is necesssary
            return True
        except FileExistsError:
            return False

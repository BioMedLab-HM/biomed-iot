import json
import requests
from biomed_iot.config_loader import config
import logging


logger = logging.getLogger(__name__)


class GrafanaUserManager:
    '''Grafana Manager...'''

    def __init__(self, user):
        logger.info("In GrafanaUserManager's __init__ function")
        self.username = user.username
        logger.info('GrafanaUserManager __init__ function: After self.username')
        self.user_pword = user.password  # Oder selbst generiertes PW?
        logger.info('GrafanaUserManager __init__ function: After self.user_pword')
        self.user_email = user.email  # braucht Grafana das?
        logger.info('GrafanaUserManager __init__ function: After self.user_email')
        self.influx_token = user.influxuserdata.bucket_token
        self.influx_bucket_name = user.influxuserdata.bucket_name
        logger.info('GrafanaUserManager __init__ function: After self.influx_token')
        self.influx_org_name = config.influxdb.INFLUX_ORG_NAME
        logger.info('GrafanaUserManager __init__ function: After self.influx_org_id')
        self.influx_host = config.influxdb.INFLUX_HOST
        logger.info('GrafanaUserManager __init__ function: After self.influx_host')
        self.influx_port = config.influxdb.INFLUX_PORT
        logger.info('GrafanaUserManager __init__ function: After self.influx_port')
        self.hostname = config.grafana.GRAFANA_HOST
        logger.info('GrafanaUserManager __init__ function: After self.hostname')
        self.port = config.grafana.GRAFANA_PORT
        logger.info('GrafanaUserManager __init__ function: After self.port')
        self.admin_username = config.grafana.GRAFANA_ADMIN_USERNAME
        logger.info('GrafanaUserManager __init__ function: After self.admin_username')
        self.admin_password = config.grafana.GRAFANA_ADMIN_PASSWORD
        logger.info('GrafanaUserManager __init__ function: After self.admin_password')
        self.grafana_origin = f"http://{self.admin_username}:{self.admin_password}@{self.hostname}:{self.port}"
        logger.info("End of GrafanaUserManager's __init__ function")

    def _make_org(self):
        payload = '{"name": "'
        payload += self.username
        payload += '"}'
        url = f"{self.grafana_origin}/api/orgs"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, data=payload, headers=headers)
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

    def _makeuser(self):
        payload = '{"name":"'
        payload += self.username
        payload += '", "email":"'
        payload += self.user_email
        payload += '", "login":"'
        payload += self.username
        payload += '", "password":"'
        payload += self.user_pword
        payload += '"}'
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users"
        r = requests.post(url, data=payload, headers=headers)
        return r

    def _add_user_to_org(self, orgid):
        payload = '{"role":"Editor", "loginOrEmail": "'
        payload += self.username
        payload += '"}'
        url = f"{self.grafana_origin}/api/orgs/{orgid}/users"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, data=payload, headers=headers)
        return r

    def _make_data_source(self):
        payload = '{"access": "proxy", '
        payload += '"database":"'
        payload += self.influx_bucket_name
        payload += '", "name":"'
        payload += self.username
        payload += '", "type":"influxdb", '
        payload += '"url": "http://{}:{}", '.format(self.influx_host, self.influx_port)
        payload += '"secureJsonData": {"httpHeaderValue1": "Token '
        payload += self.influx_token
        payload += '","token":"'
        payload += self.influx_token
        payload += '"}, "jsonData":{"httpMode": "GET", "version": "InfluxQL", "httpHeaderName1": "Authorization", "organization": "iotree42"}'  # TODO: using .format() or f string with {self.influx_org_name} both do not work here
        payload += ', "isDefault":true, "version":1, "readOnly":false}'
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/datasources"
        r = requests.post(url, data=payload, headers=headers)
        payload = '{"access": "proxy", '
        payload += '"database":"'
        payload += self.influx_bucket_name
        payload += '", "name":"'
        payload += self.username
        payload += 'Flux", "type":"influxdb", '
        payload += '"url": "http://{}:{}", '.format(self.influx_host, self.influx_port)
        payload += '"secureJsonData": {"httpHeaderValue1": "Token '
        payload += self.influx_token
        payload += '","token":"'
        payload += self.influx_token
        payload += '"}, "jsonData":{"httpMode": "POST", "version": "Flux", "httpHeaderName1": "Authorization", "organization": "iotree42"}'
        payload += ', "isDefault":false, "version":1, "readOnly":false}'
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/datasources"
        r = requests.post(url, data=payload, headers=headers)
        return r

    def _get_user_id(self):
        url = f"{self.grafana_origin}/api/users/lookup?loginOrEmail={self.username}"
        headers = {'content-type': 'application/json'}
        r = requests.get(url, headers=headers)
        content = json.loads(r.text)
        userid = content["id"]
        return userid

    def _switch_user_org(self, userid, orgid):
        url = f"{self.grafana_origin}/api/users/{userid}/using/{orgid}"
        headers = {'content-type': 'application/json'}
        r = requests.post(url,  headers=headers)
        return r

    def _switch_org_main(self):
        url = f"{self.grafana_origin}/api/user/using/1"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, headers=headers)
        return r

    def _remove_user_from_main_org(self, userid):
        url = f"{self.grafana_origin}/api/orgs/1/users/{userid}"
        headers = {'content-type': 'application/json'}
        r = requests.delete(url, headers=headers)
        return r


    def create_user(self):
        logger.info('grafana: create_user()')
        self._make_org()
        logger.info('grafana: After _make_org()')
        try:
            orgid = self._get_org_id()
            logger.info('grafana: After _get_org_id()')
            self._switch_org(orgid)
            logger.info('grafana: After _switch_org(orgid)')
            self._makeuser()
            logger.info('grafana: After _makeuser()')
            self._add_user_to_org(orgid)
            logger.info('grafana: After _add_user_to_org(orgid)')
            self._make_data_source()
            logger.info('grafana: After _make_data_source()')
            userid = self._get_user_id()
            logger.info('grafana: After _get_user_id()')
            self._switch_user_org(userid, orgid)
            logger.info('grafana: After _get_user_id(userid, orgid)')
            self._remove_user_from_main_org(userid)
            # self._switch_org_main()
            logger.info('grafana: After _remove_user_from_main_org()')
            return True
        except FileExistsError:
            logger.error('grafana: FileExistsError')
            return False

    def _get_user_id(self):
        url = f"{self.grafana_origin}/api/users/lookup?loginOrEmail={self.username}"
        headers = {'content-type': 'application/json'}
        r = requests.get(url, headers=headers)
        content = json.loads(r.text)
        userid = content["id"]
        return userid

    def _del_user(self, userid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/admin/users/{userid}"
        r = requests.delete(url, headers=headers)
        return r

    def _get_org_id(self):
        url = f"{self.grafana_origin}/api/orgs/name/{self.username}"
        headers = {'content-type': 'application/json'}
        r = requests.get(url, headers=headers)
        content = json.loads(r.text)
        orgid = content["id"]
        print(orgid)
        return orgid

    def _del_org(self, orgid):
        headers = {'content-type': 'application/json'}
        url = f"{self.grafana_origin}/api/orgs/{orgid}"
        r = requests.delete(url, headers=headers)
        print(r)
        return r

    def _switch_org_main(self):
        url = f"{self.grafana_origin}/api/user/using/1"
        headers = {'content-type': 'application/json'}
        r = requests.post(url, headers=headers)
        return r

    def delete_user(self):
        try:
            userid = self._get_user_id()
            self._del_user(userid)
            orgid = self._get_org_id()
            self._del_org(orgid)
            self._switch_org_main()
            return True
        except FileExistsError:
            return False


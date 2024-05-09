import json
import users.models as user_models
from biomed_iot.config_loader import config
from influxdb_client import InfluxDBClient
import requests  # For HTTP requests to the v1 compatibility endpoint
import logging


logger = logging.getLogger(__name__)

# INFLUX_ALL_ACCESS_TOKEN authorizes to perform create and delete actions within the organization
INFLUX_ALL_ACCESS_TOKEN = config.influxdb.INFLUX_ALL_ACCESS_TOKEN


class InfluxUserManager:
    """
    Manages InfluxDB resources (buckets and tokens) for a user.

    Attributes:
        user: Django user instance associated with InfluxDB resources.
    """

    def __init__(self, user):
        """
        Initializes InfluxUserManager with user and InfluxDB configuration.

        Parameters:
            user: The Django user instance.
        """
        self.user = user
        self.org_id = config.influxdb.INFLUX_ORG_ID
        self.host = config.influxdb.INFLUX_HOST
        self.port = config.influxdb.INFLUX_PORT
        self.url = f'http://{self.host}:{self.port}'
        self.auth_url = f'{self.url}/api/v2/authorizations'
        self.client = InfluxDBClient(url=self.url, token=INFLUX_ALL_ACCESS_TOKEN, org=self.org_id)

    def _create_bucket(self):
        """
        Creates a new bucket in InfluxDB with a unique name.

        Returns:
            The created bucket instance.
        """
        bucket = None
        bucket_name = user_models.InfluxUserData.generate_unique_bucket_name()  # TODO: self.user.influxuserdata.generate_unique_bucket_name()
        bucket = self.client.buckets_api().create_bucket(bucket_name=bucket_name, org=self.org_id)
        if bucket:
            return bucket
        else:
            logger.error(f'Failed to create bucket: {bucket_name}')
            raise Exception(f'Failed to create bucket: {bucket_name}')
        

    def _create_bucket_token(self, bucket):
        """
        Creates a read-write token for the specified bucket.

        Parameters:
            bucket: The bucket instance for which the token is created.

        Returns:
            A tuple containing the bucket token and its ID.
        """
        headers = {'Authorization': f'Token {INFLUX_ALL_ACCESS_TOKEN}', 'Content-type': 'application/json'}
        payload = {
            'orgID': self.org_id,
            'permissions': [
                {'action': 'read', 'resource': {'type': 'buckets', 'id': bucket.id, 'orgID': self.org_id}},
                {'action': 'write', 'resource': {'type': 'buckets', 'id': bucket.id, 'orgID': self.org_id}},
            ],
        }

        response = requests.post(self.auth_url, headers=headers, data=json.dumps(payload))
        if response.status_code in [200, 201]:
            response_json = response.json()
            return (response_json.get('token'), response_json.get('id'))
        else:
            raise Exception(f'Failed to create token: {response.text}')


    def create_new_influx_user_resources(self) -> bool:
        """
        Creates new InfluxDB resources (bucket and token) for the user and stores their data.

        Returns:
            True if the resources were successfully created and saved; False otherwise.
        """
        logger.info('in create_new_influx_user_resources() function')
        bucket = self._create_bucket()
        logger.info(f'bucket: {bucket.name}; id: {bucket.id}')
        bucket_token, bucket_token_id = self._create_bucket_token(bucket)
        logger.info(f'bucket_token: {bucket_token}; id: {bucket_token_id}')
        # Assuming self.user is the Django user instance associated with these resources
        influx_user_data, created = user_models.InfluxUserData.objects.update_or_create(
            user=self.user,
            defaults={
                'bucket_name': bucket.name,
                'bucket_id': bucket.id,
                'bucket_token': bucket_token,
                'bucket_token_id': bucket_token_id,
            },
        )
        logger.info(f'user_models.InfluxUserData created?: {created}')

        success = all([influx_user_data, bucket.id, bucket_token_id])  # True if all values are not None
        logger.info(f"create_new_influx_user_resources returns '{success}'")
        return success

    def delete_influx_user_resources(self) -> bool:
        """
        Deletes the InfluxDB resources (bucket and token) associated with the user.

        Returns:
            True if all resources were successfully deleted; False otherwise.
        """
        token_deleted = False
        bucket_deleted = False
        model_instance_deleted = False

        try:
            # get bucket_id and bucket_token_id from self.user's user_models.InfluxUserData
            influx_user_data = user_models.InfluxUserData.objects.get(user=self.user)
            bucket_id = influx_user_data.bucket_id
            bucket_token_id = influx_user_data.bucket_token_id
        except user_models.InfluxUserData.DoesNotExist:
            print('Influx user data not found.')
            return False  # No resources to delete if the user data is not found.

        # Delete the Token in InfluxDB
        delete_token_url = f'{self.auth_url}/{bucket_token_id}'
        delete_token_response = requests.delete(
            delete_token_url, headers={'Authorization': f'Token {INFLUX_ALL_ACCESS_TOKEN}'}
        )
        if delete_token_response.status_code in [204, 200]:
            print(f"Bucket-token with ID '{bucket_token_id}' deleted.")
            token_deleted = True
        else:
            print(f"Failed to delete bucket-token with ID '{bucket_token_id}")

        # Delete the bucket in InfluxDB
        # Attempt to delete the bucket
        try:
            self.client.buckets_api().delete_bucket(bucket_id)
            print(f"Bucket with ID '{bucket_id}' deleted.")
            bucket_deleted = True
        except Exception as e:
            if e.status == 404:  # Bucket not found
                print("Bucket already deleted or not found.")
                bucket_deleted = True
            else:
                print(f"Failed to delete bucket: {e}")
                bucket_deleted = False

        if bucket_deleted:
            try:
                # Delete the user_models.InfluxUserData model instance
                influx_user_data.delete()
                model_instance_deleted = True
            except Exception as e:
                print(f'Exception occurred while deleting user_models.InfluxUserData model instance: {e}')

        return all([token_deleted, bucket_deleted, model_instance_deleted])

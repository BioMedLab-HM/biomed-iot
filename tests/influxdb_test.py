# ruff: noqa: E402
"""
This script interacts with an InfluxDB instance to demonstrate various operations using the InfluxDBClient library.

Sections:
1. **Configuration**: Sets up the InfluxDB connection parameters, including the URL, access token, organization ID, and bucket name.
2. **Initialize Client**: Initializes the InfluxDB client using the provided credentials.
3. **Step 1: Create a New Bucket**: Creates a new bucket named "test" for storing and managing data.
4. **Step 2: Create a Read-Write Token**: Generates a read-write token specifically for the "test" bucket to allow authorized data operations.
5. **Step 3: Write Test Data**: Writes sample data (the answer to the ultimate question of life) into the "test" bucket using the InfluxDBClient.
6. **Step 4: Query Data Using InfluxQL**: Queries the stored data using the InfluxQL language through the v1 compatibility endpoint.
7. **Step 5: Delete Data**: Deletes the test data from the "test" bucket using the InfluxDB API.
8. **Step 6: Delete the Test-Bucket Token**: Deletes the previously created read-write token to clean up security credentials.
9. **Step 7: Delete the "Test" Bucket**: Removes the "test" bucket from the InfluxDB instance to clean up resources.
10. **Exception Handling and Cleanup**: Ensures proper cleanup of resources and handles any exceptions that may occur during the script's execution.
"""


# Further information: https://influxdb-client.readthedocs.io/en/stable/index.html

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests  # For making HTTP requests to the v1 compatibility endpoint
from datetime import datetime
import json

# Configuration
url = 'http://localhost:8086'  # e.g., "http://localhost:8086"
all_access_token = ''
org_id = ''  # Your organization name
bucket_name = 'test'

# Initialize client
client = InfluxDBClient(url=url, token=all_access_token, org=org_id)
try:
    ### Step 1: Create a new bucket called "test"
    bucket = client.buckets_api().create_bucket(bucket_name=bucket_name, org=org_id)
    print(f"Bucket '{bucket.name}' created.")

    bucket = client.buckets_api().find_bucket_by_name(bucket_name)


    ### Step 2: Create a read-write token for the "test" bucket
    bucket_token = None
    token_id = None
    auth_url = f'{url}/api/v2/authorizations'
    headers = {'Authorization': f'Token {all_access_token}', 'Content-type': 'application/json'}
    payload = {
        'orgID': org_id,
        'permissions': [
            {'action': 'read', 'resource': {'type': 'buckets', 'id': bucket.id, 'orgID': org_id}},
            {'action': 'write', 'resource': {'type': 'buckets', 'id': bucket.id, 'orgID': org_id}},
        ],
    }
    response = requests.post(auth_url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        # Parse the response JSON to extract the token
        response_json = response.json()
        bucket_token = response_json.get('token')
        token_id = response_json.get('id')
        print(f'Token created: {bucket_token}')
    else:
        print(f'Failed to create token: {response.text}')

    ### Step 3: Write test data to the "test" bucket  # statt token.token: all_access_token
    write_client = InfluxDBClient(url=url, token=bucket_token, org=org_id).write_api(write_options=SYNCHRONOUS)
    point = Point('UltimateQuestion').tag('Response', 'DeepThought').field('Answer', 42)
    write_client.write(bucket=bucket_name, org=org_id, record=point)
    print('Test data written.')


    ### Step 4: Query the data using InfluxQL through the v1 compatibility endpoint
    query_url = f'{url}/query?org={org_id}&db={bucket_name}&q=SELECT * FROM "testMeasurement" WHERE time > now() - 1h'
    response = requests.get(query_url, headers={'Authorization': f'Token {bucket_token}'})
    if response.status_code == 200:
        print('Queried data (InfluxQL):')
        print(response.text)
    else:
        print('Failed to query data using InfluxQL.')


    ### Step 5: Delete the data using the /api/v2/delete endpoint
    delete_url = f'{url}/api/v2/delete?org={org_id}&bucket={bucket_name}'
    delete_headers = {'Authorization': f'Token {bucket_token}', 'Content-Type': 'application/json'}
    # Generating the current time in ISO 8601 format for the stop time in the delete request
    stop_time = datetime.now().isoformat() + 'Z'  # datetime.utcnow().isoformat() + "Z"

    delete_data = {'start': '1970-01-01T00:00:00Z', 'stop': stop_time, 'predicate': '_measurement="testMeasurement"'}
    delete_response = requests.post(delete_url, json=delete_data, headers=delete_headers)
    if delete_response.status_code == 204:
        print('Test data deleted.')
    else:
        print(f'Failed to delete data: {delete_response.text}')

    ### Step 6: Delete the test-bucket token
    # Construct the API URL for deleting an authorization
    delete_url = f'{url}/api/v2/authorizations/{token_id}'
    # Construct the headers
    headers = {'Authorization': f'Token {all_access_token}'}
    # Make the DELETE request to delete the authorization
    response = requests.delete(delete_url, headers=headers)
    if response.status_code in [204, 200]:
        print('Token deleted successfully.')
    else:
        print(f'Failed to delete token: {response.text}')

    ### Step 7: Delete the "test" bucket
    buckets_api = client.buckets_api()
    bucket = buckets_api.find_bucket_by_name(bucket_name)
    client.buckets_api().delete_bucket(bucket)
    print(f"Bucket '{bucket_name}' deleted.")
except Exception as e:
    print(e)

finally:
    client.close()

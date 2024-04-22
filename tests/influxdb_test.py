#https://influxdb-client.readthedocs.io/en/stable/index.html

from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import requests  # For making HTTP requests to the v1 compatibility endpoint
from datetime import datetime
import json

# Configuration
url = "http://localhost:8086"  # e.g., "http://localhost:8086"
all_access_token = "..."
org_id = "..."  # Your organization name
bucket_name = "test"

# Initialize client
client = InfluxDBClient(url=url, token=all_access_token, org=org_id)
try:
    # Step 1: Create a new bucket called "test"
    bucket = client.buckets_api().create_bucket(bucket_name=bucket_name, org=org_id)
    # bucket = client.buckets_api().find_bucket_by_name(bucket_name)
    print(f"Bucket '{bucket_name}' created.")


    #Step 2: Create a read-write token for the "test" bucket
    bucket_token = None
    token_id = None
    auth_url = f"{url}/api/v2/authorizations"
    headers = {
        "Authorization": f"Token {all_access_token}",
        "Content-type": "application/json"
    }
    payload = {
        "orgID": org_id,
        "permissions": [
            {"action": "read", "resource": {"type": "buckets", "id": bucket.id, "orgID": org_id}},
            {"action": "write", "resource": {"type": "buckets", "id": bucket.id, "orgID": org_id}}
        ]
    }
    response = requests.post(auth_url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        # Parse the response JSON to extract the token
        response_json = response.json()
        bucket_token = response_json.get("token")
        token_id = response_json.get("id")
        print(f"Token created: {bucket_token}")
    else:
        print(f"Failed to create token: {response.text}")


    # Step 3: Write test data to the "test" bucket  # statt token.token: all_access_token
    write_client = InfluxDBClient(url=url, token=bucket_token, org=org_id).write_api(write_options=SYNCHRONOUS)
    point = Point("testMeasurement").tag("location", "test").field("value", 123.5)
    write_client.write(bucket=bucket_name, org=org_id, record=point)
    print("Test data written.")


    # Step 4: Query the data using InfluxQL through the v1 compatibility endpoint
    query_url = f"{url}/query?org={org_id}&db={bucket_name}&q=SELECT * FROM \"testMeasurement\" WHERE time > now() - 1h"
    response = requests.get(query_url, headers={"Authorization": f"Token {bucket_token}"})
    if response.status_code == 200:
        print("Queried data (InfluxQL):")
        print(response.text)
    else:
        print("Failed to query data using InfluxQL.")


    # Step 5: Delete the data using the /api/v2/delete endpoint
    delete_url = f"{url}/api/v2/delete?org={org_id}&bucket={bucket_name}"
    delete_headers = {
        "Authorization": f"Token {bucket_token}",
        "Content-Type": "application/json"
    }
    # Generating the current time in ISO 8601 format for the stop time in the delete request
    stop_time =  datetime.now().isoformat() + "Z" # datetime.utcnow().isoformat() + "Z"
    
    delete_data = {
        "start": "1970-01-01T00:00:00Z",
        "stop": stop_time,
        "predicate": "_measurement=\"testMeasurement\""
    }
    delete_response = requests.post(delete_url, json=delete_data, headers=delete_headers)
    if delete_response.status_code == 204:
        print("Test data deleted.")
    else:
        print(f"Failed to delete data: {delete_response.text}")


    # Step 6: Delete the test-bucket token
    # Construct the API URL for deleting an authorization
    delete_url = f"{url}/api/v2/authorizations/{token_id}"
    # Construct the headers
    headers = {
        "Authorization": f"Token {all_access_token}"
    }
    # Make the DELETE request to delete the authorization
    response = requests.delete(delete_url, headers=headers)
    if response.status_code in [204, 200]:
        print("Token deleted successfully.")
    else:
        print(f"Failed to delete token: {response.text}")


    # Step 7: Delete the "test" bucket
    buckets_api = client.buckets_api()
    bucket = buckets_api.find_bucket_by_name(bucket_name)
    client.buckets_api().delete_bucket(bucket)
    print(f"Bucket '{bucket_name}' deleted.")
except Exception as e:
    print(e)

finally:
    client.close()

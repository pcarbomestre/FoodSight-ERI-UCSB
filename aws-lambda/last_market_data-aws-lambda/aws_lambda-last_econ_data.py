import requests  # For making HTTP requests
import json  # For handling JSON data
import boto3  # AWS SDK for Python, allows Python scripts to use services like Amazon S3 and Amazon EC2
from concurrent.futures import ThreadPoolExecutor  # For parallel execution

# Constants
base_url = "https://marsapi.ams.usda.gov"  # Base URL for the marsapi
api_key = open("../foodsight-app/.mmn_api_token").read()   # API key for authentication with marsapi (type yours)
s3 = boto3.client('s3')  # Initializing Amazon S3 client
bucket_name = 'foodsight-lambda'  # Name of the S3 bucket
key_path_read = 'market_data/markets_data_final.json'  # Path to the JSON file in the S3 bucket

# Function to fetch data from marsapi
def get_data_from_marsapi(endpoint):
    with requests.Session() as session:  # Creates a session to manage connections
        response = session.get(base_url + endpoint, auth=(api_key, ''))  # Sends GET request
        
        # Checks if the response status is 200 (OK)
        if response.status_code == 200:
            return response.json()  # Returns JSON content of the response
        else:
            response.raise_for_status()  # Raises an exception if the response contains an error

# Function to fetch market data
def fetch_data_for_market(market):
    slug_id = market['slug_id']
    market_name = market['market_location_name']
    print(f"Fetching data for {market_name} (Slug ID: {slug_id})...")

    # Endpoint to check data availability for the last 15 days
    endpoint_limit = f"/services/v1.2/reports/{slug_id}/Details?lastDays=15&market_type=Auction Livestock"
    data_limit = get_data_from_marsapi(endpoint_limit)

    # Checks if there's data for the last 30 days
    if data_limit and 'results' in data_limit and data_limit['results']:
        lastDay = 1  # Initializes day counter
        while lastDay <= 30:  # Loop to search data day-by-day for the last 30 days
            endpoint = f"/services/v1.2/reports/{slug_id}/Details?lastDays={lastDay}&market_type=Auction Livestock"
            data = get_data_from_marsapi(endpoint)

            # Checks if data is available for the day
            if data and 'results' in data and data['results']:
                print(f"Data found for {slug_id} at lastDay={lastDay}")
                return data['results']

            # If no data found for the day, print a message and check the next day
            print(f"No data found for {slug_id} at lastDay={lastDay}. Trying next day...")
            lastDay += 1

    # If no data found for the last 30 days, print a message and move to the next market
    print(f"No data found for {slug_id} within the last 30 days. Moving to the next slug_id.")
    return []

# Function to fetch data for all markets
def fetch_all_data(markets_list):
    all_data = []

    # Parallel execution using ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_data_for_market, markets_list))

    # Aggregates all data
    for data in results:
        if data:
            all_data.extend(data)

    return all_data

def lambda_handler(event, context):
    # Fetching market list from S3
    response = s3.get_object(Bucket=bucket_name, Key=key_path_read)  # Fetches the object from the S3 bucket
    markets_list = json.loads(response['Body'].read().decode('utf-8'))  # Decodes and loads the JSON data

    # Fetches data for all markets
    last_market_data = fetch_all_data(markets_list)

    # Converts the aggregated data to JSON and uploads to S3
    json_content = json.dumps(last_market_data)
    json_bytes = json_content.encode('utf-8')
    
    key_path_write = 'market_data/last_market_data.json'
    s3.put_object(Bucket=bucket_name, Key=key_path_write, Body=json_bytes)
    print(f"Store data at: bucket {bucket_name}, key {key_path_write}")

    return {
        'statusCode': 200,
        'body': json.dumps('Data fetched and saved successfully!')
    }

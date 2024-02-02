# ------------------ Importing Libraries ------------------ #

import boto3
import pandas as pd
import geopandas as gpd
import json
import sys
import os
import io
import requests
import zipfile
import janitor
from datetime import datetime
from io import BytesIO
from botocore.exceptions import NoCredentialsError

# ------------------ AWS S3 parameters ------------------ #

s3 = boto3.client('s3')  # Initializing Amazon S3 client
bucket_name = 'foodsight-lambda'
key_path_grasscast_grid_read = 'spatial_data/grasscast_aoi_grid.geojson'
key_path_overlapping_gridids_read = 'spatial_data/overlapping_gridids.json'
key_path_seasprcp_data_read = 'spatial_data/seasprcp_data'
key_path_seasprcp_grid_read = 'spatial_data/seasprcp_grid.csv'


# ------------------ Define functions ------------------#
print("Defining helper functions...")

## Read/write functions:

# Function to read a JSON file from S3
def read_json_from_s3(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    json_obj = response['Body'].read().decode('utf-8')
    return pd.DataFrame(json.loads(json_obj))

# Function to read a GeoJSON file from S3 into a GeoPandas DataFrame
def read_geojson_from_s3(bucket, key):
    geojson_obj = s3.get_object(Bucket=bucket, Key=key)
    return gpd.read_file(BytesIO(geojson_obj['Body'].read()))

# Function to read a shapefile from S3 into a GeoPandas DataFrame
def read_shapefile_from_s3(bucket_name, folder_path):
    # Create a temporary directory to store files
    local_dir = '/tmp/shp_folder/'
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # List all files in the S3 folder
    try:
        files = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)['Contents']
    except NoCredentialsError:
        return "Error: No AWS credentials found."
    except KeyError:
        return "Error: No files found in the specified bucket/folder."

    # Download each file in the folder to the local directory
    for file in files:
        file_name = file['Key'].split('/')[-1]
        if file_name.endswith('.shp') or file_name.endswith('.shx') or file_name.endswith('.dbf'):
            s3.download_file(bucket_name, file['Key'], local_dir + file_name)

    # Read the shapefile into a geopandas dataframe
    try:
        shp_files = [os.path.join(local_dir, f) for f in os.listdir(local_dir) if f.endswith('.shp')]
        if len(shp_files) == 0:
            return "Error: No .shp file found in the specified folder."
        gdf = gpd.read_file(shp_files[0])

        # Check if the CRS is set, if not, set it to a default (assuming WGS 84)
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            # Transform CRS to WGS 84 (EPSG:4326) if needed
            gdf.to_crs(epsg=4326, inplace=True)
        return gdf

    except Exception as e:
        return "Error: " + str(e)

    finally:
        # Clean up the temporary directory
        for f in os.listdir(local_dir):
            os.remove(os.path.join(local_dir, f))
        os.rmdir(local_dir)
        
# Function to save dataframe into S3
def df_to_s3_csv(df, bucket, key):
    # Convert DataFrame to CSV in-memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    # Convert String buffer to Bytes buffer
    csv_buffer_bytes = io.BytesIO(csv_buffer.getvalue().encode())
    # Upload to S3
    s3.put_object(Bucket=bucket, Body=csv_buffer_bytes.getvalue(), Key=key)


## Helper functions:

# Function to access Climate Outlook files from NOAA Climate Prediction Center
# More information at: https://www.cpc.ncep.noaa.gov/products/predictions/long_range/interactive/index.php
def download_and_extract_seasprcp_files(year, month, s3_bucket, s3_folder):
    # Check if the month is between April and July
    if month < 3 or month > 7:
        return False

    base_url = 'https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/'
    filename = 'seasprcp_{0:04d}{1:02d}.zip'.format(year, month)
    url = base_url + filename

    try:
        # Check and delete existing files in the S3 folder
        response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_folder)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=s3_bucket, Key=obj['Key'])
        # Download the ZIP file
        response = requests.get(url)
        response.raise_for_status()
        # Create a temporary file for the ZIP
        temp_zip_path = '/tmp/' + filename
        with open(temp_zip_path, 'wb') as f:
            f.write(response.content)
        # Extract files and upload to S3
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.startswith('lead1_'):
                    zip_ref.extract(file, '/tmp/')
                    # Splitting the file name and extension
                    file_name, file_extension = os.path.splitext(file)
                    # Renaming file with _prcp and year, preserving the original extension
                    new_filename = f"{file_name}_{month}_{year}{file_extension}"
                    os.rename('/tmp/' + file, '/tmp/' + new_filename)
                    s3.upload_file('/tmp/' + new_filename, s3_bucket, s3_folder + '/' + new_filename)
                    os.remove('/tmp/' + new_filename)
        # Remove the ZIP file after extraction
        os.remove(temp_zip_path)
        return "Files starting with 'lead1' extracted and uploaded to S3 successfully."

    except requests.exceptions.HTTPError as err:
        return "HTTP Error: " + str(err)
    except zipfile.BadZipFile:
        return "Error: The downloaded file is not a zip file."
    except Exception as e:
        return "Error: " + str(e)


# Function to associate each grid cell to the climate outlook
def join_attributes_by_largest_overlap(seasprcp_raw, precip_grid_raw):
    
    seasprcp_projected = seasprcp_raw.to_crs(epsg=4326)
    precip_grid_projected = precip_grid_raw.to_crs(epsg=4326)
    intersection = gpd.overlay(seasprcp_projected, precip_grid_projected, how='intersection')
    intersection['area'] = intersection.geometry.area
    intersection.sort_values(by='area', inplace=True)
    intersection.drop_duplicates(subset='gridid', keep='last', inplace=True)
    intersection = intersection.to_crs(epsg=4326)
    joined = seasprcp_raw.merge(intersection[['gridid','Cat','Prob']], left_on='gridid', right_on='gridid').clean_names()
    
    return joined

# ------------------ Process and store updated Spatial Data ------------------#
def handler(event, context):

    print("Downloading spatial data from NOAA CPC...")
    download_result = download_and_extract_seasprcp_files(datetime.now().year, datetime.now().month, bucket_name, key_path_seasprcp_data_read)
    if download_result is False:
        print("     No download required. Month is not between April and July.")
        sys.exit() 

    print("Preparing spatial data...")
    # Reference forecast to climate outlooks
    print("     Read climate data from S3...")
    seasprcp_raw = read_shapefile_from_s3(bucket_name, key_path_seasprcp_data_read)
    if isinstance(seasprcp_raw, str):
        print("         ",seasprcp_raw)
    else:
        print("         Climate data read successfully.")

    seasprcp_raw['Prob'] = seasprcp_raw['Prob'].apply(lambda x: (1/3)*100 if x == 33.0 else x)
    ## Read in AOI Grid
    print("     Read in AOI grid...")
    grasscast_aoi_grid = read_geojson_from_s3(bucket_name, key_path_grasscast_grid_read)
    # Apply function to associate each grid cell to the climate outlook
    print("     Join climate attributes to grid...")
    seasprcp_grid = join_attributes_by_largest_overlap(grasscast_aoi_grid, seasprcp_raw)
    # Save data
    print("Save spatial data outputs to S3...")
    df_to_s3_csv(seasprcp_grid, bucket_name, key_path_seasprcp_grid_read)

    return {
        'statusCode': 200,
        'body': json.dumps('Execution completed')
    }
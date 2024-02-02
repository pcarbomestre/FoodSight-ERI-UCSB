
# ------------------ Importing Libraries ------------------ #

import sys
from datetime import date, datetime, timedelta
import pandas as pd
import requests
import janitor
import json
import io
from io import BytesIO
import boto3 

# ------------------ AWS S3 parameters ------------------ #

s3 = boto3.client('s3')  # Initializing Amazon S3 client
bucket_name = 'foodsight-lambda'  # Name of the S3 bucket

key_path_all_hist_read = 'hist_data/hist_data_grasscast_gp_sw.csv'
key_path_gp_hist_read = 'hist_data/updated_hist_data_grasscast_gp.csv'
key_path_sw_hist_read = 'hist_data/updated_hist_data_grasscast_sw.csv'

key_path_all_forecast_read = 'forecast_data/forecast_data_grasscast_gp_sw.csv'
key_path_gp_forecast_read = 'forecast_data/forecast_data_grasscast_gp_clim.csv'
key_path_sw_forecast_read = 'forecast_data/forecast_data_grasscast_sw_clim.csv'

key_path_seasprcp_grid_read = 'spatial_data/seasprcp_grid.csv'
key_path_overlapping_gridids_read = 'spatial_data/overlapping_gridids.json'

# S3 loading functions
def read_csv_from_s3(bucket, key):
    csv_obj = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(BytesIO(csv_obj['Body'].read()))

# Function to read a JSON file from S3
def read_json_from_s3(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    json_obj = response['Body'].read().decode('utf-8')
    return pd.DataFrame(json.loads(json_obj))

# S3 saving function
def df_to_s3_csv(df, bucket, key):
    # Convert DataFrame to CSV in-memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    # Convert String buffer to Bytes buffer
    csv_buffer_bytes = io.BytesIO(csv_buffer.getvalue().encode())
    # Upload to S3
    s3.put_object(Bucket=bucket, Body=csv_buffer_bytes.getvalue(), Key=key)


# ------------------ Define functions ------------------#
# Predefined functions:

# Function to pull the latest forecast data from the Grass-Cast website
def download_forecast_lambda(year=date.today().year, region_code='gp', existing_df=None):
    base_url = "https://grasscast.unl.edu/data/csv/{year}/ANPP_forecast_summary_{region_code}_{year}_{month}_{day}.csv"
    month_names = {4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

    # List of shared columns
    shared_columns = ['fips', 'countystate', 'gridid', 'indx', 'year', 'meanndvigrid', 'meananppgrid', 
                    'ndvi_predict_below', 'npp_predict_below', 'npp_stdev_below', 'deltanpp_below', 
                    'pct_diffnpp_below', 'ndvi_predict_avg', 'npp_predict_avg', 'npp_stdev_avg', 
                    'deltanpp_avg', 'pct_diffnpp_avg', 'ndvi_predict_above', 'npp_predict_above', 
                    'npp_stdev_above', 'deltanpp_above', 'pct_diffnpp_above', 'report_date']

    start_date = datetime(year, 4, 1)  # Default start date is April 1st of the given year

    # If an existing dataframe is provided, find the next date after the latest report_date
    if existing_df is not None and not existing_df.empty:
        most_recent_report_date = pd.to_datetime(existing_df['report_date'].max()).year

        if most_recent_report_date != year :
            existing_df = None
        else:
            existing_df['report_date'] = pd.to_datetime(existing_df['report_date']).astype('datetime64[us]')
            last_date = existing_df['report_date'].max()
            start_date = last_date + timedelta(days=1)

    new_data_downloaded = False  # Flag to track if data is downloaded

    for month in range(start_date.month, 10):  # From starting month to September
        # Setting the end day of the month
        if month in [4, 6, 9]:  # April, June, September have 30 days
            end_day = 30
        else:
            end_day = 31

        for day in range(start_date.day if month == start_date.month else 1, end_day + 1):
            # Constructing the URL for each specific date
            url = base_url.format(year=year, region_code=region_code, month=month_names[month], day=day)
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"Data found and downloaded for date: {year}-{month}-{day}")
                    print(url)
                    # Reading the CSV into a Pandas dataframe
                    new_df = pd.read_csv(url)
                    # Create report_date variable in date format
                    report_date = datetime(year, month, day)
                    new_df['report_date'] = report_date
                    # Rename the columns to lowercase and replace spaces with underscores
                    new_df = new_df.clean_names()
                    # Filter the dataframe to include only the shared columns
                    new_df = new_df[shared_columns]

                    # Concatenate with the existing dataframe
                    if existing_df is not None:
                        existing_df = pd.concat([existing_df, new_df], ignore_index=True)
                    else:
                        existing_df = new_df

                    new_data_downloaded = True
                    return existing_df

                else:
                    print(f"No data available for date: {year}-{month}-{day}")
            except Exception as e:
                print(f"Error downloading file for date: {year}-{month}-{day}, Error: {e}")

    if new_data_downloaded is False:
        print(f"No new data downloaded for {region_code} region. Stopping execution.")
        return None


# Function to calculate ANPP based on climate outlook 
def calculate_NPP_predict_clim(row):
    Cat = row['cat']
    Prob = row['prob']
    NPP_predict_below = row['npp_predict_below']
    NPP_predict_above = row['npp_predict_above']
    NPP_predict_avg = row['npp_predict_avg']

    if Cat == 'EC':
        return NPP_predict_below * (1/3) + NPP_predict_avg * (1/3) + NPP_predict_above * (1/3)
    else:
        # Calculate remaining_prob
        remaining_prob = 1 - ((Prob / 100) + (1/3))
        if Cat == 'Below':
            return (NPP_predict_below * (Prob / 100)) + NPP_predict_avg * (1/3) + NPP_predict_above * remaining_prob
        elif Cat == 'Above':
            return (NPP_predict_above * (Prob / 100)) + NPP_predict_avg * (1/3) + NPP_predict_below * remaining_prob

def handler(event, context):

    # ------------------ Prepare Spatial Data ------------------#
    print("Reading spatial data...")
    # Read spatial data
    seasprcp_grid = read_csv_from_s3(bucket_name, key_path_seasprcp_grid_read)

    # ------------------ Pull new forecast data from GrassCast ------------------#

    # SW data
    print("Pulling SW data from GrassCast...")
    # Download the latest forecast data for the SW region
    # Load the previous forecast records (if any) to concatenate and set the start date 
    existing_df = read_csv_from_s3(bucket_name, key_path_sw_forecast_read)
    columns_to_exclude = ['cat', 'prob', 'npp_predict_clim']
    existing_df = existing_df[[col for col in existing_df.columns if col not in columns_to_exclude]]
    # Apply function
    grasscast_forecast_sw  = download_forecast_lambda(year=date.today().year, region_code='sw', existing_df=existing_df)

    # GP data
    print("Pulling GP data from GrassCast...")
    # Download the latest forecast data for the GP region
    # Load the previous forecast records (if any) to concatenate and set the start date
    existing_df = read_csv_from_s3(bucket_name, key_path_gp_forecast_read)
    columns_to_exclude = ['cat', 'prob', 'npp_predict_clim']
    existing_df = existing_df[[col for col in existing_df.columns if col not in columns_to_exclude]]
    # Apply function
    grasscast_forecast_gp = download_forecast_lambda(year=date.today().year, region_code='gp', existing_df=existing_df)

    # Stop execution if no new data was downloaded
    if grasscast_forecast_sw is None and grasscast_forecast_gp is None:
        print("No new data available. Stopping execution.")
        sys.exit()

    # ------------------ Apply updates for SW ------------------#

    if grasscast_forecast_sw is not None:
        print("Updating SW data...")

        # Add new climate related variables to the forecast dataset
        # Merge forecast data with grid based on Id
        grasscast_forecast_sw_clim = pd.merge(grasscast_forecast_sw, 
                                            seasprcp_grid[['gridid', 'cat', 'prob']], 
                                            left_on='gridid', right_on='gridid', how='left')
        # Apply function to calculate ANPP based on climate outlook to SW DataFrame
        grasscast_forecast_sw_clim['npp_predict_clim'] = grasscast_forecast_sw_clim.apply(calculate_NPP_predict_clim, axis=1)
        # Store the updated forecast dataset to be used in the following iteration to pull updated data from GrassCast
        df_to_s3_csv(grasscast_forecast_sw_clim, bucket_name, key_path_sw_forecast_read)

        # Update last record on the historical dataset based on new forecast data
        # Load last available historical data
        hist_sw = read_csv_from_s3(bucket_name, key_path_sw_hist_read)
        forecast_sw = grasscast_forecast_sw_clim
        # Assuming grasscast_forecast_sw_clim is already loaded as forecast_sw
        forecast_sw['report_date'] = pd.to_datetime(forecast_sw['report_date'])
        # Filter for the last day of May and the last day of the year
        last_day_may = forecast_sw[forecast_sw['report_date'].dt.month == 5].groupby('year')['report_date'].max()
        last_day_year = forecast_sw.groupby('year')['report_date'].max()
        # Group by 'year' and get the last 'report_date'
        max_dates_per_year = pd.concat([last_day_may, last_day_year])
        # Merge the DataFrames
        result = pd.merge(forecast_sw, max_dates_per_year, on=['year', 'report_date'])
        # Extract the month and assign seasons
        result['month'] = result['report_date'].dt.month
        result['season'] = result['month'].apply(lambda x: 'spring' if 4 <= x < 6 else 'summer')
        # Assign values to the new columns based on the season
        result['predicted_spring_anpp_lbs_ac'] = result.apply(lambda row: row['npp_predict_clim'] if row['season'] == 'spring' else None, axis=1)
        result['predicted_summer_anpp_lbs_ac'] = result.apply(lambda row: row['npp_predict_clim'] if row['season'] == 'summer' else None, axis=1)
        # Filter out years from hist_sw that are also present in forecast_sw
        forecast_years = forecast_sw['report_date'].dt.year.unique()
        hist_sw = hist_sw[~hist_sw['year'].isin(forecast_years)]
        # Select the specified columns
        selected_columns_hist = hist_sw[["gridid", "year", "predicted_spring_anpp_lbs_ac", "predicted_summer_anpp_lbs_ac"]]
        selected_columns_forecast = result[["gridid", "year", "predicted_spring_anpp_lbs_ac", "predicted_summer_anpp_lbs_ac"]]
        # Group and merge
        merged_selected_columns_forecast = selected_columns_forecast.groupby(['gridid', 'year'], as_index=False).first()
        hist_sw = pd.concat([selected_columns_hist, merged_selected_columns_forecast], ignore_index=True)
        # Store updated historical dataset for the next iteration
        df_to_s3_csv(hist_sw, bucket_name, key_path_sw_hist_read)


    # ------------------ Apply updates for GP ------------------#

    if grasscast_forecast_gp is not None:
        print("Updating GP data...")

        # Add new climate related variables to the forecast dataset
        # Merge forecast data with grid based on Id
        grasscast_forecast_gp_clim = pd.merge(grasscast_forecast_gp, 
                                            seasprcp_grid[['gridid', 'cat', 'prob']], 
                                            left_on='gridid', right_on='gridid', how='left')
        # Apply function to calculate ANPP based on climate outlook to SW DataFrame
        grasscast_forecast_gp_clim['npp_predict_clim'] = grasscast_forecast_gp_clim.apply(calculate_NPP_predict_clim, axis=1)
        
        # GP and SW grids overlap, so we need to remove the overlapping grids from the GP dataset which is the less informative (only one seasonal forecast)
        # Read in overlapping grid ids
        overlapping_ids = read_json_from_s3(bucket_name, key_path_overlapping_gridids_read)
        # Convert the 'gridid' in overlapping_ids to a set for faster lookup
        overlapping_ids_set = set(overlapping_ids['gridid'])
        # Create a boolean index for rows in combined_df where 'gridid' is not in overlapping_ids_set
        non_overlapping_index = ~grasscast_forecast_gp_clim['gridid'].isin(overlapping_ids_set)
        # Filter the combined_df using this index
        grasscast_forecast_gp_clim = grasscast_forecast_gp_clim[non_overlapping_index]
        # Store the updated forecast dataset to be used in the following iteration to pull updated data from GrassCast
        df_to_s3_csv(grasscast_forecast_gp_clim, bucket_name, key_path_gp_forecast_read)


        # Update last record on the historical dataset based on new forecast data
        # Load last available historical data
        hist_gp = read_csv_from_s3(bucket_name, key_path_gp_hist_read)
        forecast_gp = grasscast_forecast_gp_clim
        # Convert the 'Date' column to datetime if it's not
        forecast_gp['report_date'] = pd.to_datetime(forecast_gp['report_date'])
        # Filter the dataframe for the last day of the year
        max_dates_per_year = forecast_gp.groupby('year')['report_date'].max()
        # Merge the DataFrames
        result = pd.merge(forecast_gp, max_dates_per_year, on=['year', 'report_date'])
        # Assign the value from npp_predict_clim to anpp_lbs_ac or predicted_summer_anpp_lbs_ac
        result['anpp_lbs_ac'] = result.apply(lambda row: row['npp_predict_clim'], axis=1)
        # Filter out years from hist_sw that are also present in forecast_sw
        forecast_years = forecast_gp['report_date'].dt.year.unique()
        hist_gp = hist_gp[~hist_gp['year'].isin(forecast_years)]
        # Select the specified columns from hist_grasscast_gp
        selected_columns_hist = hist_gp[["gridid", "year", "anpp_lbs_ac"]]
        selected_columns_forecast = result[["gridid", "year", "anpp_lbs_ac"]]
        merged_selected_columns_forecast = selected_columns_forecast.groupby(['gridid', 'year'], as_index=False).first()
        hist_gp = pd.concat([selected_columns_hist, merged_selected_columns_forecast], ignore_index=True)
        # Store updated historical dataset for the next iteration
        df_to_s3_csv(hist_gp, bucket_name, key_path_gp_hist_read)


    # ------------------ Combine SW and GP dataframes ------------------#
    print("Combining SW and GP dataframes and preparing files...")

    # Read in files
    # Reloading the datasets to prevent potential problems associated when pulling GrassCast data from one of the regions
    hist_gp = read_csv_from_s3(bucket_name, key_path_gp_hist_read)
    hist_sw = read_csv_from_s3(bucket_name, key_path_sw_hist_read)
    forecast_gp = read_csv_from_s3(bucket_name, key_path_gp_forecast_read)
    forecast_sw = read_csv_from_s3(bucket_name, key_path_sw_forecast_read)

    # Concatenate GP and SW and create the final datasets to be used in the APP
    df_hist = pd.concat([hist_sw, hist_gp], ignore_index=True)
    df_forecast = pd.concat([forecast_sw, forecast_gp], ignore_index=True)
    # Store the resulting datasets to be read in the APP
    df_to_s3_csv(df_hist, bucket_name, key_path_all_hist_read)
    df_to_s3_csv(df_forecast, bucket_name, key_path_all_forecast_read)
    print("Execution completed successfully.")

    return {
        'statusCode': 200,
        'body': json.dumps('Execution completed')
    }

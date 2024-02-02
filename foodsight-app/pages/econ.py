
# ------------------------------------------------------------------------------
# Libraries
# Standard libraries
import json
import time
from datetime import datetime, timedelta

# Third-party libraries for data handling and numerical computations
import numpy as np
import pandas as pd
import geopandas as gpd

# Third-party libraries for visualization
import plotly.express as px 
import plotly.graph_objects as go

# Dash libraries for web applications
import dash
import dash_daq as daq
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

# Specific imports
from geopandas.tools import sjoin

# Imports
import requests
import boto3
s3 = boto3.client('s3')


dash.register_page(__name__)

# ------------------------------------------------------------------------------
# Import and pre-process data

# # ANPP Data
bucket_name = 'foodsight-lambda'  # Name of the S3 bucket
## Historic data
key_path_all_hist_read = 'hist_data/hist_data_grasscast_gp_sw.csv'
hist_response = s3.get_object(Bucket=bucket_name, Key=key_path_all_hist_read)
df_hist = pd.read_csv(hist_response['Body'])
## Forcast data
key_path_all_forecast_read = 'forecast_data/forecast_data_grasscast_gp_sw.csv'
forecast_response = s3.get_object(Bucket=bucket_name, Key=key_path_all_forecast_read)
df_forecast = pd.read_csv(forecast_response['Body'])

# Testing data from local. To speed up the deployment process
# df_hist = pd.read_csv("../testing_data/aws/hist_data_grasscast_gp_sw.csv")
# df_forecast = pd.read_csv("../testing_data/aws/forecast_data_grasscast_gp_sw.csv")

# --------------------------
# Spatial data

## AOI Grid
grid_geojson_path = 'static/grasscast_aoi_grid.geojson'
aoi_grid = gpd.read_file(grid_geojson_path).to_crs(epsg=4326).clean_names()
# Merging historical and forecast data with grid
gdf_hist = aoi_grid.merge(df_hist, left_on='gridid', right_on='gridid')
gdf_forecast = aoi_grid.merge(df_forecast, left_on='gridid', right_on='gridid')
# Historical plot slider range
YEARS = gdf_hist['year'].unique().tolist()
# Grid IDs and AOI dictionary
aoi_gridids_json_path = 'static/aoi_gridids.json'
with open(aoi_gridids_json_path, 'r') as file:
    aoi_gridids = json.load(file)

## Counties
counties_geojson_path = 'static/grasscast_counties.geojson'
with open(counties_geojson_path, 'r') as f:
    counties_geojson = json.load(f)
counties_gpd = gpd.read_file(counties_geojson_path).to_crs(epsg=4326)
counties_list = counties_gpd['name'].tolist()

# Mapbox token
token = open(".mapbox_token").read() # you will need your own token

# --------------------------
# Market data

## API call function
def get_data_from_mmnapi(api_key, endpoint):
    base_url = "https://marsapi.ams.usda.gov"
    try:
        response = requests.get(base_url + endpoint, auth=(api_key, ''))
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle request-related errors (e.g., network issues, invalid URLs, timeouts)
        return "The access to the API is temporarily unavailable"
    except ValueError as e:
        # Handle JSON decoding errors
        return "Error decoding JSON response from the API"

## API key
api_key = open(".mmn_api_token").read() 
# It is necessary to obtain an MMN token.
# More information at https://mymarketnews.ams.usda.gov/mymarketnews-api

## Cattle markets 
# (compiled post API evaluation for our Area of Interest)
with open('data/cattle_markets.json') as json_file:
    cattle_markets_list = json.load(json_file) 
# Cattle class, State and Markets list for dropdown menus
cattle_dropdown_options = []
cattle_type_dropdown_options = [{'label': 'All', 'value': 'All'}, {'label': 'Heifers', 'value': 'Heifers'}, {'label': 'Steers', 'value': 'Steers'}]
cattle_state_dropdown_options = list(set([item['market_location_state'] for item in cattle_markets_list]))
cattle_state_dropdown_options = sorted(cattle_state_dropdown_options)
cattle_state_dropdown_options.insert(0, "All")

## Last cattle market data
# (Stored in S3 bucket. Updated daily using lambda function)
key_path_read_econ = 'market_data/last_market_data.json'
response = s3.get_object(Bucket=bucket_name, Key=key_path_read_econ)
last_market_data = response['Body'].read().decode('utf-8')
daily_top_cattle_data = pd.DataFrame(json.loads(last_market_data))

# # Testing data from local. To speed up the deployment process
# with open('../testing_data/last_market_data.json') as json_file:
#     last_market_data = json.load(json_file) 
# daily_top_cattle_data = pd.DataFrame(last_market_data)
# daily_top_cattle_data = daily_top_cattle_data[daily_top_cattle_data['class'].isin(['Heifers', 'Steers'])]

## Hay markets
# (compiled post API evaluation for our Area of Interest)
with open('data/hay_markets.json') as json_file:
    hay_markets_list = json.load(json_file) 
# Hay class, grade, State and Markets list for dropdown menus
hay_dropdown_options = []
hay_class_dropdown_options = [{'label': 'All', 'value': 'All'}, {'label': 'All Alfalfas', 'value': 'All Alfalfas'}, {'label': 'All Grasses', 'value': 'All Grasses'}, {'label': 'Others', 'value': 'Others'}, {'label': 'Alfalfa/Grass Mix', 'value': 'Alfalfa/Grass Mix'}, {'label': 'Mixed Grass', 'value': 'Mixed Grass'}, {'label': 'Wheat', 'value': 'Wheat'}, {'label': 'Alfalfa/Oat Mix', 'value': 'Alfalfa/Oat Mix'}, {'label': 'Alfalfa/Orchard Mix', 'value': 'Alfalfa/Orchard Mix'}, {'label': 'Alfalfa/Timothy Mix', 'value': 'Alfalfa/Timothy Mix'}, {'label': 'Clover/Grass Mix', 'value': 'Clover/Grass Mix'}, {'label': 'Grass', 'value': 'Grass'}, {'label': 'Corn Stalk', 'value': 'Corn Stalk'}, {'label': 'Oat', 'value': 'Oat'}, {'label': 'Alfalfa', 'value': 'Alfalfa'}, {'label': 'Prairie/Meadow Grass', 'value': 'Prairie/Meadow Grass'}, {'label': 'Orchard Grass', 'value': 'Orchard Grass'}, {'label': 'Orchard/Timothy Grass', 'value': 'Orchard/Timothy Grass'}, {'label': 'Rye', 'value': 'Rye'}, {'label': 'Barley', 'value': 'Barley'}, {'label': 'Timothy Grass', 'value': 'Timothy Grass'}, {'label': 'Teff', 'value': 'Teff'}, {'label': 'Brome Grass', 'value': 'Brome Grass'}, {'label': 'Clover', 'value': 'Clover'}, {'label': 'Alfalfa/Wheat Mix', 'value': 'Alfalfa/Wheat Mix'}, {'label': 'Rye Grass', 'value': 'Rye Grass'}, {'label': 'Sorghum', 'value': 'Sorghum'}, {'label': 'Sudan', 'value': 'Sudan'}, {'label': 'Triticale', 'value': 'Triticale'}, {'label': 'Soybean', 'value': 'Soybean'}, {'label': 'Fescue Grass', 'value': 'Fescue Grass'}, {'label': 'Alfalfa /Rye Mix', 'value': 'Alfalfa /Rye Mix'}, {'label': 'Fodder', 'value': 'Fodder'}, {'label': 'Corn', 'value': 'Corn'}, {'label': 'Millet', 'value': 'Millet'}, {'label': 'Alfalfa/Triticale Mix', 'value': 'Alfalfa/Triticale Mix'}, {'label': 'Bluegrass', 'value': 'Bluegrass'}, {'label': 'Alfalfa/Bluegrass Mix', 'value': 'Alfalfa/Bluegrass Mix'}, {'label': 'Milo', 'value': 'Milo'}, {'label': 'Canary Reed', 'value': 'Canary Reed'}, {'label': 'Canola', 'value': 'Canola'}, {'label': 'Forage Mix-Two Way', 'value': 'Forage Mix-Two Way'}, {'label': 'Alfalfa/Forage Mix', 'value': 'Alfalfa/Forage Mix'}, {'label': 'Alfalfa Straw', 'value': 'Alfalfa Straw'}, {'label': 'Forage Mix-Three Way', 'value': 'Forage Mix-Three Way'}, {'label': 'Alfalfa/Sudan Mix', 'value': 'Alfalfa/Sudan Mix'}]
hay_grade_dropdown_options = [{'label': 'All', 'value': 'All'}, {'label': 'Good', 'value': 'Good'}, {'label': 'Fair/Good', 'value': 'Fair/Good'}, {'label': 'Fair', 'value': 'Fair'}, {'label': 'Good/Premium', 'value': 'Good/Premium'}, {'label': 'Utility/Fair', 'value': 'Utility/Fair'}, {'label': 'Utility', 'value': 'Utility'}, {'label': 'Premium', 'value': 'Premium'}, {'label': 'Supreme', 'value': 'Supreme'}, {'label': 'Premium/Supreme', 'value': 'Premium/Supreme'}]
hay_state_dropdown_options = list(set([item['market_location_state'] for item in hay_markets_list]))
hay_state_dropdown_options = sorted(hay_state_dropdown_options)
hay_state_dropdown_options.insert(0, "All")

## Time variable
# Get the current year
current_year = datetime.now().year
# Check if the maximum year in the DataFrame is not equal to the current year
# Correction for the case when forecast data has not been released for the current year yet (i.e., January-April)
if df_hist['year'].max() != current_year:
    # If not, set the current_year to the previous year
    current_year = current_year - 1

# ------------------------------------------------------------------------------
# Layout
layout = html.Div([
    html.Div(
        id="app-container",
        children=[
            html.Div(
                id="left-column",
                children=[
                    html.Div(
                        id="cattle-graph-container",
                        children=[
                            html.Div(
                                [
                                    html.H5("Cattle prices:", id='title-dropdown-container'),
                                    html.Div(
                                        id="grouped-dropdowns",
                                        children=[
                                            html.Div(
                                                [
                                                    html.P('Class:', className="dropdown-title"),
                                                    dcc.Dropdown(
                                                        id='cattle-type-dropdown-cattle',
                                                        options=cattle_type_dropdown_options,
                                                        value='Heifers',
                                                        className='my-custom-dropdown',
                                                    ),
                                                ],
                                                id='type-dropdown-container'
                                            ),
                                            html.Div(
                                                [
                                                    html.P('State:', className="dropdown-title"),
                                                    dcc.Dropdown(
                                                        id='state-dropdown-cattle',
                                                        options=cattle_state_dropdown_options,
                                                        value='All',
                                                        className='my-custom-dropdown'
                                                    ),
                                                ],
                                                id='state-dropdown-container'
                                            ),
                                            html.Div(
                                                [
                                                    html.P('Auction:', className="dropdown-title"),
                                                    dcc.Dropdown(
                                                        id='location-dropdown-cattle',
                                                        options=cattle_dropdown_options,
                                                        value='Cattlemen\'s Livestock Auction - Belen, NM',
                                                        className='my-custom-dropdown'
                                                    ),
                                                ],
                                                id='location-dropdown-container'
                                            ),
                                        ]
                                    ),
                                ],
                                className='econ-dropdown-container'
                            ),
                            html.Div(
                                [
                                    daq.BooleanSwitch(
                                        id='econ-toggle-switch',
                                        on=True,
                                        color="#4a517b"
                                    ),
                                    html.Div(id='switch-output'),
                                ],
                                id='econ-toggle-container'
                            ),
                            html.Div(id='tooltip-container'),
                            html.Div(
                                [
                                    dcc.Loading(
                                        id="loading-1",
                                        type="circle",
                                        children=dcc.Graph(
                                            id='box-trend-graph',
                                            config={'displayModeBar': False},
                                            style={'visibility': 'hidden'}
                                        ),
                                    )
                                ]
                            ),
                            html.Div(
                                [
                                    html.Button('All', id='btn-all', n_clicks=1, className='button-style'),
                                    html.Button('2Y', id='btn-2yr', n_clicks=0, className='button-style'),
                                    html.Button('1Y', id='btn-1yr', n_clicks=0, className='button-style'),
                                    html.Button('6M', id='btn-6mo', n_clicks=0, className='button-style'),
                                    html.Button('2M', id='btn-2mo', n_clicks=0, className='button-style'),
                                ],
                                className='button-container'
                            ),
                            html.Div(id='hidden-div-econ', style={'display': 'none'}),
                            html.Div(
                                [
                                    html.H5("Top auction markets:", id='title-table-econ-container'),
                                    dbc.Tooltip(
                                        "The table below presents the top markets that have data available from the past 15 days, filtered by the selected 'State.' It includes the name of the market, the date of the most recent auction, and the average price on that date for the specified 'Class.'",
                                        target="title-table-econ-container",
                                        id="top-markets-table-tooltip",
                                        placement="top",
                                    ),
                                    dcc.Loading(
                                        id="loading-2",
                                        type="circle",
                                        children=dcc.Graph(
                                            id='table-econ',
                                            config={'displayModeBar': False},
                                            style={'visibility': 'hidden'}
                                        ),
                                    )
                                ],
                                id="market-table-container"
                            )
                        ],
                    ),
                    html.Div([html.Div(id='output-api-data', children={})]),
                ],
            ),
            html.Div(
                id="right-column",
                children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    dbc.Tooltip(
                                        "The graph below displays the relationship between price and weight for the most recent auction day of the selected market.",
                                        target="price-weight-title",
                                        id="price-weight-tooltip",
                                        placement="top",
                                    ),
                                    html.Div(
                                        [
                                            html.P(
                                                "Price vs Weight (lbs), last day recorded:",
                                                id="price-weight-title"
                                            ),
                                            dcc.Loading(
                                                id="loading-3",
                                                type="circle",
                                                children=dcc.Graph(
                                                    id='price-weight-graph',
                                                    config={'displayModeBar': False},
                                                    style={'visibility': 'hidden'}
                                                ),
                                            )
                                        ]
                                    )
                                ],
                                id='price-weight-graph-container',
                                className='mini_container_spatial'
                            ),
                            html.Div(
                                [
                                    dcc.Loading(
                                        id="loading-1",
                                        type="circle",
                                        children=html.Div(
                                            [
                                                html.Div(id='forecas-summary-box'),
                                                html.Div(
                                                    [
                                                        dcc.Link(
                                                            children=html.Button(
                                                                '+ Forecast info',
                                                                id='btn-forecast-info',
                                                                n_clicks=0,
                                                                className='button-style-forecast'
                                                            ),
                                                            href='/forecast',
                                                            className="page-link"
                                                        ),
                                                    ],
                                                    className='button-container-econ'
                                                ),
                                            ]
                                        ),
                                    ),
                                ],
                                id='forecast_summary',
                                className='mini_container_spatial'
                            ),
                        ],
                        id='info-container2',
                    ),
                    html.Div(
                        id="hay-graph-container",
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H5("Hay prices:", id='hay-title-dropdown-container'),
                                            html.Div(
                                                id="grouped-dropdowns-hay",
                                                children=[
                                                    html.Div(
                                                        [
                                                            html.P('Class:', className="dropdown-title"),
                                                            dcc.Dropdown(
                                                                id='hay-class-dropdown',
                                                                options=hay_class_dropdown_options,
                                                                value='All',
                                                                className='my-custom-dropdown',
                                                            ),
                                                        ],
                                                        id='class-dropdown-container'
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.P('Grade:', className="dropdown-title"),
                                                            dcc.Dropdown(
                                                                id='hay-grade-dropdown',
                                                                options=hay_grade_dropdown_options,
                                                                value='All',
                                                                className='my-custom-dropdown',
                                                            ),
                                                        ],
                                                        id='grade-dropdown-container'
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.P('State:', className="dropdown-title"),
                                                            dcc.Dropdown(
                                                                id='state-dropdown-hay',
                                                                options=hay_state_dropdown_options,
                                                                value='All',
                                                                className='my-custom-dropdown'
                                                            ),
                                                        ],
                                                        id='hay-state-dropdown-container'
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.P('Auction:', className="dropdown-title"),
                                                            dcc.Dropdown(
                                                                id='location-dropdown-hay',
                                                                options=hay_dropdown_options,
                                                                value='Rock Valley Hay Auction (2)',
                                                                className='my-custom-dropdown'
                                                            ),
                                                        ],
                                                        id='hay-location-dropdown-container'
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className='econ-dropdown-container'
                                    ),
                                    html.Div(
                                        [
                                            dcc.Loading(
                                                id="loading-4",
                                                type="circle",
                                                children=dcc.Graph(
                                                    id='indicator-hay-graph',
                                                    config={'displayModeBar': False},
                                                    style={'visibility': 'hidden'}
                                                ),
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Button('All', id='btn-all-hay', n_clicks=1, className='button-style'),
                                            html.Button('2Y', id='btn-2yr-hay', n_clicks=0, className='button-style'),
                                            html.Button('1Y', id='btn-1yr-hay', n_clicks=0, className='button-style'),
                                            html.Button('6M', id='btn-6mo-hay', n_clicks=0, className='button-style'),
                                            html.Button('2M', id='btn-2mo-hay', n_clicks=0, className='button-style'),
                                        ],
                                        className='button-container'
                                    ),
                                ]
                            ),
                            html.Div(id='hidden-div-hay', style={'display': 'none'}),
                        ],
                    ),
                ],
            ),
        ],
    ),
])


# ------------------------------------------------------------------------------
# Callbacks

## ----------------------------------------
## Callbacks for Cattle data

# --------------------------
# Cattle API Data

# Select dropdown cattle market based on State
@callback(
    Output('location-dropdown-cattle', 'options'),
    Input('state-dropdown-cattle', 'value')
)
def update_markets(selected_state):
    if selected_state == "All":
        markets = [item['market_location_name'] for item in cattle_markets_list]
    else:
        markets = [item['market_location_name'] for item in cattle_markets_list if item['market_location_state'] == selected_state]
    
    markets_sorted = sorted(markets)
    
    return [{'label': market, 'value': market} for market in markets_sorted]


# Callback to update data description based on toggle switch
@callback(
    [Output('switch-output', 'children'),
     Output('tooltip-container', 'children')],
    Input('econ-toggle-switch', 'on')
)
def update_output_and_tooltip(on):
    if on:
        return "Daily average prices", dbc.Tooltip(
            "Nominal prices averaged across all transactions by date. Red indicates a market decline over the selected time range. Green corresponds a market rise from the first to the last record selected.",
            target="switch-output",
            id="switch-output-tooltip"
        )
    else:
        return "Monthly prices", dbc.Tooltip(
            "Nominal prices aggregated by month. Months where prices decrease from the first to the last record are shown in red. Conversely, months with a price increase are shown in green. Outliers not displayed.",
            target="switch-output",
            id="switch-output-tooltip"
        )

# Callback to update time range active button
@callback(
    [Output('btn-all', 'style'),
     Output('btn-2yr', 'style'),
     Output('btn-1yr', 'style'),
     Output('btn-6mo', 'style'),
     Output('btn-2mo', 'style')],
    [Input('btn-all', 'n_clicks'),
     Input('btn-2yr', 'n_clicks'),
     Input('btn-1yr', 'n_clicks'),
     Input('btn-6mo', 'n_clicks'),
     Input('btn-2mo', 'n_clicks')]
)
def update_active_button(btn_all, btn_2yr, btn_1yr, btn_6mo, btn_2mo):
    
    default_style = {
        'backgroundColor': 'transparent',
        'color': '#dbe5f3'
    }

    active_style = {
        'backgroundColor': '#dbe5f3',
        'color': '#282b3f'
    }

    # Get the id of the button that was clicked
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # If no buttons have been pressed yet, return default styles with btn-all set to active
    if not ctx.triggered:
        styles = [default_style for _ in range(5)]
        styles[0] = active_style  # Make btn-all active
        return styles

    # Dictionary to map button IDs to their index in the vals list
    button_indices = {
        'btn-all': 0,
        'btn-2yr': 1,
        'btn-1yr': 2,
        'btn-6mo': 3,
        'btn-2mo': 4
    }

    # Index of the button that was clicked
    active_button_index = button_indices[button_id]
    # Start with all buttons having the default style
    styles = [default_style for _ in range(5)]
    # Set the active style for the clicked button
    styles[active_button_index] = active_style

    return styles


# Callback to generate update the trend and candlestick char for cattle data
@callback(
    [Output('box-trend-graph', 'figure'),
     Output('hidden-div-econ', 'children'),
     Output('box-trend-graph', 'style')],
    [Input('location-dropdown-cattle', 'value'),
     Input('cattle-type-dropdown-cattle', 'value'),
     Input('btn-all', 'n_clicks'),
     Input('btn-2yr', 'n_clicks'),
     Input('btn-1yr', 'n_clicks'),
     Input('btn-6mo', 'n_clicks'),
     Input('btn-2mo', 'n_clicks'),
     Input('econ-toggle-switch', 'on'),
     State('hidden-div-econ', 'children')],
)
def update_cattle(location, cattle_type, n1, n2, n3, n4, n5, econ_toggle_switch_on, last_btn):
    ctx = dash.callback_context

    ## Get data from API call
    # Find the corresponding slug_id for the selected_location_name
    selected_slug_id = next(item['slug_id'] for item in cattle_markets_list if item['market_location_name'] == location)
    # Adjust the class parameter based on the selected value
    if cattle_type == "All":
        cattle_class = "class=Heifers,Steers"
    else:
        cattle_class = f"class={cattle_type}"

    # Make the API call
    endpoint = f"/services/v1.2/reports/{selected_slug_id}?q=commodity=Feeder Cattle;{cattle_class}"
    data = get_data_from_mmnapi(api_key, endpoint)

    # Check if API works
    if isinstance(data, str) or not data.get("results"):
        # Return a figure with the "The access to the API is temporarily unavailable" message
        fig = go.Figure()
        fig.add_annotation(
            text="API access is temporarily unavailable",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="white")
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0, 
                        autoexpand=True))
        
        fig.update_yaxes(visible=False, showticklabels=False, showgrid=False)
        fig.update_xaxes(visible=False, showticklabels=False, showgrid=False)

        return fig, last_btn, {}
    
    
    else:
        # Process data if API works and data has been pulled
        daily_cattle_sw_location = pd.DataFrame(data["results"])
        daily_cattle_sw_location['report_date'] = pd.to_datetime(daily_cattle_sw_location['report_date'])
        # Difference between the latest and earliest dates
        max_date = daily_cattle_sw_location['report_date'].max()
        min_date = daily_cattle_sw_location['report_date'].min()
        # The difference in months
        months_difference = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month

        # Set conditionals based on triggered elements to update the displayed data
        if not ctx.triggered:
            months = months_difference
            last_btn = 'btn-all'
        else:
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            # Dropdown menus triggers
            if triggered_id == 'location-dropdown-cattle' and last_btn is not None:
                triggered_id = last_btn
            if triggered_id == 'cattle-type-dropdown-cattle' and last_btn is not None:
                triggered_id = last_btn
            # toggle switch trigger
            if triggered_id == 'econ-toggle-switch' and last_btn is not None:
                triggered_id = last_btn
            # Time range buttons triggers
            if triggered_id == 'btn-all':
                months = months_difference
                last_btn = 'btn-all'
            elif triggered_id == 'btn-2yr':
                months = 24
                last_btn = 'btn-2yr'
            elif triggered_id == 'btn-1yr':
                months = 12
                last_btn = 'btn-1yr'
            elif triggered_id == 'btn-6mo':
                months = 6
                last_btn = 'btn-6mo'
            elif triggered_id == 'btn-2mo':
                months = 2
                last_btn = 'btn-2mo'

        ## Generate charts based on toggle switch
        # Line graph creation (switch on)
        if econ_toggle_switch_on:

            # Line graph data wrangling
            grouped_df = daily_cattle_sw_location.groupby('report_date')['avg_price'].mean().reset_index()
            grouped_df = grouped_df.sort_values('report_date')
            max_date = grouped_df['report_date'].max()
            one_year_before_max_date = max_date - pd.DateOffset(months=months)
            last_year_df = grouped_df[grouped_df['report_date'] >= one_year_before_max_date]
            price_change = last_year_df['avg_price'].iloc[-1] - last_year_df['avg_price'].iloc[0]
            color = 'green' if price_change >= 0 else 'red'
            fillcolor_base = '0,128,0' if price_change >= 0 else '128,0,0'

            # Create Figure
            fig = go.Figure()

            # Gradient Fill for Scatter Plot
            num_layers = 20
            base_y = last_year_df['avg_price'].min()

            # Plotly library does not support gradient fill for line graphs
            # The following loop provides a way of creating transparent gradient below the line graph
            for i in range(num_layers - 1):
                fraction = i / num_layers
                y_values = base_y + (last_year_df['avg_price'] - base_y) * fraction
                gradient_fillcolor = f'rgba({fillcolor_base},{(i + 1) / num_layers * 0.2})'  # Varying the opacity
                fig.add_trace(go.Scatter(x=last_year_df['report_date'], y=y_values,
                                        mode='lines', 
                                        fill='tonexty', line=dict(width=0),
                                        fillcolor=gradient_fillcolor,
                                        hoverinfo='none'
                                ))

            # The topmost gradient layer to match exactly with the line graph's y-values
            fig.add_trace(go.Scatter(x=last_year_df['report_date'], y=last_year_df['avg_price'],
                                    mode='lines', 
                                    fill='tonexty', line=dict(width=0),
                                    fillcolor=f'rgba({fillcolor_base},0.2)',
                                    hoverinfo='none'
                            ))
            # Add Line Chart on top of Gradient
            fig.add_trace(go.Scatter(x=last_year_df['report_date'], y=last_year_df['avg_price'], 
                                    mode='lines', 
                                    line=dict(color=color),
                                    name='avg_price',
                                    hovertemplate='%{x|%Y-%m-%d}<br>Daily average price: $%{y:.2f}<extra></extra>'
                            ))

            # Add indicator (most recent value and % change)
            fig.add_trace(go.Indicator(
                mode="number+delta",
                value=last_year_df['avg_price'].iloc[-1],
                delta={'reference': last_year_df['avg_price'].iloc[0], 'relative': True, 'valueformat': '.1%', 'font': {'size': 17}},
                number={'valueformat': '$.1f', 'font':{'size': 22, 'color': '#dbe5f3'}},
                domain={'y': [0.99, 1], 'x': [0.8, 0.9]}
            ))
        
            min_price = last_year_df['avg_price'].min()
            max_price = last_year_df['avg_price'].max()
            padding = (max_price - min_price) * 0.1

            # Update layout
            fig.update_yaxes(
                range=[min_price - padding, max_price + padding+20], 
                showticklabels=True, showgrid=False,
                tickfont=dict(color='#dbe5f3'),  # Updates tick label color
                title_font=dict(color='#dbe5f3'),  # Updates axis title color
                title_text="$/cwt",
                ticksuffix="     ",
                zeroline=False 
            )

            fig.update_xaxes(showticklabels=True, showgrid=False,
                            tickfont=dict(color='#dbe5f3'),
                            zeroline=False )
    
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=False,
                yaxis_showgrid=False,
                showlegend=False,
                margin=dict(l=0, r=0, t=19, b=0, 
                            autoexpand=True)
            )
            
            return fig, last_btn, {}
            

        # Candlestick char creation (monthly aggregated data) (switch off)
        else:

            # Candlestick graph data wrangling
            max_date = daily_cattle_sw_location['report_date'].max()
            one_year_before_max_date = max_date - pd.DateOffset(months=months)
            last_year_df = daily_cattle_sw_location[daily_cattle_sw_location['report_date'] >= one_year_before_max_date]
            last_year_df['yearmonth'] = last_year_df['report_date'].dt.to_period('M')
            last_year_df['yearmonth'] = last_year_df['yearmonth'].astype(str)
            last_year_df = last_year_df.sort_values(['yearmonth', 'report_date'])

            def calculate_trend(df):
                if len(df) > 1:
                    average_price = df['avg_price'].mean()
                    if df['avg_price'].iloc[-1] > average_price:
                        return 'Increasing'
                    elif df['avg_price'].iloc[-1] < average_price:
                        return 'Decreasing'
                return np.nan

            trend_df = last_year_df.groupby('yearmonth').apply(calculate_trend).reset_index()
            trend_df.columns = ['yearmonth', 'Trend']
            last_year_df = pd.merge(last_year_df, trend_df, on='yearmonth', how='left')
            last_year_df = last_year_df.dropna(subset=['Trend'])
            color_map = {'Increasing': 'green', 'Decreasing': 'red'}
            last_year_df['Color'] = last_year_df['Trend'].map(color_map)

            # Outliers may distort the boxplot, not providing relevant information since these are not representative of the market trends.
            # Therefore, we opted to remove outliers from the boxplot. These may result in slight differences on max values among the Candlestick and the line graph..
            # Define the function to remove outliers
            def remove_outliers(df):
                Q1 = df['avg_price'].quantile(0.25)
                Q3 = df['avg_price'].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                return df[(df['avg_price'] >= lower_bound) & (df['avg_price'] <= upper_bound)]

            # Apply the function on the last_year_df grouped by yearmonth
            filtered_last_year_df = last_year_df.groupby('yearmonth').apply(remove_outliers).reset_index(drop=True)

            # Create Figure
            fig = go.Figure()
            for i in filtered_last_year_df['yearmonth'].unique():
                fig.add_trace(
                    go.Box(
                        y=filtered_last_year_df[filtered_last_year_df['yearmonth'] == i]['avg_price'],
                        name=i,
                        marker_color=filtered_last_year_df[filtered_last_year_df['yearmonth'] == i]['Color'].iloc[0],
                        boxmean=True,
                        boxpoints=False
                    )
                )
                
            # Update layout
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_showgrid=False,
                yaxis_showgrid=False,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0, 
                            autoexpand=True)
            )

            fig.update_xaxes(tickfont=dict(color='#dbe5f3'))

            fig.update_yaxes(
                tickfont=dict(color='#dbe5f3'),
                title_font=dict(color='#dbe5f3'),
                title_text="$/cwt",
                ticksuffix="     "
            )

            return fig, last_btn, {}


# --------------------------
# Top Cattle markets table

@callback(
    [Output('table-econ', 'figure'),
     Output('table-econ', 'style')],
    [Input('state-dropdown-cattle', 'value'),
     Input('cattle-type-dropdown-cattle', 'value')]
)
def update_table(selected_state, cattle_type):
    
    # If type is not "All", filter by class and grade
    if cattle_type != "All":
        daily_cattle_list = daily_top_cattle_data[daily_top_cattle_data['class']== cattle_type]
    else:
        daily_cattle_list = daily_top_cattle_data

    # If state is not "All", filter daily_cattle_list by state
    if selected_state != "All":
        daily_cattle_list = daily_cattle_list[daily_cattle_list['market_location_state'] == selected_state]

    # Limit data displayed to that updated within the last 15 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=15)
    daily_cattle_list['report_date'] = pd.to_datetime(daily_cattle_list['report_date'])
    daily_cattle_list = daily_cattle_list[(daily_cattle_list['report_date'] >= start_date) & (daily_cattle_list['report_date'] <= end_date)]

    # Get the average price for each market on the last day recorded
    grouped_df = daily_cattle_list.groupby(['market_location_name', 'report_date'])['avg_price'].mean().reset_index()
    # Limit data displayed to 5 markets, sort it and define the format of the avg_price and report_date variables
    df = grouped_df.sort_values('avg_price', ascending=False).head(5)
    df['avg_price'] = df['avg_price'].round(2)
    df['report_date'] = pd.to_datetime(df['report_date']).dt.strftime('%b %d')
    top5_df = df.sort_values(by='avg_price', ascending=False).head(5)

    # Create Figure
    fig = go.Figure(data=[go.Table(
        columnwidth = [6, 1.5, 2.5], 
        header=dict(values=[], 
                    fill_color='rgba(0,0,0,0)', 
                    line_color='rgba(0,0,0,0)', 
                    line_width=0),  # hide column names and lines, set header colors
        cells=dict(values=[top5_df['market_location_name'], top5_df['report_date'], top5_df['avg_price'].map('$ {:,.2f} /cwt'.format)],
                    fill_color='rgba(0,0,0,0)',  # set cell fill color to transparent
                    line_color='rgba(0,0,0,0)',  # set line color to transparent
                    line_width=0,  # set line width to 0
                    font_color= 'white',
                    align='left')
                    )
                ]
            )

    # Update layout
    fig.update_layout(
        autosize=False,
        height=120, 
        paper_bgcolor='rgba(0,0,0,0)',  # set paper background to transparent
        plot_bgcolor='rgba(0,0,0,0)',  # set plot background to transparent
        margin=dict(l=0, r=0, t=0, b=0, 
                    autoexpand=True)
    )

    return fig, {}


# --------------------------
# Cattle Weight vs Price chart

@callback(
    [Output('price-weight-graph', 'figure'),
     Output('price-weight-graph', 'style')],
    [Input('location-dropdown-cattle', 'value'),
     Input('cattle-type-dropdown-cattle', 'value')]  
)
def update_price_weight(location, type):

    #If type is not "All", filter by class and grade
    if type != "All":
        daily_cattle_type = daily_top_cattle_data[daily_top_cattle_data['class']== type]
    else:
        daily_cattle_type = daily_top_cattle_data

    # Prepare data
    # Filter the rows based on location and date conditions
    filtered_data = daily_cattle_type[daily_cattle_type['market_location_name'] == location]
    filtered_data['report_date'] = pd.to_datetime(filtered_data['report_date'])
    max_date = filtered_data['report_date'].max()
    filtered_data = filtered_data[(filtered_data['report_date'] == max_date)]
    
    # Reshape the dataframe to facilitate representation
    weights_df = filtered_data[['avg_weight_min', 'avg_weight_max']].melt(var_name='variable', value_name='weight')
    prices_df = filtered_data[['avg_price_min', 'avg_price_max']].melt(var_name='variable', value_name='price')

    # Group weights into bins for clearer visualization of the data
    max_weight = weights_df['weight'].max()
    bins = np.arange(0, max_weight + 51, 50)  # +51 to include the max_weight
    weights_df['weight_grouped'] = pd.cut(weights_df['weight'], bins=bins, right=True)
    weights_df['weight_rounded'] = weights_df['weight_grouped'].apply(lambda x: x.right).astype(int)

    # Create the final dataframe to represent by combining weights and prices
    final_df = pd.DataFrame({
        'weight': weights_df['weight_rounded'],
        'price': prices_df['price']
    })

    # Create Color Gradient from green to red to represent the price trend
    unique_weights = sorted(final_df['weight'].unique())
    box_data = []
    medians = []
    # Collect the median prices for each weight and store in medians list
    for weight in unique_weights:
        price_for_weight = final_df[final_df['weight'] == weight]['price']
        medians.append(np.median(price_for_weight))
    # Normalize the median values between 0 and 1
    normalized_medians = (medians - np.min(medians)) / (np.max(medians) - np.min(medians))
    # Map normalized values to a color gradient
    colors = [(int(255 * (1 - val)), int(255 * val), 0) for val in normalized_medians]

    # Create the boxplot for each weight
    for weight, color in zip(unique_weights, colors):
        price_for_weight = final_df[final_df['weight'] == weight]['price']
        box_data.append(
            go.Box(
                y=price_for_weight, 
                name=str(weight), 
                line=dict(color='rgb{}'.format(color)),
                boxpoints='outliers',  # this ensures only outliers are affected
                marker=dict(
                    color='rgb{}'.format(color), 
                    outliercolor='rgba(255, 0, 0, 0.6)',  
                    line=dict(
                        outliercolor='rgba(255, 0, 0, 0.6)',
                        outlierwidth=0.5
                    ),
                    size=3  # size of the outliers
                ),
            )
        )

    # Create Figure
    fig = go.Figure(data=box_data)
    fig.update_yaxes(showticklabels=True, showgrid=False, tickfont=dict(size=10))
    fig.update_xaxes(showticklabels=True, showgrid=False, tickangle=290,tickfont=dict(size=9))

    # Update layout
    fig.update_layout(
        yaxis_title="$/cwt",
        xaxis=dict(
            type='category',
            title_font=dict(color='#dbe5f3',size=10),
            tickfont=dict(color='#dbe5f3'),
            fixedrange=True,
            zeroline=False 
        ),
        yaxis=dict(
            title_font=dict(color='#dbe5f3',size=10),
            tickfont=dict(color='#dbe5f3'),
            fixedrange=True,
            zeroline=False 
        ),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0, autoexpand=True),
    )

    return fig, {}


## ----------------------------------------
## Callbacks for ANPP Forecast summary

## Helper function for the forecast summary callback
# Forecast data wrangling
def create_forecast_summaries(dff, current_year):

    # Convert 'report_date' to datetime format
    dff['report_date'] = pd.to_datetime(dff['report_date'])

    forecast_summaries = []

    # Loop through each unique date
    for date in dff['report_date'].unique():
        dff_year = dff[dff['report_date'] == date]
        forecast_summary_dict = dff_year.iloc[0].to_dict()  # get first row values, which then will be overwritten

        # Update the dictionary with mean values for specified columns
        forecast_summary_dict.update({
            'report_date': date,
            'npp_predict_below': dff_year['npp_predict_below'].mean(),
            'npp_predict_avg': dff_year['npp_predict_avg'].mean(),
            'npp_predict_above': dff_year['npp_predict_above'].mean(),
            'prob': dff_year['prob'].mean(),
            'npp_predict_clim': dff_year['npp_predict_clim'].mean(),
            'cat': dff_year['cat'].mode()[0] if not dff_year['cat'].mode().empty else None
        })

        forecast_summaries.append(forecast_summary_dict)

    # Convert the summaries to a DataFrame
    df_plot = pd.DataFrame(forecast_summaries)
    # Filter for the current or previous year
    df_plot = df_plot[df_plot['year'] == current_year]

    return df_plot


# Summary box callback
@callback(
    Output("forecas-summary-box", "children"),
    Input('autocomplete-input', 'value'),
)
def econ_update_summary(by_county):
    
    # See process_summary_boxes() and update_summary_boxes() in forecast.py for more details

    if by_county is not None:
    
        polygon = counties_gpd.loc[counties_gpd['name'] == by_county]
        columns_to_keep_forcast = ['gridid','report_date','npp_predict_below', 'npp_predict_avg','npp_predict_above',
                                'cat', 'prob','year', 'npp_predict_clim','meananppgrid','geometry']
        dff_forcast_polygon = sjoin(gdf_forecast[columns_to_keep_forcast], polygon, how='inner', predicate='intersects')
        df_plot = create_forecast_summaries(dff_forcast_polygon,current_year)
        latest_date_rows = df_plot[df_plot['report_date'] == df_plot['report_date'].max()]
            
    cat_descriptions = {
        'Below': 'drier than normal',
        'Above': 'rainier than normal',
        'EC': 'normal',
    }

    for _, row in latest_date_rows.iterrows():
        
        predict = row['npp_predict_clim']
        mean = row['meananppgrid']
        cat = row['cat']
        cat_description = cat_descriptions[cat]
        difference = predict - mean
        percentage = (abs(difference) * 100) / mean
        direction = "higher" if difference > 0 else "lower"
        direction = "higher" if difference > 0 else "lower"
        arrow_direction = "up" if direction == "higher" else "down"

        month = datetime.now().month
        if 4 <= month <= 5:
            season = 'for this spring'
            verb = 'is'
            verb2 = 'will be'
        elif 6 <= month <= 9:
            season = 'for this summer'
            verb = 'is'
            verb2 = 'will be'
        elif 10 <= month <= 12:
            season = 'for this summer'
            verb = 'was'
            verb2 = 'was'
        else:
            season = 'last season'
            verb = 'was'
            verb2 = 'was'

        variables_style = {"color": "#2e55a3", "font-size": "20px","vertical-align": "middle"}
        text_style = {"color": "black","vertical-align": "middle"}

        box = html.Div([
            html.Span(f"In {by_county}, the expected production {season} {verb} about", style=text_style),
            html.Span(f" {round(predict,0):.0f}", style=variables_style),
            html.Span(" lb/ac. ", style=text_style),
            html.Span(f"Being this year's weather {cat_description}", style=text_style),
            html.Span(f", the production {verb2}  ", style=text_style),
            html.Span(f" {round(percentage,0):.0f}% ", style=variables_style),
            html.Span(f"{direction}   ", style=variables_style),
            html.Span(className=f"fa fa-arrow-{arrow_direction}", style=variables_style),
            html.Span("  than the historical average.")
        ])

    return box


## ----------------------------------------
## Callbacks for Hay data

# Select dropdown hay market based on State
@callback(
    Output('location-dropdown-hay', 'options'),
    Input('state-dropdown-hay', 'value')
)
def update_markets(selected_state):

    if selected_state == "All":
        markets = [item['market_location_name'] for item in hay_markets_list]
    else:
        markets = [item['market_location_name'] for item in hay_markets_list if item['market_location_state'] == selected_state]
    
    markets_sorted = sorted(markets)
    
    return [{'label': market, 'value': market} for market in markets_sorted]

# Callback to update time range active button
@callback(
    [Output('btn-all-hay', 'style'),
     Output('btn-2yr-hay', 'style'),
     Output('btn-1yr-hay', 'style'),
     Output('btn-6mo-hay', 'style'),
     Output('btn-2mo-hay', 'style')],
    [Input('btn-all-hay', 'n_clicks'),
     Input('btn-2yr-hay', 'n_clicks'),
     Input('btn-1yr-hay', 'n_clicks'),
     Input('btn-6mo-hay', 'n_clicks'),
     Input('btn-2mo-hay', 'n_clicks')]
)
def update_active_button(btn_all, btn_2yr, btn_1yr, btn_6mo, btn_2mo):
    
    default_style = {
        'backgroundColor': 'transparent',
        'color': '#dbe5f3'
    }

    active_style = {
        'backgroundColor': '#dbe5f3',
        'color': '#282b3f'
    }

    # Get the id of the button that was clicked
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # If no buttons have been pressed yet, return default styles with btn-all-hay set to active
    if not ctx.triggered:
        styles = [default_style for _ in range(5)]
        styles[0] = active_style  # Make btn-all-hay active
        return styles

    # Dictionary to map button IDs to their index in the vals list
    button_indices = {
        'btn-all-hay': 0,
        'btn-2yr-hay': 1,
        'btn-1yr-hay': 2,
        'btn-6mo-hay': 3,
        'btn-2mo-hay': 4
    }

    # Index of the button that was clicked
    active_button_index = button_indices[button_id]
    # Start with all buttons having the default style
    styles = [default_style for _ in range(5)]
    # Set the active style for the clicked button
    styles[active_button_index] = active_style

    return styles
    

# Callback to generate and update the hay graph
@callback(
    [Output('indicator-hay-graph', 'figure'),
     Output('hidden-div-hay', 'children'),
     Output('indicator-hay-graph', 'style')],
    [Input('location-dropdown-hay', 'value'),
     Input('hay-class-dropdown', 'value'),
     Input('hay-grade-dropdown', 'value'),
     Input('btn-all-hay', 'n_clicks'),
     Input('btn-2yr-hay', 'n_clicks'),
     Input('btn-1yr-hay', 'n_clicks'),
     Input('btn-6mo-hay', 'n_clicks'),
     Input('btn-2mo-hay', 'n_clicks'),
     State('hidden-div-hay', 'children')],
)
def update_hay(location, hay_class, hay_grade, n1, n2, n3, n4, n5, last_btn_hay):
    ctx = dash.callback_context

    ## Get data from API call
    # Find the corresponding slug_id for the selected_location_name
    selected_slug_id = next(item['slug_id'] for item in hay_markets_list if item['market_location_name'] == location)
    
    # Adjust the grade parameter based on the selected value
    if hay_grade == "All":
        hay_grade_search = "" #f"quality={','.join(actual_hay_grades)}"
    else:
        hay_grade_search = f"quality={hay_grade}"

    # Adjust the class parameter based on the selected value
    hay_classes = [option['value'] for option in hay_class_dropdown_options]
    actual_hay_classes = [h for h in hay_classes if h not in ["All", "All Alfalfas", "All Grasses", "Others"]]

    if hay_class == "All":
        hay_class_search = ""  #f"class={','.join(actual_hay_classes)}"
    elif hay_class == "All Alfalfas":
        hay_class_search = 'class=' + ','.join([h for h in actual_hay_classes if 'Alfalfa' in h])
    elif hay_class == "All Grasses":
        hay_class_search = 'class=' + ','.join([h for h in actual_hay_classes if 'Grass' in h])
    elif hay_class == "Others":
        hay_class_search = 'class=' + ','.join([h for h in actual_hay_classes if 'Alfalfa' not in h and 'Grass' not in h])
    else:
        hay_class_search = f"class={hay_class}"

    # Make the API call
    endpoint = f"/services/v1.2/reports/{selected_slug_id}?q=commodity=Hay;{hay_class_search};{hay_grade_search};"
    data = get_data_from_mmnapi(api_key, endpoint)
    
    # Transform pulled data into a DataFrame
    if not isinstance(data, str):
        daily_hay_sw_filtered = pd.DataFrame(data["results"])
    else:
        print("Received data is a string. Cannot convert to DataFrame.")

    # Check if API works
    if isinstance(data, str):
    # Return a figure with the "The access to the API is temporarily unavailable" message
        fig = go.Figure()
        fig.add_annotation(
            text="API access is temporarily unavailable",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="white")
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0, 
                        autoexpand=True))
        
        fig.update_yaxes(visible=False, showticklabels=False, showgrid=False)
        fig.update_xaxes(visible=False, showticklabels=False, showgrid=False)

        return fig, last_btn_hay, {}
    
    # Check if the filtered dataframe is empty
    # Return a figure with a warnning message if so
    elif daily_hay_sw_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data for this search",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="white")
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0, 
                        autoexpand=True))
        
        fig.update_yaxes(visible=False, showticklabels=False, showgrid=False)
        fig.update_xaxes(visible=False, showticklabels=False, showgrid=False)

        return fig, last_btn_hay, {}
    
    # Check if the filtered dataframe has only one observation
    # Return a figure with a warnning message
    elif len(daily_hay_sw_filtered) == 1:
        fig = go.Figure()
        fig.add_annotation(
            text="There are no time series results for this search",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="white")
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0, 
                        autoexpand=True))
        
        fig.update_yaxes(visible=False, showticklabels=False, showgrid=False)
        fig.update_xaxes(visible=False, showticklabels=False, showgrid=False)

        return fig, last_btn_hay, {}
    
    # Represent the extracted data in a graph
    else:
        # Process data if API works and data has been pulled
        daily_hay_sw_filtered['report_Date'] = pd.to_datetime(daily_hay_sw_filtered['report_Date'])
        # Difference between the latest and earliest dates
        max_date = daily_hay_sw_filtered['report_Date'].max()
        min_date = daily_hay_sw_filtered['report_Date'].min()
        # The difference in months
        months_difference = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month

        # Set conditionals based on triggered elements to update the displayed data
        if not ctx.triggered:
            months = months_difference
            last_btn_hay = 'btn-all-hay'  # default button
        else:
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            # Location dropdown menu triggers
            if triggered_id in ['location-dropdown-hay', 'hay-class-dropdown', 'hay-grade-dropdown'] and last_btn_hay is not None:
                triggered_id = last_btn_hay
            # Time range buttons triggers
            if triggered_id == 'btn-all-hay':
                months = months_difference
                last_btn_hay = 'btn-all-hay'
            elif triggered_id == 'btn-2yr-hay':
                months = 24
                last_btn_hay = 'btn-2yr-hay'
            elif triggered_id == 'btn-1yr-hay':
                months = 12
                last_btn_hay = 'btn-1yr-hay'
            elif triggered_id == 'btn-6mo-hay':
                months = 6
                last_btn_hay = 'btn-6mo-hay'
            elif triggered_id == 'btn-2mo-hay':
                months = 2
                last_btn_hay = 'btn-2mo-hay'

        # If the months difference is zero and selected months is also zero, consider days.
        if months_difference == 0 and months == 0:
            days_difference = (max_date - min_date).days
            one_year_before_max_date = max_date - pd.DateOffset(days=days_difference)
        else:
            # Get the date before the most recent date
            one_year_before_max_date = max_date - pd.DateOffset(months=months)

        # Prepare data and color for the graph
        grouped_df = daily_hay_sw_filtered.groupby('report_Date')['average_Price'].mean().reset_index()
        grouped_df = grouped_df.sort_values('report_Date')
        last_year_df = grouped_df[grouped_df['report_Date'] >= one_year_before_max_date]
        price_change = last_year_df['average_Price'].iloc[-1] - last_year_df['average_Price'].iloc[0]
        color = 'green' if price_change >= 0 else 'red'
        fillcolor_base = '0,128,0' if price_change >= 0 else '128,0,0'  # Use RGB format for base color

        # Create Figure
        fig = go.Figure()

        # Gradient Fill for Scatter Plot
        num_layers = 20
        base_y = last_year_df['average_Price'].min()

        # Plotly library does not support gradient fill for line graphs
        # The following loop provides a way of creating transparent gradient below the line graph
        for i in range(num_layers - 1):
            fraction = i / num_layers
            y_values = base_y + (last_year_df['average_Price'] - base_y) * fraction
            gradient_fillcolor = f'rgba({fillcolor_base},{(i + 1) / num_layers * 0.2})'  # Varying the opacity
            fig.add_trace(go.Scatter(x=last_year_df['report_Date'], y=y_values,
                                    mode='lines', 
                                    fill='tonexty', line=dict(width=0),
                                    fillcolor=gradient_fillcolor,
                                    hoverinfo='none'
                            ))

        # The topmost gradient layer to match exactly with the line graph's y-values
        fig.add_trace(go.Scatter(x=last_year_df['report_Date'], y=last_year_df['average_Price'],
                                mode='lines', 
                                fill='tonexty', line=dict(width=0),
                                fillcolor=f'rgba({fillcolor_base},0.2)',
                                hoverinfo='none'
                        ))

        # Add Line Chart on top of Gradient
        fig.add_trace(go.Scatter(x=last_year_df['report_Date'], y=last_year_df['average_Price'], 
                                mode='lines', 
                                line=dict(color=color),
                                name='average_price',
                                hovertemplate='%{x|%Y-%m-%d}<br>Daily average price: $%{y:.2f}<extra></extra>'
                        ))

        # Add indicator (most recent value and % change)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=last_year_df['average_Price'].iloc[-1],
            delta={'reference': last_year_df['average_Price'].iloc[0], 'relative': True, 'valueformat': '.1%', 'font': {'size': 17}},
            number={'valueformat': '$.1f', 'font':{'size': 22, 'color': '#dbe5f3'}},
            domain={'y': [0.99, 1], 'x': [0.8, 0.9]}
        ))

        min_price = last_year_df['average_Price'].min()
        max_price = last_year_df['average_Price'].max()
        padding = (max_price - min_price) * 0.1

        # Update layout
        fig.update_yaxes(
            range=[min_price - padding, max_price + padding+20], 
            showticklabels=True, showgrid=False,
            tickfont=dict(color='#dbe5f3'),
            title_font=dict(color='#dbe5f3'),
            title_text="$/ton",
            ticksuffix="     ",
            zeroline=False 
        )

        fig.update_xaxes(showticklabels=True, showgrid=False,
                        tickfont=dict(color='#dbe5f3'),
                        zeroline=False )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            showlegend=False,
            margin=dict(l=0, r=0, t=19, b=0, 
                        autoexpand=True)
        )

        return fig, last_btn_hay, {}






        
   
        

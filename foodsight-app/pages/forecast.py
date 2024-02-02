
# ------------------------------------------------------------------------------
# Libraries

# Standard Library Imports
from base64 import b64encode
from datetime import datetime, timedelta
import json
from io import BytesIO
import time
import janitor

# Dash imports for web apps
import dash
import dash_daq as daq
from dash import callback, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Geospatial processing and visualization
import geopandas as gpd
from geopandas.tools import sjoin
from pyproj import CRS, Transformer
from shapely.geometry import Point
from shapely.ops import transform

# Plotting and visualization
import matplotlib.cm as cm
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

# Data manipulation
import numpy as np
import pandas as pd

# Image processing
from PIL import Image
# import cv2

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
# df_hist = pd.read_csv("../testing_lambda/hist_data_grasscast_gp_sw.csv")
# df_forecast = pd.read_csv("../testing_lambda/forecast_data_grasscast_gp_sw.csv")

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
# Markets list for dropdown menu
dropdown_options = list(set([item['market_location_name'] for item in cattle_markets_list]))
dropdown_options = sorted(dropdown_options)

## Time variables
# Get the current month
current_month = datetime.now().month
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
                        [
                            html.Div(id='firstText', className='mini_container'),
                            html.Div(id='secondText', className='mini_container'),
                            html.Div(id='thirdText', className='mini_container'),
                            html.Div(id='fourthText', className='mini_container'),
                            dcc.Store(id='initial_year_text'),
                            dcc.Store(id='time_range_text'),
                            dcc.Store(id='lastTriggered'),
                        ],
                        id='info-container', className='row container-display'
                    ),
                    html.Div(
                        id="graph-container",
                        children=[
                            dcc.Tabs(id="tabs", value='tab-1', children=[
                                dcc.Tab(
                                    label='Forecast', value='tab-1',
                                    children=[
                                        html.P(id="output_text", children=[]),
                                        html.Div(
                                            id="plot-and-switch-container",
                                            children=[
                                                html.Div([
                                                    html.Div(
                                                        daq.BooleanSwitch(
                                                            id='my-toggle-switch',
                                                            on=False,
                                                        ),
                                                        style={'display': 'inline-block', 'text-align': 'left', 'padding-left':'3rem'}
                                                    ),
                                                ]),
                                                dcc.Loading(
                                                    id="loading-3",
                                                    type="circle",
                                                    children=dcc.Graph(
                                                        id='line-plot-2',
                                                        figure={},
                                                        style={'visibility': 'hidden'},
                                                        config={'displayModeBar': False, 'scrollZoom': False}
                                                    ),
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                                dcc.Tab(
                                    label='Historical', value='tab-2',
                                    children=[
                                        html.P(id="output_text2", children=[]),
                                        html.Div(
                                            id="plot-and-slider-container",
                                            children=[
                                                dcc.Loading(
                                                    id="loading-4",
                                                    type="circle",
                                                    children=dcc.Graph(
                                                        id='line-plot',
                                                        figure={},
                                                        style={'visibility': 'hidden'},
                                                        config={'displayModeBar': False, 'scrollZoom': False}
                                                    ),
                                                ),
                                                dcc.Slider(
                                                    id="slct_year",
                                                    min=min(YEARS),
                                                    max=max(YEARS),
                                                    value=max(YEARS),
                                                    step=1,
                                                    marks={
                                                        str(min(YEARS)): {"label": str(min(YEARS)), "style": {"color": "#7fafdf"}},
                                                        str(max(YEARS)): {"label": str(max(YEARS)), "style": {"color": "#7fafdf"}}
                                                    },
                                                    tooltip={'always_visible': True, "placement": "bottom"}
                                                ),
                                            ]
                                        ),
                                        html.Div([
                                            html.Button('All', id='btn-all-hist', n_clicks=1, className='button-style2'),
                                            html.Button('30Y', id='btn-30yr-hist', n_clicks=0, className='button-style2'),
                                            html.Button('20Y', id='btn-20yr-hist', n_clicks=0, className='button-style2'),
                                            html.Button('10Y', id='btn-10yr-hist', n_clicks=0, className='button-style2'),
                                        ], className='button-container-hist'),
                                        html.Div(id='time-range-store', style={'display':'none'}),
                                        dcc.Store(id='time-range-store2')
                                    ]
                                ),
                            ]),
                        ],
                    )
                ],
            ),
            html.Div(
                id="right-column",
                children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Where can you find better pastures?", id="compass-summary-title"),
                                    dbc.Tooltip(
                                        "This plot indicates the direction to find better pastures, based on the selected distance and either the centroid of the chosen county/map area or the selected point location.",
                                        target="polar-graph-container",
                                        placement="bottom",
                                    ),
                                    dbc.Tooltip(
                                        "This plot displays the distribution of ANPP data within the buffer zone, based on the chosen distance. It compares the ANPP values at the centroid of the county or the delineated area on the map, or at the selected point location, with the productivity in the surrounding area.",
                                        target="graph-bar-container",
                                        placement="bottom",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id='distance-input-container',
                                                        children=[
                                                            html.Label('Distance:', className='inline-label-input'),
                                                            dcc.Input(
                                                                id='miles-input',
                                                                type='number',
                                                                value=50,
                                                                min=12,
                                                                max=500,
                                                                className='inline-label-input'
                                                            ),
                                                            html.Label('miles', className='inline-label-input'),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        id='polar-graph-container',
                                                        children=[
                                                            dcc.Loading(
                                                                id="loading-1",
                                                                type="circle",
                                                                children=dcc.Graph(
                                                                    id='polar-graph',
                                                                    figure={},
                                                                    style={'visibility': 'hidden'},
                                                                    config={'displayModeBar': False, 'staticPlot': True}
                                                                ),
                                                            )
                                                        ]
                                                    ),
                                                ],
                                                className='all-elements-column'
                                            ),
                                            html.Div(
                                                id='graph-bar-container',
                                                children=[
                                                    dcc.Loading(
                                                        id="loading-1",
                                                        type="circle",
                                                        children=html.Img(id="violin-gradient-plot")
                                                    )
                                                ]
                                            ),
                                        ],
                                        className='columns-container'
                                    )
                                ],
                                id='compass_loc',
                                className='mini_container_spatial'
                            ),
                            html.Div(
                                html.Div([
                                    html.Div([
                                        dcc.Dropdown(
                                            id='location-dropdown',
                                            options=dropdown_options,
                                            value='Cattlemen\'s Livestock Auction - Belen, NM',  # Default market
                                            className='my-custom-dropdown'
                                        ),
                                    ]),
                                    dcc.Loading(
                                        id="loading-5",
                                        type="circle",
                                        children=dcc.Graph(
                                            id='indicator-graph',
                                            config={'displayModeBar': False, 'staticPlot': True},
                                            style={'visibility': 'hidden'}
                                        ),
                                    ),
                                    html.Div([
                                        html.Button('ALL', id='btn-all-forecast', n_clicks=1, className='button-style'),
                                        html.Button('2Y', id='btn-2yr-forecast', n_clicks=0, className='button-style'),
                                        html.Button('1Y', id='btn-1yr-forecast', n_clicks=0, className='button-style'),
                                        html.Button('2M', id='btn-6mo-forecast', n_clicks=0, className='button-style'),
                                        dcc.Link(
                                            children=html.Button('+ Market info', id='btn-market-info', n_clicks=0, className='button-style-market'),
                                            href='/econ',
                                            className="page-link"
                                        ),
                                    ], className='button-container-forecast'),
                                ]),
                                id='econ_summary',
                                className='mini_container_spatial'
                            ),
                            html.Div(id='hidden-div_econ', style={'display':'none'}),
                        ],
                        id='info-container2',
                    ),
                    html.Div(
                        id="heatmap-container",
                        children=[
                            html.Div(
                                id="heatmap-header-container",
                                children=[
                                    html.P(id='output_container', children=[]),
                                    dcc.Checklist(
                                        id='checkboxes-map',
                                        options=[
                                            {'label': 'Great Plains', 'value': 'gp'},
                                            {'label': 'Southwest', 'value': 'sw'}
                                        ],
                                        value=[]
                                    ),
                                ]
                            ),
                            # dcc.Loading(
                                # id="loading-2",
                                # type="circle",
                                # children=
                                dcc.Graph(
                                    id='choropleth-map',
                                    config={
                                        'scrollZoom': True,
                                        'displaylogo': False,
                                        'displayModeBar': True,
                                        'modeBarButtonsToRemove':['toImage', 'hoverClosestPie']
                                    },
                                    clickData=None,
                                    figure={},
                                    style={'visibility': 'hidden'},
                                ),
                            # ),
                            html.Div(id='selected-data-store', style={'display': 'none'}),
                            html.Div(id='stored-bounds-zoom', style={'display': 'none'}),
                            html.Div(id='stored-dragmode', style={'display': 'none'}),
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
## Callbacks for Summary data

# --------------------------
# Summary Data

## Helper functions for summary boxes callback

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

# Historical data wrangling
def create_hist_summaries(df, columns_to_keep, spatial_join=False, polygon=None):
    if spatial_join:
        if polygon is None:
            raise ValueError("Polygon DataFrame is required for spatial join.")
        df = sjoin(df[columns_to_keep], polygon, how='inner', predicate='intersects')
    else:
        df = df[columns_to_keep]

    yearly_summaries = []
    for year in df['year'].unique():
        df_year = df[df['year'] == year]
        summary_dict = df_year.iloc[0].to_dict()  # get first row values, which will be overwritten
        summary_dict['year'] = year
        # override with mean values for specified columns
        summary_dict.update({
            'predicted_spring_anpp_lbs_ac': df_year['predicted_spring_anpp_lbs_ac'].mean(),
            'predicted_summer_anpp_lbs_ac': df_year['predicted_summer_anpp_lbs_ac'].mean(),
            'anpp_lbs_ac': df_year['anpp_lbs_ac'].mean(),
        })
        yearly_summaries.append(summary_dict)
    
    # Creating the new column 'predicted_anpp' in the historical data
    hist_data = pd.DataFrame(yearly_summaries)
    hist_data['predicted_anpp'] = np.where(
                hist_data['anpp_lbs_ac'].notna(), hist_data['anpp_lbs_ac'],
                np.where(
                    (current_month in [4, 5]),
                    hist_data['predicted_spring_anpp_lbs_ac'],
                    hist_data['predicted_summer_anpp_lbs_ac']
                )
            )

    return hist_data

# Text and boxes generation
def process_summary_boxes(latest_date_rows, current_month, hist_data, time_range_text):

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

        difference = round(predict - mean)
        percentage = (abs(difference) * 100) / mean
        direction = "higher" if difference > 0 else "lower"
        arrow_direction = "up" if direction == "higher" else "down"

        # Determine the season and appropriate verbs based on the current month
        if 4 <= current_month <= 5:
            season = 'for this spring'
            verb = 'is'
            verb2 = 'will be'
        elif 6 <= current_month <= 9:
            season = 'for this summer'
            verb = 'is'
            verb2 = 'will be'
        elif 10 <= current_month <= 12:
            season = 'for this summer'
            verb = 'was'
            verb2 = 'was'
        else:
            season = 'last season'
            verb = 'was'
            verb2 = 'was'

        if season == 'Spring':
            hist_data['abs_diff'] = abs(hist_data['predicted_anpp'] - predict)
        else:
            hist_data['abs_diff'] = abs(hist_data['predicted_anpp'] - predict)

        most_similar_row = hist_data.loc[hist_data['abs_diff'].idxmin()]
        most_similar_year = most_similar_row['year']
        
        text = (f"In this location, the expected productivity {season} {verb} about {round(predict,0):.0f} lb/ac.")
        text2 = (f"In {current_year}, the productivity {verb2} {percentage:.0f}% {direction} than the historical average.")

        first_box = html.Div([
            html.Span(f"The expected productivity {season} {verb} about ", style={"color": "black"}),
            html.Br(),
            html.Span(f"{round(predict,0):.0f}", style={"color": "#2e55a3", "font-size": "24px"}),
            html.Span(" lb/ac.", style={"color": "black"})
        ])

        second_box = html.Div([
            html.Span(f"Weather {verb} "),
            html.Br(),
            html.Span(f"{cat_description.split(' ')[0]}", style={"color": "#2e55a3", "font-size": "24px"}) if cat_description != 'normal' else "",
            html.Span(" than normal") if cat_description != 'normal' else "",
            html.Span(f"{cat_description}", style={"color": "#2e55a3", "font-size": "24px"}) if cat_description == 'normal' else ""
        ])

        if difference == 0:
            third_box = html.Div([
                html.Span(f"The productivity {verb2}"),
                html.Br(),
                html.Span(f"{round(percentage,0):.0f}% ", style={"color": "#2e55a3", "font-size": "18px"}),
                html.Span("within   ", style={"color": "#2e55a3", "font-size": "16px"}),
                html.Span(className="fa-solid fa-equals", style={"color": "#2e55a3","font-size": "20px"}),
                html.Br(),
                html.Span(" the historical average")
            ])
        else:
            third_box = html.Div([
                html.Span(f"The productivity {verb2}"),
                html.Br(),
                html.Span(f"{round(percentage,0):.0f}% ", style={"color": "#2e55a3", "font-size": "18px"}),
                html.Span(f"{direction}   ", style={"color": "#2e55a3", "font-size": "16px"}),
                html.Span(className=f"fa fa-arrow-{arrow_direction}", style={"color": "#2e55a3","font-size": "20px"}),
                html.Br(),
                html.Span(" than the historical average")
            ])

        fourth_box = html.Div([
            html.Span(f"Conditions most similar to those from "),
            html.Span(f"{most_similar_year:.0f} ", style={"color": "#2e55a3", "font-size": "20px", "vertical-align": "middle"}),
            html.Span(f" ({time_range_text})", style={"font-size": "9px", "vertical-align": "middle"}),
        ])

    return  text, text2, first_box, second_box, third_box, fourth_box

# Fourth box content
@callback(
    [Output('initial_year_text', 'data'),
     Output('time_range_text', 'data'),
    ],
    [Input('time-range-store2', 'data')]
)
def update_summary_boxes_content(start_year):
    # Identify which input triggered the callback
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    initial_year = gdf_hist['year'].min()  # Default value
    min_year = min(YEARS)
    max_year = max(YEARS)
    time_range_text = f"{min_year} - {max_year}" 

    if triggered_id == 'time-range-store2' or start_year is not None:
                
        if start_year['last_button'] == 'btn-30yr-hist':
            initial_year = current_year-30
            time_range_text = f"{max_year - 30} - {max_year}"

        elif start_year['last_button'] == 'btn-20yr-hist':
            initial_year = current_year-20
            time_range_text = f"{max_year - 20} - {max_year}"

        elif start_year['last_button'] == 'btn-10yr-hist':
            initial_year = current_year-10
            time_range_text = f"{max_year - 10} - {max_year}"

    return initial_year, time_range_text


# Summary boxes callback
@callback(
    [Output('output_text', 'children'),
     Output('output_text2', 'children'),
     Output("firstText", "children"),
     Output("secondText", "children"),
     Output("thirdText", "children"),
     Output("fourthText", "children"),
     Output("lastTriggered", "data")
    ],
    [Input('choropleth-map', 'clickData'),
     Input('autocomplete-input', 'value'),
     Input('selected-data-store', 'children'),
     Input('initial_year_text', 'data'),
     Input('time_range_text', 'data'),
     Input('lastTriggered', 'data')],
)
def update_summary_boxes(clickData, by_county, selected_data_store, initial_year, time_range_text, last_trigger):

    # Identify which input triggered the callback
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
  
    # Define last trigger to be loaded in the following user interaction
    if triggered_id in ['choropleth-map', 'autocomplete-input', 'selected-data-store']:
        last_trigger = triggered_id
    
    # Trigger the data wrangling and summary boxes
    if triggered_id in ['initial_year_text','time_range_text', 'choropleth-map', 'autocomplete-input', 'selected-data-store']:

        # Filter the historical data based on the initial year
        gdf_hist_filtered = gdf_hist[(gdf_hist['year'] >= initial_year) & (gdf_hist['year'] != current_year)]

        # Filter data based on user selection
        if triggered_id == 'autocomplete-input' or last_trigger == 'autocomplete-input':
            polygon = counties_gpd.loc[counties_gpd['name'] == by_county]
            
            # Forecast
            columns_to_keep_forcast = ['gridid','report_date','npp_predict_below', 'npp_predict_avg','npp_predict_above',
                                    'cat', 'prob','year', 'npp_predict_clim','meananppgrid','geometry']
            dff_forcast_polygon = sjoin(gdf_forecast[columns_to_keep_forcast], polygon, how='inner', predicate='intersects')
            df_plot = create_forecast_summaries(dff_forcast_polygon,current_year)
            latest_date_rows = df_plot[df_plot['report_date'] == df_plot['report_date'].max()]
            
            # Historical
            columns_to_keep_hist = ['gridid','year','predicted_spring_anpp_lbs_ac', 'predicted_summer_anpp_lbs_ac', 'anpp_lbs_ac', 'geometry']
            hist_data = create_hist_summaries(gdf_hist_filtered, columns_to_keep_hist, spatial_join=True, polygon=polygon)

            text, text2, first_box, second_box, third_box, fourth_box = process_summary_boxes(latest_date_rows, current_month, hist_data, time_range_text)

        elif (triggered_id == 'choropleth-map' or last_trigger == 'choropleth-map') and clickData is not None:
            id_value = clickData['points'][0]['customdata'][0]

            # Forecast
            df_plot = df_forecast[df_forecast['gridid'] == id_value]
            df_plot = df_plot[df_plot['year'] == current_year]
            latest_date_rows = df_plot[df_plot['report_date'] == df_plot['report_date'].max()]

            # Historical
            hist_data = gdf_hist_filtered[gdf_hist_filtered['gridid'] == id_value]
            # Creating the new column 'predicted_anpp' in the historical data
            hist_data['predicted_anpp'] = np.where(
                hist_data['anpp_lbs_ac'].notna(), hist_data['anpp_lbs_ac'],
                np.where(
                    (current_month in [4, 5]),
                    hist_data['predicted_spring_anpp_lbs_ac'],
                    hist_data['predicted_summer_anpp_lbs_ac']
                )
            )

            text, text2, first_box, second_box, third_box, fourth_box = process_summary_boxes(latest_date_rows, current_month, hist_data, time_range_text)

        elif (triggered_id == 'selected-data-store' or last_trigger == 'selected-data-store') and selected_data_store is not None:
            formatted_selected_data =  json.loads(selected_data_store)

            # Forecast
            dff_forcast_selected = gdf_forecast[gdf_forecast['gridid'].isin(formatted_selected_data)]
            df_plot = create_forecast_summaries(dff_forcast_selected, current_year)
            latest_date_rows = df_plot[df_plot['report_date'] == df_plot['report_date'].max()]

            # Historical
            dff_hist_selected = gdf_hist_filtered[gdf_hist_filtered['gridid'].isin(formatted_selected_data)]
            columns_to_keep_hist = ['gridid', 'year', 'predicted_spring_anpp_lbs_ac', 'predicted_summer_anpp_lbs_ac', 'anpp_lbs_ac', 'geometry']
            hist_data = create_hist_summaries(dff_hist_selected, columns_to_keep_hist, spatial_join=False)

            text, text2, first_box, second_box, third_box, fourth_box = process_summary_boxes(latest_date_rows, current_month, hist_data, time_range_text)

        else: # default data from county selection
            polygon = counties_gpd.loc[counties_gpd['name'] == by_county]
            # Forecast
            columns_to_keep_forcast = ['gridid','report_date','npp_predict_below', 'npp_predict_avg','npp_predict_above',
                                    'cat', 'prob','year', 'npp_predict_clim','meananppgrid','geometry']
            dff_forcast_polygon = sjoin(gdf_forecast[columns_to_keep_forcast], polygon, how='inner', predicate='intersects')
            df_plot = create_forecast_summaries(dff_forcast_polygon,current_year)
            latest_date_rows = df_plot[df_plot['report_date'] == df_plot['report_date'].max()]
            # Historical
            columns_to_keep_hist = ['gridid','year','predicted_spring_anpp_lbs_ac', 'predicted_summer_anpp_lbs_ac', 'anpp_lbs_ac', 'geometry']
            hist_data = create_hist_summaries(gdf_hist_filtered, columns_to_keep_hist, spatial_join=True, polygon=polygon)
            text, text2, first_box, second_box, third_box, fourth_box = process_summary_boxes(latest_date_rows, current_month, hist_data, time_range_text)

            
        return text, text2, first_box, second_box, third_box, fourth_box, last_trigger


## ----------------------------------------
## Callbacks for Forecast data

# --------------------------
# Forecast chart

# Helper function for the forecast chart callback
def process_forecast_data(dff_forecast, columns_to_keep, current_year):

    dff_forecast['report_date'] = pd.to_datetime(dff_forecast['report_date'])
    # Process forecast summaries
    forecast_summaries = []
    for date in dff_forecast['report_date'].unique():
        dff_year = dff_forecast[dff_forecast['report_date'] == date]
        forecast_summary_dict = dff_year.iloc[0].to_dict()  # get first row values
        forecast_summary_dict['report_date'] = date
        # Override with mean values for specified columns
        forecast_summary_dict.update({
            'npp_predict_below': dff_year['npp_predict_below'].mean(),
            'npp_predict_avg': dff_year['npp_predict_avg'].mean(),
            'npp_predict_above': dff_year['npp_predict_above'].mean(),
            'prob': dff_year['prob'].mean(),
            'npp_predict_clim': dff_year['npp_predict_clim'].mean(),
            'cat': dff_year['cat'].mode()[0] if not dff_year['cat'].mode().empty else None
        })
        forecast_summaries.append(forecast_summary_dict)

    # Convert summaries to DataFrame
    df_plot = pd.DataFrame(forecast_summaries)
    
    df_plot = df_plot[df_plot['year'] == current_year]

    # Split the data into Spring and Summer
    df_plot['Month'] = df_plot['report_date'].dt.month
    spring_df = df_plot[(df_plot['Month'] >= 4) & (df_plot['Month'] <= 5)]
    summer_df = df_plot[df_plot['Month'] >= 6]

    return spring_df, summer_df


# Forecast chart callback
@callback(
    [Output('line-plot-2', 'figure'),
     Output('line-plot-2', 'style')],
    [Input('choropleth-map', 'clickData'),
     Input('my-toggle-switch', 'on'),
     Input('autocomplete-input', 'value'),
     Input('selected-data-store', 'children')]
)
def update_forecast_plot(clickData, on, by_county,selected_data_store):
    
    ## Select forecast and historical data of interest

    # Identify which input triggered the callback
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id in ['my-toggle-switch', 'choropleth-map'] and clickData is not None:
        id_value = clickData['points'][0]['customdata'][0]
        df_plot = df_forecast[df_forecast['gridid'] == id_value]
            
        df_plot = df_plot[df_plot['year'] == current_year]  
                    
        # Split the data into Spring and Summer
        df_plot['report_date'] = pd.to_datetime(df_plot['report_date'])
        df_plot['Month'] = df_plot['report_date'].dt.month
        spring_df = df_plot[(df_plot['Month'] >= 4) & (df_plot['Month'] <= 5)]
        summer_df = df_plot[df_plot['Month'] >= 6]

        def find_aoi_for_gridid(aoi_gridids, id_value):
            aoi_detected = None
            for entry in aoi_gridids:
                if id_value in entry["gridid"]:
                    aoi_detected = entry["aoi"]
                    break
            return aoi_detected
        
        aoi_detected = find_aoi_for_gridid(aoi_gridids, id_value)

    elif triggered_id in ['my-toggle-switch', 'autocomplete-input'] and by_county is not None:
        polygon = counties_gpd.loc[counties_gpd['name'] == by_county]
        columns_to_keep_forcast = ['gridid','report_date','npp_predict_below', 'npp_predict_avg','npp_predict_above',
                                'cat', 'prob','year', 'npp_predict_clim','geometry']
        # spatial join between the gdf_forecast and the polygon
        dff_forcast_polygon = sjoin(gdf_forecast[columns_to_keep_forcast], polygon, how='inner', predicate='intersects')
        spring_df, summer_df = process_forecast_data(dff_forcast_polygon, columns_to_keep_forcast, current_year)

        def find_aoi(counties_geojson, by_county):
            aoi_detected = None
            for feature in counties_geojson["features"]:
                if feature["properties"]["name"] == by_county:
                    aoi_value = feature["properties"]["aoi"]
                    if aoi_value in ["gp", "sw"]:
                        aoi_detected = aoi_value
                        break
            return aoi_detected
        
        aoi_detected = find_aoi(counties_geojson, by_county)

    elif triggered_id == 'selected-data-store' and selected_data_store is not None:
        formatted_selected_data =  json.loads(selected_data_store)
 
        # Forecast
        # Filter the gdf_forecast DataFrame based on the formatted_selected_data list
        dff_forcast_selected = gdf_forecast[gdf_forecast['gridid'].isin(formatted_selected_data)]
        columns_to_keep_forcast = ['gridid', 'report_date', 'npp_predict_below', 'npp_predict_avg', 'npp_predict_above',
                                'cat', 'prob', 'year', 'npp_predict_clim', 'meananppgrid', 'geometry']
        dff_forcast_selected = dff_forcast_selected[columns_to_keep_forcast]

        spring_df, summer_df = process_forecast_data(dff_forcast_selected, columns_to_keep_forcast, current_year)

        def find_dominant_aoi(aoi_gridids, formatted_selected_data):
            all_sw = True

            for grid_id in formatted_selected_data:
                is_sw = False
                for entry in aoi_gridids:
                    if grid_id in entry["gridid"]:
                        if entry["aoi"] == "sw":
                            is_sw = True
                        break
                if not is_sw:
                    all_sw = False
                    break

            return "sw" if all_sw else "gp"  # sw > gp or equal counts set to 'gp' to avoid problems with differences in data split
            
        aoi_detected = find_dominant_aoi(aoi_gridids, formatted_selected_data)

    else:
        def find_aoi(counties_geojson, by_county):
            aoi_detected = None
            for feature in counties_geojson["features"]:
                if feature["properties"]["name"] == by_county:
                    aoi_value = feature["properties"]["aoi"]
                    if aoi_value in ["gp", "sw"]:
                        aoi_detected = aoi_value
                        break
            return aoi_detected
        polygon = counties_gpd.loc[counties_gpd['name'] == by_county]
        columns_to_keep_forcast = ['gridid','report_date','npp_predict_below', 'npp_predict_avg','npp_predict_above',
                                'cat', 'prob','year', 'npp_predict_clim','geometry']
        # spatial join between the gdf_forecast and the polygon
        dff_forcast_polygon = sjoin(gdf_forecast[columns_to_keep_forcast], polygon, how='inner', predicate='intersects')
        spring_df, summer_df = process_forecast_data(dff_forcast_polygon, columns_to_keep_forcast, current_year)
        aoi_detected = find_aoi(counties_geojson, by_county)

    
    ## Generate the forecast chart
    
    # Helper functions to create annotations when there is only one observation
    # Function to check if DataFrame has only one observation
    def is_single_observation(df):
        return len(df['report_date'].unique()) == 1
    # Function to add a message annotation to a plot
    def add_single_point_message(fig, message, row, col):
        fig.add_annotation(
            text= f"<i>{message}</i>",
            xref="paper", yref="paper",
            x=2.5, y=1.5, showarrow=False,
            font=dict(size=13, color="grey"),
            row=row, col=col,
        )
        fig.update_yaxes(visible=False, showticklabels=False, showgrid=False, row=row, col=col)
        fig.update_xaxes(visible=False, showticklabels=False, showgrid=False, row=row, col=col)


    # Chart with forecast scenarios data 
    if on:  # This means that the toggle switch is on

        def create_traces(df):
            traces = []
            # ANPP avg
            traces.append(go.Scatter(x=df['report_date'], y=df['npp_predict_avg'], 
                                    name='ANPP avg', line=dict(color='rgb(128, 128, 0)', dash='dash'),
                                    hovertemplate="Average ANPP: %{y:.0f} lb/ac<extra></extra>"))  
            # ANPP below
            traces.append(go.Scatter(x=df['report_date'], y=df['npp_predict_below'], 
                                    name='ANPP below', line=dict(color='rgb(237, 189, 69)', dash='dash'),
                                     hovertemplate="Below ANPP: %{y:.0f} lb/ac<extra></extra>"))  
            # ANPP above
            traces.append(go.Scatter(x=df['report_date'], y=df['npp_predict_above'], 
                                    name='ANPP above', line=dict(color='rgb(0, 128, 0)', dash='dash'),
                                    hovertemplate="Above ANPP: %{y:.0f} lb/ac<extra></extra>"))  
            # actual ANPP
            traces.append(go.Scatter(x=df['report_date'], y=df['npp_predict_clim'], 
                                    name='actual ANPP', line=dict(color='rgba(220,220,220,0.5)', width=1),
                                    mode='lines', showlegend=False,
                                    hoverinfo='skip'))  
            return traces

        # Handling spring_df
        last_value_spring = spring_df['npp_predict_clim'].values[-1]
        spring_df['report_date'] = pd.to_datetime(spring_df['report_date'])
        spring_dates = spring_df['report_date'].dropna().tolist()

        # Check if summer_df is empty
        summer_df_empty = summer_df.empty
        if summer_df.empty:
            last_value_summer = spring_df['npp_predict_clim'].values[-1]
            summer_df['report_date'] = pd.to_datetime(spring_df['report_date'])
            summer_dates = spring_df['report_date'].dropna().tolist()
        elif not summer_df_empty:
            last_value_summer = summer_df['npp_predict_clim'].values[-1]
            summer_df['report_date'] = pd.to_datetime(summer_df['report_date'])
            summer_dates = summer_df['report_date'].dropna().tolist()

        # Generate subplots
        subplot_titles = [" ",  " "] if not summer_df_empty else [" "] # It forces to create predefined subplot titles, despite these being updated later
        fig = sp.make_subplots(rows=2 if not summer_df_empty else 1, cols=1, subplot_titles=subplot_titles, vertical_spacing=0.3)

        # Add spring traces
        if is_single_observation(spring_df):
            # Format the date as "Month day, Year"
            add_single_point_message(fig,
                                     (f'First forecast value for Spring months. <br>'
                                      f'({round(last_value_spring, 0):.0f} lb/ac. Release date: {spring_dates[-1].strftime("%B %d, %Y")}). <br>'
                                      'No trends available yet.'),
                                     row=1, col=1)
        else:
            for i, trace in enumerate(create_traces(spring_df), start=1):
                fig.add_trace(trace, row=1, col=1)

        # Add summer traces if summer_df is not empty
        if not summer_df_empty:
            if is_single_observation(summer_df):
                add_single_point_message(fig,
                                     (f'First forecast value for Summer months. <br>'
                                      f'({round(last_value_summer, 0):.0f} lb/ac. Release date: {summer_dates[-1].strftime("%B %d, %Y")}). <br>'
                                      'No trends available yet.'),
                                     row=2, col=1)
            else:
                for i, trace in enumerate(create_traces(summer_df), start=1):
                    fig.add_trace(trace, row=2, col=1)

        # Update x and y axis titles
        fig.update_xaxes(title_text='', row=1, col=1, tickangle=0, tickformat='%d %b', nticks=len(spring_dates), tickvals=spring_dates, showgrid=False)
        fig.update_xaxes( tickangle=0, row=2, col=1, tickformat='%d %b', nticks=len(summer_dates), tickvals=summer_dates, showgrid=False)
        fig.update_yaxes(title_text='', row=1, col=1)
        
        # Modify subplot titles based on AOI
        if aoi_detected == "gp":
            fig.layout.annotations[0].update(text=f'Season Productivity: {round(last_value_summer,0):.0f} lb/ac')
            fig.update_xaxes(title_text='Forecast Release date')

        elif aoi_detected == "sw":
            if not summer_df_empty:
                fig.layout.annotations[0].update(text=f'Spring Productivity: {round(last_value_spring,0):.0f} lb/ac')
                fig.layout.annotations[1].update(text=f'Summer Productivity: {round(last_value_summer,0):.0f} lb/ac')
                fig.update_xaxes(title_text='Forecast Release date', tickangle=0, row=2, col=1, tickformat='%d %b', nticks=len(summer_dates), tickvals=summer_dates, showgrid=False)
            else:
                fig.layout.annotations[0].update(text=f'Spring Productivity: {round(last_value_spring,0):.0f} lb/ac')
                fig.update_xaxes(title_text='Forecast Release date')

        # Set a common y-axis title for all the subplots
        fig.update_layout(
            yaxis_title='',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=50, t=20, b=0),
            showlegend=False,
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
            xaxis2=dict(fixedrange=True),
            yaxis2=dict(fixedrange=True)
        )

        # Show the graph
        return fig, {}
    
    # Chart with expected forecast
    else: # This means that the toggle switch is off
        def create_traces(df):
        # Create a trace for npp_predict_below
            trace0 = go.Scatter(
                x=df['report_date'],
                y=df['npp_predict_below'],
                mode='lines',
                name='npp_predict_below',
                line=dict(color='rgb(0, 128, 0)', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            )
            # Create a trace for npp_predict_above with filled area to npp_predict_below
            trace1 = go.Scatter(
                x=df['report_date'],
                y=df['npp_predict_above'],
                mode='lines',
                name='npp_predict_above',
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgb(0, 128, 0)', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            )
            # Create a trace for npp_predict_avg with reduced opacity
            trace2 = go.Scatter(
                x=df['report_date'],
                y=df['npp_predict_avg'],
                mode='lines',
                name='npp_predict_avg',
                line=dict(color='rgba(0, 128, 0, 0.5)', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            )
            # Create a trace for npp_predict_clim with thicker line, dots and black line around the dots
            trace3 = go.Scatter(
                x=df['report_date'],
                y=df['npp_predict_clim'],
                mode='lines+markers',
                name='npp_predict_clim',
                line=dict(color='rgb(237, 189, 69)', width=4),
                marker=dict(
                    size=6,
                    color='rgb(237, 189, 69)',
                    line=dict(
                        color='white',
                        width=1
                    )
                ),
                hovertemplate="ANPP: %{y:.0f} lb/ac<extra></extra>",
                showlegend=False
            )

            # Adjustments for the case when summer_df is empty
            if summer_df_empty:
                fig.update_layout(xaxis2=dict(fixedrange=True), yaxis2=dict(fixedrange=True))

            return [trace0, trace1, trace2, trace3]

        # Handling spring_df
        last_value_spring = spring_df['npp_predict_clim'].values[-1]
        spring_df['report_date'] = pd.to_datetime(spring_df['report_date'])
        spring_dates = spring_df['report_date'].dropna().tolist()

        # Check if summer_df is empty
        summer_df_empty = summer_df.empty
        if summer_df.empty:
            last_value_summer = spring_df['npp_predict_clim'].values[-1]
            summer_df['report_date'] = pd.to_datetime(spring_df['report_date'])
            summer_dates = spring_df['report_date'].dropna().tolist()
        elif not summer_df_empty:
            last_value_summer = summer_df['npp_predict_clim'].values[-1]
            summer_df['report_date'] = pd.to_datetime(summer_df['report_date'])
            summer_dates = summer_df['report_date'].dropna().tolist()

        # Generate subplots
        subplot_titles = [" ",  " "] if not summer_df_empty else [" "] # It forces to create predefined subplot titles, despite these being updated later
        fig = sp.make_subplots(rows=2 if not summer_df_empty else 1, cols=1, subplot_titles=subplot_titles, vertical_spacing=0.3)

        # Add spring traces
        if is_single_observation(spring_df):
            # Format the date as "Month day, Year"
            add_single_point_message(fig,
                                     (f'First forecast value for Spring months. <br>'
                                      f'({round(last_value_spring, 0):.0f} lb/ac. Release date: {spring_dates[-1].strftime("%B %d, %Y")}). <br>'
                                      'No trends available yet.'),
                                     row=1, col=1)
        else:
            for i, trace in enumerate(create_traces(spring_df), start=1):
                fig.add_trace(trace, row=1, col=1)

        # Add summer traces if summer_df is not empty
        if not summer_df_empty:
            if is_single_observation(summer_df):
                add_single_point_message(fig,
                                     (f'First forecast value for Summer months. <br>'
                                      f'({round(last_value_summer, 0):.0f} lb/ac. Release date: {summer_dates[-1].strftime("%B %d, %Y")}). <br>'
                                      'No trends available yet.'),
                                     row=2, col=1)
            else:
                for i, trace in enumerate(create_traces(summer_df), start=1):
                    fig.add_trace(trace, row=2, col=1)

        # Update x and y axis titles
        fig.update_xaxes(title_text='', row=1, col=1, tickangle=0, tickformat='%d %b', nticks=len(spring_dates), tickvals=spring_dates, showgrid=False)
        fig.update_xaxes( tickangle=0, row=2, col=1, tickformat='%d %b', nticks=len(summer_dates), tickvals=summer_dates, showgrid=False)
        fig.update_yaxes(title_text='', row=1, col=1)
       
        # Modify subplot titles based on AOI
        if aoi_detected == "gp":
            fig.layout.annotations[0].update(text=f'Season Productivity: {round(last_value_summer,0):.0f} lb/ac')
            fig.update_xaxes(title_text='Forecast Release date')

        elif aoi_detected == "sw":
            if not summer_df_empty:
                fig.layout.annotations[0].update(text=f'Spring Productivity: {round(last_value_spring,0):.0f} lb/ac')
                fig.layout.annotations[1].update(text=f'Summer Productivity: {round(last_value_summer,0):.0f} lb/ac')
                fig.update_xaxes(title_text='Forecast Release date', tickangle=0, row=2, col=1, tickformat='%d %b', nticks=len(summer_dates), tickvals=summer_dates, showgrid=False)
            else:
                fig.layout.annotations[0].update(text=f'Spring Productivity: {round(last_value_spring,0):.0f} lb/ac')
                fig.update_xaxes(title_text='Forecast Release date')

        # Common y-axis title and layout updates
        fig.update_layout(
            yaxis_title='',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=20, t=20, b=0),
            showlegend=False,
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True)
        )

        # Adjustments for the case when summer_df is empty
        if summer_df_empty:
            fig.update_layout(xaxis2=dict(fixedrange=True), yaxis2=dict(fixedrange=True))

        return fig, {}
    

## ----------------------------------------
## Callbacks for the Historical series

# --------------------------
# Historical data plot
    
# Helper functions for the historical data plot callback
# Process the data to be plotted
def process_hist_series_data(df):
    hist_summaries = []
    for year in df['year'].unique():
        dff_year = df[df['year'] == year]
        hist_summary_dict = dff_year.iloc[0].to_dict()
        hist_summary_dict['year'] = pd.to_datetime(str(year), format='%Y')
        hist_summary_dict.update({
            'predicted_anpp': dff_year['predicted_anpp'].mean()
        })
        hist_summaries.append(hist_summary_dict)

    df_plot = pd.DataFrame(hist_summaries)
    df_plot['year'] = pd.to_datetime(df_plot['year'], format='%Y')

    return df_plot

# Define y axis range based on the selected AOI
def apply_aoi_to_hist_series(df, df_to_plot, selected_aoi, aoi_gridids, y_column):

    if len(selected_aoi) == 2 or not selected_aoi:
        y_range = [0, max(df[y_column])]
    else:
        # Find the corresponding list of gridids for the checkbox value
        selected_gridids = []
        for mapping in aoi_gridids:
            if mapping["aoi"] == selected_aoi[0]:
                selected_gridids = mapping["gridid"]
                break

        # Filter DataFrame based on the selected gridids
        filtered_dff = df[df['gridid'].isin(selected_gridids)]
        y_range = [0, max(filtered_dff[y_column])]

    # Compare and adjust y_range based on df_to_plot 
    # (to solve scale issue when transitioning from gp data to sw AOI)
    if max(df_to_plot[y_column]) > y_range[1]:
        y_range[1] = max(df_to_plot[y_column])

    return y_range


# Historical data plot callback
@callback(
    [Output('line-plot', 'figure'),
     Output('line-plot', 'style')],
    [Input('choropleth-map', 'clickData'),
     Input('slct_year', 'value'),
     Input('autocomplete-input', 'value'),
     Input('selected-data-store', 'children'),
     Input('checkboxes-map', 'value'),
     Input('initial_year_text', 'data'),
     Input('lastTriggered', 'data')]
)
def update_hist_series_plot(clickData, option_slctd, by_county, selected_data_store, selected_aoi, initial_year, last_trigger):
    
    # Identify which input triggered the callback
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Define y axis
    y_column = 'predicted_anpp'

    # Define last trigger to be loaded in the following user interaction
    if triggered_id in ['choropleth-map', 'autocomplete-input', 'selected-data-store']:
        last_trigger = triggered_id
    
    # Trigger the data wrangling and summary boxes
    if triggered_id in ['initial_year_text','time_range_text','slct_year', 'checkboxes-map', 'choropleth-map',  'autocomplete-input', 'selected-data-store']:

        # Filter the historical data based on the years range
        gdf_copy = gdf_hist[(gdf_hist['year'] >= initial_year) & (gdf_hist['year'] <= current_year)]
        gdf_copy['predicted_anpp'] = np.where(
                gdf_copy['anpp_lbs_ac'].notna(), gdf_copy['anpp_lbs_ac'],
                np.where(
                    (current_month in [4, 5]),
                    gdf_copy['predicted_spring_anpp_lbs_ac'],
                    gdf_copy['predicted_summer_anpp_lbs_ac']
                )
            )
        
        if triggered_id == 'autocomplete-input' or last_trigger == 'autocomplete-input':

            # Get polygon defining the county area
            polygon = counties_gpd.loc[counties_gpd['name'] == by_county]

            # Filter data to display
            columns_to_keep_hist = ['gridid', 'predicted_spring_anpp_lbs_ac', 'predicted_summer_anpp_lbs_ac','year', 'predicted_anpp', 'geometry']
            df = sjoin(gdf_copy[columns_to_keep_hist], polygon, how='inner', predicate='intersects')
            df_plot = process_hist_series_data(df)

        elif (triggered_id == 'choropleth-map' or last_trigger == 'choropleth-map') and clickData is not None:

            # Get the gridid of the clicked cell
            id_value = clickData['points'][0]['customdata'][0]

            # Filter data to display
            df_plot = gdf_copy[gdf_copy['gridid'] == id_value]
            df_plot['year'] = pd.to_datetime(df_plot['year'], format='%Y')

        elif (triggered_id == 'selected-data-store' or last_trigger == 'selected-data-store') and selected_data_store is not None:

            # Get the polygon og the area selected in the map
            formatted_selected_data =  json.loads(selected_data_store)
        
            # Filter data to display
            columns_to_keep_hist = ['gridid', 'year', 'predicted_spring_anpp_lbs_ac', 'predicted_summer_anpp_lbs_ac', 'predicted_anpp', 'geometry']
            dff_hist_selected = gdf_copy[gdf_copy['gridid'].isin(formatted_selected_data)][columns_to_keep_hist]
            df_plot = process_hist_series_data(dff_hist_selected)

        else: # default data from county selection
            # Get polygon defining the county area
            polygon = counties_gpd.loc[counties_gpd['name'] == by_county]
            # Filter data to display
            columns_to_keep_hist = ['gridid', 'predicted_spring_anpp_lbs_ac', 'predicted_summer_anpp_lbs_ac','year', 'predicted_anpp', 'geometry']
            df = sjoin(gdf_copy[columns_to_keep_hist], polygon, how='inner', predicate='intersects')
            df_plot = process_hist_series_data(df)

        # Sort resulting dataframe by years
        df_plot = df_plot.sort_values('year')
        # Load slider data
        slctd_year = pd.to_datetime(option_slctd, format='%Y')
        # Define range based on selected AOI
        y_range = apply_aoi_to_hist_series(gdf_copy, df_plot, selected_aoi, aoi_gridids, y_column)

        # Generate the chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_plot['year'],
            y=df_plot[y_column],
            fill='tozeroy',
            fillcolor='rgba(0, 128, 0, 0.2)', #green color with 0.4 opacity
            mode='lines+markers', #adds points to the line
            line=dict(color='green'),
            marker=dict(size=4), #changes size of the
            name='ANPP_mean_Spring (lbs/ac)',
            hovertemplate='year: %{x|%Y} | ANPP: %{y:.0f} lb/ac<extra></extra>'
        ))

        # Update axes
        fig.update_xaxes(title_text='', showticklabels=False)
        fig.update_yaxes(title_text= "Predicted ANPP (lbs/ac)", 
                        range=y_range)

        # Add vertical dashed line
        fig.add_shape(
            type="line",
            x0=slctd_year, y0=0,
            x1=slctd_year, y1=1,
            yref="paper",
            line=dict(
                color="black",
                width=1,
                dash="dash",
            )
        )

        # Update the layout of the plot to have a transparent background
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=0, b=0),
        )

        return fig, {}
 

# --------------------------
# Callback function to update the active button for the years range (historical data plot)
@callback(
    Output("time-range-store2", "data"),
    [Input('btn-all-hist', 'n_clicks'),
     Input('btn-30yr-hist', 'n_clicks'),
     Input('btn-20yr-hist', 'n_clicks'),
     Input('btn-10yr-hist', 'n_clicks')],
    [State('time-range-store2', 'data')]
)
def update_active_button_hist(btn_all, btn_30yr, btn_20yr, btn_10yr, last_btn_hist_store):
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'last_button': 'btn-all-hist'}

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id in ['btn-30yr-hist', 'btn-20yr-hist', 'btn-10yr-hist', 'btn-all-hist']:
        return {'last_button': button_id}
    else:
        return last_btn_hist_store # If unexpected event, keep the last known value

# --------------------------
# Callback function to update the active button style (historical data plot)
@callback(
    [Output('btn-all-hist', 'style'),
     Output('btn-30yr-hist', 'style'),
     Output('btn-20yr-hist', 'style'),
     Output('btn-10yr-hist', 'style')],
    [Input('btn-all-hist', 'n_clicks'),
     Input('btn-30yr-hist', 'n_clicks'),
     Input('btn-20yr-hist', 'n_clicks'),
     Input('btn-10yr-hist', 'n_clicks')]
)
def update_active_button_hist(btn_all, btn_30yr, btn_20yr, btn_10yr):

    default_style = {
        'backgroundColor': 'transparent',
        'color': '#282b3f'
    }
    active_style = {
        'backgroundColor': '#282b3f',
        'color': '#dbe5f3'
    }

    ctx = dash.callback_context
    # If no buttons have been pressed yet, return default styles with btn-all-hist set to active
    if not ctx.triggered:
        styles = [default_style for _ in range(4)]
        styles[0] = active_style  # Make btn-all-hist active
        return styles
        
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    button_indices = {
        'btn-all-hist': 0,
        'btn-30yr-hist': 1,
        'btn-20yr-hist': 2,
        'btn-10yr-hist': 3
    }

    active_button_index = button_indices[button_id]
    styles = [default_style for _ in range(4)]
    styles[active_button_index] = active_style

    return styles

# --------------------------
# Callback function to update slider range (historical data plot)
@callback(
    [Output('slct_year', 'min'),
     Output('slct_year', 'max'),
     Output('slct_year', 'value'),
     Output('slct_year', 'marks')],
    [Input('btn-all-hist', 'n_clicks'),
     Input('btn-30yr-hist', 'n_clicks'),
     Input('btn-20yr-hist', 'n_clicks'),
     Input('btn-10yr-hist', 'n_clicks')]
)
def update_slider_hist(all_btn, btn_30yr, btn_20yr, btn_10yr):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if 'btn-all-hist' in changed_id:
        start_year = min(YEARS)
    elif 'btn-30yr-hist' in changed_id:
        start_year = max(YEARS) - 30
    elif 'btn-20yr-hist' in changed_id:
        start_year = max(YEARS) - 20
    elif 'btn-10yr-hist' in changed_id:
        start_year = max(YEARS) - 10
    else:
        start_year = min(YEARS)  # default to all years
    
    end_year = max(YEARS)

    return start_year, end_year, end_year, {
        str(start_year): {
            "label": str(start_year),
            "style": {"color": "#7fafdf"},
        },
        str(end_year): {
            "label": str(end_year),
            "style": {"color": "#7fafdf"},
        }
    }


## ----------------------------------------
## Callbacks for the spatial comparison ANPP plots

# --------------------------
# Polar plot
@callback(
    [Output('polar-graph', 'figure'),
     Output('polar-graph', 'style')],
    [Input('autocomplete-input', 'value'),
     Input('miles-input', 'value'),
     Input('choropleth-map', 'clickData'),
     Input('slct_year', 'value'),
     Input('selected-data-store', 'children')]
)
def update_polar(by_county, miles, clickData, option_slctd, selected_data_store):

    dff = gdf_hist[gdf_hist["year"] == option_slctd]

    # Creating predicted_anpp variable from the three anpp possible variables variables
    # dff['predicted_anpp'] = np.where(
    #     dff['anpp_lbs_ac'].notna(), dff['anpp_lbs_ac'],
    #     np.where(
    #         (current_month in [4, 5]),
    #         dff['predicted_spring_anpp_lbs_ac'],
    #         dff['predicted_summer_anpp_lbs_ac']
    #     )
    # )

    # Find the most recent report_date in df_forecast
    most_recent_report_date = pd.to_datetime(df_forecast['report_date'].max())    
    # Extract the month from the most recent report_date
    most_recent_month = most_recent_report_date.month

    # Creating predicted_anpp variable from the three anpp possible variables variables
    dff['predicted_anpp'] = np.where(
        dff['anpp_lbs_ac'].notna(), dff['anpp_lbs_ac'],
        np.where(
            (most_recent_month in [4, 5]),
            dff['predicted_spring_anpp_lbs_ac'],
            dff['predicted_summer_anpp_lbs_ac']
        )
    )

    # Identify which input triggered the callback
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    projected_crs = "EPSG:4326"

    # Get location point from which to draw the buffer
    # Location based on county polygon centroid
    if triggered_id in ['miles-input','slct_year', 'autocomplete-input'] and by_county is not None:
        sw_county = counties_gpd[counties_gpd['name'] == by_county]
        centroid = sw_county.to_crs(projected_crs).geometry.centroid.iloc[0]
        point = Point(centroid.x, centroid.y)

    # Location based on selected cell
    elif triggered_id in ['miles-input','slct_year', 'choropleth-map'] and clickData is not None:
        id_value = clickData['points'][0]['customdata'][0]
        selected_cell = dff[dff['gridid'] == id_value]
        centroid = selected_cell.to_crs(projected_crs).geometry.centroid.iloc[0]
        point = Point(centroid.x, centroid.y)

    # Location based on area selected centroid
    elif triggered_id in ['miles-input','slct_year', 'selected-data-store'] and selected_data_store is not None:
        formatted_selected_data =  json.loads(selected_data_store)
        dff_forcast_selected = gdf_forecast[gdf_forecast['gridid'].isin(formatted_selected_data)]
        combined_geometry = dff_forcast_selected.geometry.unary_union
        single_polygon = combined_geometry.convex_hull
        centroid = single_polygon.centroid
        point = Point(centroid.x, centroid.y)

    else: # default data from county selection
        sw_county = counties_gpd[counties_gpd['name'] == by_county]
        centroid = sw_county.to_crs(projected_crs).geometry.centroid.iloc[0]
        point = Point(centroid.x, centroid.y)

    # Input distance in miles. Transform to the unit of the CRS used (meters)
    buffer_distance_meters = miles * 1609.34
    lon, lat = centroid.x, centroid.y
    wgs84 = CRS('EPSG:4326')
    my_projection = CRS(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m no_defs")
    project = Transformer.from_crs(wgs84, my_projection, always_xy=True).transform
    point_in_meters = transform(project, point)
    # Create buffer
    buffer = Point(point_in_meters).buffer(buffer_distance_meters)
    project_back = Transformer.from_crs(my_projection, wgs84, always_xy=True).transform
    buffer_wgs84 = transform(project_back, buffer)
    buffer_gdf = gpd.GeoDataFrame(geometry=[buffer_wgs84], crs="EPSG:4326")
    # Intersect the buffer with the grid
    inter = gpd.overlay(dff, buffer_gdf, how='intersection')
    circle_centroid = buffer_gdf.geometry.centroid.iloc[0]

    # Prepare data for polar chart
    sums_and_counts = []
    for _, poly in inter.iterrows():
        center = poly.geometry.centroid
        direction = np.arctan2(center.y - circle_centroid.y, center.x - circle_centroid.x)
        sums_and_counts.append((direction, poly['predicted_anpp']))

    grouped_data = {}
    for direction, value in sums_and_counts:
        direction_degrees = np.degrees(direction) 
        direction_degrees = (direction_degrees - 90) % 360  
        direction_degrees = (360 - direction_degrees) % 360  
        direction_rounded = np.round(direction_degrees / 20) * 20
        direction_rounded = 0 if direction_rounded == 360 else direction_rounded

        if direction_rounded in grouped_data:
            grouped_data[direction_rounded].append(value)
        else:
            grouped_data[direction_rounded] = [value]

    means_and_dirs_rounded = [(direction, np.mean(values)) for direction, values in grouped_data.items()]
    dirs_rounded, means_rounded = zip(*means_and_dirs_rounded)

    df = pd.DataFrame({
        'direction': dirs_rounded,
        'value': means_rounded
    })

    # Create the polar chart 
    fig = px.bar_polar(df, r='value', theta='direction', color='value', 
                       color_continuous_scale='YlGnBu', range_r=[min(means_rounded), max(means_rounded)],
                       )

    fig.update_traces(
        hovertemplate="%{r:.2f} lb/ac"
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False),
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode='array',
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=0, b=0,
                    autoexpand=True),
    )

    return fig, {}

# --------------------------
# Violin and gradient plot
@callback(
     Output('violin-gradient-plot', 'src'),
    [Input('autocomplete-input', 'value'),
     Input('miles-input', 'value'),
     Input('choropleth-map', 'clickData'),
     Input('slct_year', 'value'),
     Input('selected-data-store', 'children')],
    )
def update_violin_gradient_plot(by_county, miles, clickData, option_slctd,selected_data_store):

    dff = gdf_hist[gdf_hist["year"] == option_slctd]

    # Creating predicted_anpp variable from the three anpp possible variables variables
    # dff['predicted_anpp'] = np.where(
    #     dff['anpp_lbs_ac'].notna(), dff['anpp_lbs_ac'],
    #     np.where(
    #         (current_month in [4, 5]),
    #         dff['predicted_spring_anpp_lbs_ac'],
    #         dff['predicted_summer_anpp_lbs_ac']
    #     )
    # )

    # Find the most recent report_date in df_forecast
    most_recent_report_date = pd.to_datetime(df_forecast['report_date'].max())    
    # Extract the month from the most recent report_date
    most_recent_month = most_recent_report_date.month

    # Creating predicted_anpp variable from the three anpp possible variables variables
    dff['predicted_anpp'] = np.where(
        dff['anpp_lbs_ac'].notna(), dff['anpp_lbs_ac'],
        np.where(
            (most_recent_month in [4, 5]),
            dff['predicted_spring_anpp_lbs_ac'],
            dff['predicted_summer_anpp_lbs_ac']
        )
    )
    
    # Identify which input triggered the callback
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    projected_crs = "EPSG:4326"

    # Get location point from which to draw the buffer
    # Location based on county polygon centroid
    if triggered_id in ['miles-input','slct_year', 'autocomplete-input'] and by_county is not None:
        sw_county = counties_gpd[counties_gpd['name'] == by_county]
        centroid = sw_county.to_crs(projected_crs).geometry.centroid.iloc[0]
        point = Point(centroid.x, centroid.y)

    # Location based on selected cell
    elif triggered_id in ['miles-input','slct_year', 'choropleth-map'] and clickData is not None:
        id_value = clickData['points'][0]['customdata'][0]
        selected_cell = dff[dff['gridid'] == id_value]
        centroid = selected_cell.to_crs(projected_crs).geometry.centroid.iloc[0]
        point = Point(centroid.x, centroid.y)

    # Location based on area selected centroid
    elif triggered_id in ['miles-input','slct_year', 'selected-data-store'] and selected_data_store is not None:
        formatted_selected_data =  json.loads(selected_data_store)
        dff_forcast_selected = gdf_forecast[gdf_forecast['gridid'].isin(formatted_selected_data)]
        combined_geometry = dff_forcast_selected.geometry.unary_union
        single_polygon = combined_geometry.convex_hull
        centroid = single_polygon.centroid
        point = Point(centroid.x, centroid.y)

    else: # default data from county selection
        sw_county = counties_gpd[counties_gpd['name'] == by_county]
        centroid = sw_county.to_crs(projected_crs).geometry.centroid.iloc[0]
        point = Point(centroid.x, centroid.y)
  
    # Input distance in miles. Transform to the unit of the CRS used (meters)
    buffer_distance_meters = miles * 1609.34 
    lon, lat = centroid.x, centroid.y
    wgs84 = CRS('EPSG:4326')
    my_projection = CRS(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m no_defs")
    project = Transformer.from_crs(wgs84, my_projection, always_xy=True).transform
    point_in_meters = transform(project, point)
    # Create buffer
    buffer = Point(point_in_meters).buffer(buffer_distance_meters)
    project_back = Transformer.from_crs(my_projection, wgs84, always_xy=True).transform
    buffer_wgs84 = transform(project_back, buffer)
    buffer_gdf = gpd.GeoDataFrame(geometry=[buffer_wgs84], crs="EPSG:4326")
    # Intersect the buffer with the grid
    data = gpd.overlay(dff, buffer_gdf, how='intersection')
    # Find the row in the GeoDataFrame where the geometry contains the point
    mask = dff['geometry'].contains(point)
    # Get the value from the 'predicted_anpp' column for that row
    point_anpp = dff.loc[mask, 'predicted_anpp'].values[0]

    # Create the continuous gradient line
    gradient = np.linspace(0, 1, 256) # Range to cover colormap
    gradient = np.vstack((gradient, gradient)) # Make 2D
    min_val = data['predicted_anpp'].min()
    max_val = data['predicted_anpp'].max()
    data['predicted_anpp'] = data['predicted_anpp'].clip(lower=min_val, upper=max_val)

    # Define gradient plot properties
    # (Given the limitation of the plotly.graph_objects module and similars, 
    # the following is a suitable aproach to create the intended gradient scale chart)

    num_segments = 70 # Define number of segments for the color bar (given the)
    x_val = 0 # Define the values for yaxis
    cmap = 'YlGnBu' # Create the color map
    # Convert matplotlib colormap to plotly
    cmap = cm.get_cmap('YlGnBu')
    plotly_colors = ['rgb'+str(tuple(int(val*255) for val in cmap(i))) for i in np.linspace(0, 1, num_segments)]

    # Create the violin plot
    fig = go.Figure()

    fig.add_trace(go.Violin(
        x=data['predicted_anpp'],
        box_visible=False,
        line_color='rgba(0,0,0,0)',  # setting line color to transparent to remove contour line
        meanline_visible=False,
        fillcolor='rgba(255,255,255,0.4)',  # white fillcolor with 0.4 opacity
        opacity=0.9,
        points=False,  # this removes inner points
        hoverinfo='none',  # this removes hover information for the violin plot
        y0="predicted_anpp"
    ))

    # Create the gradient scale
    for x_val, color in zip(np.linspace(min_val, max_val, num_segments), plotly_colors):
        fig.add_trace(
            go.Scatter(
                x=[x_val],
                y=["predicted_anpp"],
                mode='markers',
                marker=dict(color=color, size=50),
                name='',
                hoverinfo='none',
                showlegend=False
            )
        )

    # Add a point at y = mean
    fig.add_trace(go.Scatter(
        y=["predicted_anpp"],
        x=[point_anpp],
        mode='markers',
        marker=dict(
            size=60,
            color='white',
            line=dict(
                width=3,
                color='black'
            )
        ),
        hovertemplate = "%{r:.2f} lb/ac"
    ))

    # Hide y-axis and remove all plot background lines
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis_zeroline=False,
        yaxis_zeroline=False,
        margin=dict(l=0, r=0, t=0, b=0, autoexpand=True),
        xaxis=dict(range=[min_val, max_val]) # Adding range for yaxis
    )

    # Update x and y axes to hide tick labels, grid lines and set y-axis range
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False) # example range, adjust as needed
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)

    # Convert the figure to an image for displaying purposes
    img_bytes = fig.to_image(format="png", scale=0.35)
    # Using PIL to rotate the image
    with Image.open(BytesIO(img_bytes)) as img:
        rotated_img = img.rotate(90, expand=True)
        buffered = BytesIO()
        rotated_img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
    encoding = b64encode(img_bytes).decode()
    img_b64 = "data:image/png;base64," + encoding
    return img_b64  # Return the base64 string for the image source


## ----------------------------------------
## Callbacks for the Market data

# --------------------------
# Get market data from API and display it
@callback(
    [Output('indicator-graph', 'figure'),
     Output('hidden-div_econ', 'children'),
     Output('indicator-graph', 'style')],
    [Input('location-dropdown', 'value'),
     Input('btn-all-forecast', 'n_clicks'),
     Input('btn-2yr-forecast', 'n_clicks'),
     Input('btn-1yr-forecast', 'n_clicks'),
     Input('btn-6mo-forecast', 'n_clicks'),
     State('hidden-div_econ', 'children')],
)
def update_econ(location, n1, n2, n3, n4, last_btn):

    ctx = dash.callback_context

    # Get the slug_id for the selected location and get the data from the MMN API
    selected_slug_id = next(item['slug_id'] for item in cattle_markets_list if item['market_location_name'] == location)
    endpoint = f"/services/v1.2/reports/{selected_slug_id}?q=commodity=Feeder Cattle;class=Heifers"
    data = get_data_from_mmnapi(api_key, endpoint)

    # Convert data into a dataframe
    if not isinstance(data, str):
        daily_cattle_sw_location = pd.DataFrame(data["results"])
    
    # Check if API works and write a message if it doesn't
    if isinstance(data, str) or not data.get("results"):
        # Return a figure with the "The access to the API is temporarily unavailable" message
        fig = go.Figure()
        fig.add_annotation(
            text="API access is temporarily unavailable",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="white")
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0, 
                        autoexpand=True))
        
        fig.update_yaxes(visible=False, showticklabels=False, showgrid=False)
        fig.update_xaxes(visible=False, showticklabels=False, showgrid=False)

        return fig, last_btn, {}
    
    else:
        # Data processing for valid data
        daily_cattle_sw_location['report_date'] = pd.to_datetime(daily_cattle_sw_location['report_date'])
        max_date = daily_cattle_sw_location['report_date'].max()
        min_date = daily_cattle_sw_location['report_date'].min()
        months_difference = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month

        # Determining the time range based on the triggered button
        if not ctx.triggered:
            months = months_difference
            last_btn = 'btn-all-forecast'  # default button
        else:
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == 'location-dropdown' and last_btn is not None:
                triggered_id = last_btn  # Use last button clicked if location-dropdown is triggered

            if triggered_id == 'btn-all-forecast':
                months = months_difference
                last_btn = 'btn-all-forecast'
            elif triggered_id == 'btn-2yr-forecast':
                months = 24
                last_btn = 'btn-2yr-forecast'
            elif triggered_id == 'btn-1yr-forecast':
                months = 12
                last_btn = 'btn-1yr-forecast'
            elif triggered_id == 'btn-6mo-forecast':
                months = 6
                last_btn = 'btn-6mo-forecast'

        # Preparing data for the indicator graph
        grouped_df = daily_cattle_sw_location.groupby('report_date')['avg_price'].mean().reset_index()
        grouped_df = grouped_df.sort_values('report_date')
        max_date = grouped_df['report_date'].max()
        one_year_before_max_date = max_date - pd.DateOffset(months=months)
        last_year_df = grouped_df[grouped_df['report_date'] >= one_year_before_max_date]

        # Calculating price change and setting the color based on the change
        price_change = last_year_df['avg_price'].iloc[-1] - last_year_df['avg_price'].iloc[0]
        color = 'green' if price_change >= 0 else 'red'
        fillcolor_base = '0,128,0' if price_change >= 0 else '128,0,0'  # Use RGB format for base color

        # Building the figure with gradient fill for the scatter plot
        # (Given the limitation of the plotly.graph_objects module and similars, 
        # the following is a suitable aproach to create a transparent gradient below the line graph)        
        
        fig = go.Figure()
        num_layers = 20
        base_y = last_year_df['avg_price'].min()
        range_y = last_year_df['avg_price'].max() - base_y

        # Adding gradient layers
        for i in range(num_layers - 1):
            fraction = i / num_layers
            y_values = base_y + (last_year_df['avg_price'] - base_y) * fraction
            gradient_fillcolor = f'rgba({fillcolor_base},{(i + 1) / num_layers * 0.2})'
            fig.add_trace(go.Scatter(x=last_year_df['report_date'], y=y_values,
                                    mode='lines', 
                                    fill='tonexty', line=dict(width=0),
                                    fillcolor=gradient_fillcolor,
                                    hoverinfo='none'
                            ))

        # Topmost gradient layer to match exactly with the line graph's y-values
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
                        ))

        # Add indicator
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=last_year_df['avg_price'].iloc[-1],
            delta={'reference': last_year_df['avg_price'].iloc[0], 'relative': True, 'valueformat': '.1%', 'font': {'size': 13}},
            number={'valueformat': '$.1f', 'font':{'size': 17, 'color': '#dbe5f3'}},
            domain={'y': [0.99, 1], 'x': [0.1, 0.15]}
        ))

        # Setting up the y-axis and padding for the graph
        min_price = last_year_df['avg_price'].min()
        max_price = last_year_df['avg_price'].max()
        padding = (max_price - min_price) * 0.1

        # Final layout adjustments for the graph
        fig.update_yaxes(
            range=[min_price - padding, max_price + padding+20], 
            showticklabels=False, 
            showgrid=False
        )

        fig.update_xaxes(showticklabels=False, showgrid=False)

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            showlegend=False,
            margin=dict(l=0, r=0, t=19, b=0, autoexpand=True)
        )

        return fig, last_btn, {}
    
# --------------------------
# Callback function to update the active button style (Econ data plot)
@callback(
    [Output('btn-all-forecast', 'style'),
     Output('btn-2yr-forecast', 'style'),
     Output('btn-1yr-forecast', 'style'),
     Output('btn-6mo-forecast', 'style')
    ],
    [Input('btn-all-forecast', 'n_clicks'),
     Input('btn-2yr-forecast', 'n_clicks'),
     Input('btn-1yr-forecast', 'n_clicks'),
     Input('btn-6mo-forecast', 'n_clicks')
    ]
)
def update_active_button_econ(btn_5yr, btn_2yr, btn_1yr, btn_2mo):

    default_style = {'backgroundColor': 'transparent', 'color': '#dbe5f3'}
    active_style = {'backgroundColor': '#dbe5f3', 'color': '#282b3f'}

    ctx = dash.callback_context
    # If no buttons have been pressed yet, return default styles with btn-all-forecast set to active
    if not ctx.triggered:
        styles = [default_style for _ in range(4)]
        styles[0] = active_style  # Make btn-all-forecast active
        return styles

    # Get the id of the button that was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Dictionary to map button IDs to their index in the vals list
    button_indices = {
        'btn-all-forecast': 0,
        'btn-2yr-forecast': 1,
        'btn-1yr-forecast': 2,
        'btn-6mo-forecast': 3
    }

    # Index of the button that was clicked
    active_button_index = button_indices[button_id]
    # Initial default style
    styles = [default_style for _ in range(4)]
    # Set the active style for the clicked button
    styles[active_button_index] = active_style

    return styles


# --------------------------
# Choropleth map

@callback(
    Output('stored-dragmode', 'data'),
    [Input('choropleth-map', 'relayoutData'),
     Input('stored-dragmode', 'data')],
)
def update_stored_dragmode(relayoutData, stored_dragmode):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if input_id == 'choropleth-map' and relayoutData and 'dragmode' in relayoutData:
        return relayoutData['dragmode']
    return stored_dragmode


@callback(
    [Output('output_container', 'children'),
     Output('choropleth-map', 'figure'),
     Output('choropleth-map', 'style'),
     Output('stored-bounds-zoom', 'data')],
    [Input('slct_year', 'value'),
     Input('autocomplete-input', 'value'),
     Input('checkboxes-map', 'value'),
     Input('choropleth-map', 'relayoutData'),
     Input('stored-bounds-zoom', 'data'),
     Input('stored-dragmode', 'data')]
)
def update_choropleth_map(option_slctd, autocomplete, selected_aoi, relayoutData, stored_values, stored_dragmode):

    # Set zoom and bounds for the map based on triggers

    # Identify which input triggered the callback
    ctx = dash.callback_context
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Bounds and zoom for county selected
    # Loop through the features in the GeoJSON to find the desired polygon
    polygon = None
    for feature in counties_geojson['features']:
        if feature['properties']['name'] == autocomplete:
            polygon = feature['geometry']
            break
    if polygon:
        # Get bounds directly from the polygon object
        coords = polygon['coordinates'][0]
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        zoom = 7
    if input_id == 'autocomplete-input' and autocomplete:
        zoom = zoom
        center_lat = center_lat
        center_lon = center_lon

    # Bounds and zoom for AOI selected
    elif input_id == 'checkboxes-map'  and selected_aoi == ['gp']:
        zoom = 3.25
        center_lat = 41
        center_lon = -110
    elif input_id == 'checkboxes-map'  and selected_aoi == ['sw']:
        zoom = 5
        center_lat = 34.2
        center_lon = -109.5
    elif input_id == 'checkboxes-map'  and selected_aoi == ['sw', 'gp'] or selected_aoi == ['gp', 'sw'] or selected_aoi == [] :
        zoom = 3.25
        center_lat = 41
        center_lon = -110

    # Bounds and zoom from map interaction
    elif input_id == 'choropleth-map' and relayoutData and 'mapbox.zoom' in relayoutData and 'mapbox.center' in relayoutData:
        zoom = relayoutData['mapbox.zoom']
        center_lat = relayoutData['mapbox.center']['lat']
        center_lon = relayoutData['mapbox.center']['lon']
    
    # Zoom from zoom buttons
    elif input_id == 'choropleth-map' and relayoutData and 'mapbox.zoom' in relayoutData:
        zoom = relayoutData['mapbox.zoom']

    # Load the stored values if years buttons or the slider is clicked
    elif stored_values:
        stored_value_dict = stored_values[0]
        zoom = stored_value_dict['zoom']
        center_lat = stored_value_dict['center_lat']
        center_lon = stored_value_dict['center_lon']
    

    # Update map title based on AOI selection
    if ~counties_gpd[counties_gpd['name'] == autocomplete]['state_usps'].isin(['AZ', 'NM']).any():
        container = "ANPP (lb/ac) forecast" # gp title
    else:
        # Check if the current month is April or May for sw data
        if current_month in [4, 5]:
            container = "ANPP (lb/ac) Spring forecast"
        else:
            container = "ANPP (lb/ac) Summer forecast"


    # Prepare the data for the choropleth map 
    # Filter the data based on the selected year
    dff = df_hist[df_hist['year'] == option_slctd].copy()

    # Find the most recent report_date in df_forecast
    most_recent_report_date = pd.to_datetime(df_forecast['report_date'].max()) 
    # Extract the month from the most recent report_date
    most_recent_month = most_recent_report_date.month

    # Creating predicted_anpp variable from the three anpp possible variables variables
    dff['predicted_anpp'] = np.where(
        dff['anpp_lbs_ac'].notna(), dff['anpp_lbs_ac'],
        np.where(
            (most_recent_month in [4, 5]),
            dff['predicted_spring_anpp_lbs_ac'],
            dff['predicted_summer_anpp_lbs_ac']
        )
    )
    
    # Variable to display
    color ='predicted_anpp'

    # Filter data to display based on AOI selection
    if len(selected_aoi) == 2 or not selected_aoi:
        filtered_dff = dff
    else:
        # Find the corresponding list of gridids for the checkbox value
        selected_gridids = []
        for mapping in aoi_gridids:
            if mapping["aoi"] == selected_aoi[0]:
                selected_gridids = mapping["gridid"]
                break
        # Filter dataframe based on the selected gridids
        filtered_dff = dff[dff['gridid'].isin(selected_gridids)]


    # Create the choropleth map
    fig = px.choropleth_mapbox(
        filtered_dff,
        geojson=grid_geojson_path,
        featureidkey="properties.gridid",
        locations=filtered_dff["gridid"],
        color=color,
        color_continuous_scale="YlGnBu",
        mapbox_style="carto-positron",
        zoom=zoom, 
        center = {"lat": center_lat, "lon": center_lon},
        opacity=0.6,
        labels={color: f"{color} (lb/ac)"},
        range_color=(0, filtered_dff[color].max()),
        custom_data=[filtered_dff["gridid"]]
    )
    
    fig.update_traces(marker_line=dict(width=0), hovertemplate='%{z:.0f} lb/ac')

    fig.update_layout(
        mapbox_style="streets",
        mapbox_accesstoken=token,
        margin={"r": 0, "t": 29, "l": 0, "b": 0},
        mapbox_zoom=zoom,
        mapbox_center = {"lat": center_lat, "lon": center_lon},
        coloraxis_colorbar=dict(
            len=0.8,  
            x=0,  
            y=0.5,  
            title="",
        ),
        modebar_bgcolor= 'rgba(0,0,0,0)',
        modebar_color = '#97afcc',
        modebar_activecolor= '#282b3f',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        dragmode= stored_dragmode
    )

    return container, fig, {}, [{'zoom': zoom, 'center_lat': center_lat, 'center_lon': center_lon}]

# --------------------------
# AOI selection based on county selection
@callback(
    Output('checkboxes-map', 'value'),
    Input('autocomplete-input', 'value')
)
def update_aoi_checklist(selected_county):
    selected_entry = next((feature for feature in counties_geojson['features'] 
                           if feature['properties']['name'] == selected_county), None)
    # Determine the checklist value based on state_usps variable
    if selected_entry and selected_entry['properties']['state_usps'] in ['NM', 'AZ']:
        return ['sw']
    else:
        return ['gp']

# --------------------------
# Store data from lasso selection
@callback(
    Output('selected-data-store', 'children'),
    Input('choropleth-map', 'selectedData')
)
def store_selected_map_data(selectedData):
    if selectedData is not None:
        custom_data = [point['customdata'][0] for point in selectedData['points']]
        return json.dumps(custom_data)  # Store data as JSON string
    else:
        return None

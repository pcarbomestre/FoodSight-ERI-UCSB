# ------------------------------------------------------------------------------
# Libraries
import dash
from dash import dcc, html, Input, Output, callback
import geopandas as gpd
from shapely.geometry import Point
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------------------
# App configuration
external_styles = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css",
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css',
    dbc.themes.BOOTSTRAP # add the Bootstrap theme URL provided by dbc
]
app = dash.Dash(__name__, #use_pages=True,
                external_stylesheets= external_styles,
                # suppress_callback_exceptions=True,
                assets_folder ="static",
                assets_url_path="static"
                )
app.title = 'FoodSight'
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

application = app.server


# ------------------------------------------------------------------------------
# Reference pages
from pages.forecast import layout as forecast_layout
from pages.econ import layout as econ_layout
from pages.decision import layout as decision_layout
from pages.resources import layout as resources_layout


# ------------------------------------------------------------------------------
# Import data 

## AOI Grid
grid_geojson_path = 'static/grasscast_aoi_grid.geojson'
aoi_grid = gpd.read_file(grid_geojson_path).to_crs(epsg=4326)

## Counties
counties_geojson_path = 'static/grasscast_counties.geojson'
counties_gpd = gpd.read_file(counties_geojson_path).to_crs(epsg=4326)
counties_list = counties_gpd['name'].tolist()

# Counties dropdown options
def get_dropdown_options():
    return [{'label': f"{county['name']}, {county['state_usps']}", 'value': county['name']} for county in counties_gpd.to_dict('records')]


# ------------------------------------------------------------------------------
# Modal 
modal = dbc.Modal(
    [
        html.Img(id="modal-logo", src="static/modal-logo.png"),
        dbc.ModalBody("The application is currently in its Beta version, which offers early access features such as grassland productivity forecasting from Grasscast, cattle and hay market information from USDA, and a decision-making tool created by Colorado State University. This version provides limited data access. Intended solely for testing purposes."),
        dbc.ModalFooter(
            dbc.Button("Close", id="modal-close-button", className="ml-auto")
        ),
    ],
    id="welcome-modal",
    is_open=True,  # Set to True to have the modal open by default
)


# ------------------------------------------------------------------------------
# Layout
app.layout = html.Div(
    id="root",
    children=[
        modal,
        html.Meta(
            name='viewport', 
            content='width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no'
        ),  # Prevents phones from zooming when inputting values
        dcc.Location(id='url', refresh=False),
        html.Div(
            id="header",
            children=[
                html.Div(
                    id='header-title',
                    children=[
                        html.Div(
                            className='description-container',
                            children=[
                                html.Div(
                                    id="description-logo-container",
                                    children=[
                                        html.P(
                                            id="description",
                                            children=(
                                                "Explore projected grassland Aboveground Net Primary Productivity "
                                                "(ANPP) in your area or anywhere across the Great Plains and Southwest regions. The "
                                                "forecast integrates anticipated weather patterns to predict the "
                                                "production for spring and summer. Stay informed about local "
                                                "agricultural trends with real-time market price tracking for hay and "
                                                "cattle, empowering you to make informed decisions about your farming "
                                                "and ranching activities."
                                            ),
                                        ),
                                        html.Img(id="logo", src=app.get_asset_url("logo.png")),
                                        html.Div(
                                            id="info-button-container",
                                            children=[
                                                html.I(className="fa fa-info-circle", id="info_btn"),
                                                dbc.Tooltip(
                                                    id="info-tooltip",
                                                    target="info_btn",
                                                    placement="left"
                                                ),
                                            ],
                                        ),
                                    ]
                                ),
                                html.Div(
                                    id="controls-container",
                                    children=[
                                        html.Div(
                                            id="location-container",
                                            children=[
                                                html.Div(
                                                    id="location-elements",
                                                    children=[
                                                        html.Button(
                                                            html.I(className="fa fa-crosshairs"), 
                                                            id="update_btn",
                                                            n_clicks=0,
                                                        ),
                                                        dcc.Geolocation(id="geolocation"),
                                                        dcc.Dropdown(
                                                            id='autocomplete-input',
                                                            className='location-dropdown',
                                                            options=get_dropdown_options(),
                                                            value='none',
                                                            multi=False,
                                                            placeholder='Select County...',
                                                            search_value=''
                                                        ),
                                                    ]
                                                ),
                                                dcc.Link(
                                                    children=html.Button(
                                                        html.I(className="fa fa-link"), 
                                                        id='resources-button-hidden',
                                                        n_clicks=0,
                                                    ),
                                                    href='/resources',
                                                    id='resources-link',
                                                    className="page-link"
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            id="page-links",
                                            children=[
                                                dcc.Link(
                                                    children=html.Button(
                                                        'Forecast info',
                                                        className="page-button",
                                                        id='forecast-button'
                                                    ),
                                                    href='/forecast',
                                                    className="page-link"
                                                ),
                                                dcc.Link(
                                                    children=html.Button(
                                                        'Market info',
                                                        className="page-button",
                                                        id='econ-button'
                                                    ),
                                                    href='/econ',
                                                    className="page-link"
                                                ),
                                                dcc.Link(
                                                    children=html.Button(
                                                        'Decision tool',
                                                        className="page-button",
                                                        id='decision-button'
                                                    ),
                                                    href='/decision',
                                                    className="page-link"
                                                ),
                                                dcc.Link(
                                                    children=html.Button(
                                                        html.I(className="fa fa-link"), 
                                                        id='resources-button',
                                                        n_clicks=0,
                                                    ),
                                                    href='/resources',
                                                    id='resources-link-hidden',
                                                    className="page-link"
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ]
                        ),
                    ]
                ),
            ],
        ),
        html.Div(id='page-content')
    ]
)


# ------------------------------------------------------------------------------
# Callbacks

# --------------------------
# Closing the modal 
@app.callback(
    Output("welcome-modal", "is_open"),
    [Input("modal-close-button", "n_clicks")],
    [dash.dependencies.State("welcome-modal", "is_open")]
)
def closing_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# --------------------------
# Activate Geolocation
@app.callback(Output("geolocation", "update_now"), Input("update_btn", "n_clicks"))
def activate_geolocation(click):
    return True if click and click > 0 else False

# --------------------------
# Update dropdown input based on user location
@app.callback(
    Output('autocomplete-input', 'value'),
    [Input('geolocation', 'position')]
)
def update_dropdown_input(position):
    # Default coordinates if user is not in the AOI
    default_coordinates = [35.685421459731884, -105.99264908645465]
    print("location browser",position)
    if position and 'lat' in position and 'lon' in position:
        point = Point(position['lat'], position['lon'])
        if aoi_grid.contains(point).any():
            coordinates = [position['lat'], position['lon']]
        else:
            coordinates = default_coordinates
    else:
        # If no geolocation information acquired, set to default coordinates
        coordinates = default_coordinates

    point = Point(coordinates[1], coordinates[0])
    polygon = counties_gpd.loc[counties_gpd.geometry.contains(point)]
    
    if not polygon.empty:
        polygon_name = polygon['name'].values[0]
        dropdown_options = get_dropdown_options()
        if polygon_name in [option['value'] for option in dropdown_options]:
            return polygon_name
            
    # return None if polygon_name is not in dropdown_options
    return None

# --------------------------
# Callback to render the pages based on the URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname in (None, '/', '/forecast'):
        return forecast_layout
    elif pathname == '/econ':
        return econ_layout
    elif pathname == '/decision': 
        return decision_layout
    elif pathname == '/resources': 
        return resources_layout
    else:
        return forecast_layout  # This is the default page

# --------------------------
# Callback to set the active page button style
@app.callback(
    [Output('forecast-button', 'style'), 
     Output('econ-button', 'style'),
     Output('decision-button', 'style'),
     Output('resources-button', 'style'),
     Output('resources-button-hidden', 'style')],
    [Input('url', 'pathname')]
)
def update_button_style(pathname):
    default_style = {}
    dark_forecast = {'background-color': '#dbe5f3', 'border': 'none'}
    dark_econ = {'background-color': '#282b3f', 'color':'white', 'border': 'none'}
    dark_decision = {'background-color': '#efb750', 'border': 'none'}
    dark_resources = {'background-color': '#e3dfd8', 'border': 'none'}

    
    if pathname in (None, '/', '/forecast'):
        return dark_forecast, default_style, default_style, default_style, default_style
    elif pathname == '/econ':
        return default_style, dark_econ, default_style, default_style, default_style
    elif pathname == '/decision':
        return default_style, default_style, dark_decision, default_style, default_style
    elif pathname == '/resources':
        return default_style, default_style, default_style, dark_resources, dark_resources
    else:
        return default_style, default_style, default_style, default_style  # default style for all buttons

# --------------------------
# Callback to update page description
@app.callback(
    Output('info-tooltip', 'children'),
    [Input('url', 'pathname')]
)
def update_tooltip_message(pathname):
    if pathname in (None, '/', '/forecast'):
        return "This section presents the Grassland Productivity Forecast generated by Grasscast from the National Drought Mitigation Center at the University of Nebraska-Lincoln. The forecast is summarized based on county or map selection. Expected production is correlated with anticipated climate scenarios from the NOAA Climate Prediction Center. Users can access the most recent forecast value released and track forecast trends until the end of each season. Additionally, one can navigate through historical data to view past productivity. The platform also enables users to spatially identify areas with higher productivity in comparison to a current location or a selected location on the map. This feature is particularly useful for exploring productivity across the southwest plains. Ranchers and land managers should use this information in combination with their local knowledge of soils, plant communities, topography, and management to help with decision-making."
    elif pathname == '/econ':
        return "This section provides access to nominal data from several cattle and hay market auctions. The data is sourced from the MyMarketNews API, a USDA service that offers unbiased, timely, and accurate market information for hundreds of agricultural commodities and their related products. This interface features multiple tabs, enabling users to select a specific time range, cattle or hay type, state, and auction market. For cattle, users can choose between viewing daily average prices or monthly aggregated prices. Furthermore, users can visualize the relationship between prices and weight based on the most recent auction data. For hay, the platform showcases daily average price trends across various markets."
    elif pathname == '/decision':
        return "This section integrates the 'Strategies for Beef Cattle Herds During Times of Drought,' designed by Jeffrey E. Tranel, Rod Sharp, & John Deering from the Department of Agriculture and Business Management at Colorado State University. This decision tool aims to assist cow-calf producers in comparing the financial implications of various management strategies during droughts when grazing forage becomes scarce. It serves as a guide only. Producers should consult with their lenders, tax practitioners, and/or other professionals before making any final decisions.",
    elif pathname == '/resources':
        return "Details and links to the resources used in this application."
        return ""


# ------------------------------------------------------------------------------
# Start Dash on local machine
if __name__ == '__main__':
    application.run(debug=True, port=8080)
 
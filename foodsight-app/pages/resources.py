
# ------------------------------------------------------------------------------
# Libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


dash.register_page(__name__)

# ------------------------------------------------------------------------------
# Layout
layout = html.Div(
    id="resources_text",
    children=[
        html.Div(
            id="resources_intro_content",
            children=[
                html.H2('FoodSight Resources'),
                html.P([
                    'FoodSight combines a range of resources from various sources, including government agencies and universities, ',
                    'into a user-friendly platform. This integration facilitates access to data, enhancing its representation, and ',
                    'providing basic analysis tools. Among these resources, the core components of the app include:'
                ])
            ]
        ),
        html.Hr(),
        html.Div(
            id="resources_details_content",
            children=[
                html.H3('Productivity Forecast'),
                html.Div(
                    [
                        html.Img(
                            className="resources-picture",
                            src='static/resources_img1.png',
                            alt='resources_img1'
                        ),
                        html.Div(
                            [
                                html.P([
                                    'The Grassland Productivity Forecast is a GrassCast product developed by the University of Nebraska-Lincoln, ',
                                    'specifically designed for land managers and ranchers. This tool utilizes nearly 40 years of historical weather ',
                                    'and vegetation data, combined with seasonal precipitation forecasts, to predict grassland productivity. ',
                                    'It assesses whether productivity, measured in pounds per acre, is likely to be above-normal, near-normal, or ',
                                    'below-normal for the upcoming season. GrassCast is updated bi-weekly during spring and summer, adjusting to the ',
                                    'expected weather for that season, thus providing crucial insights for grazing management.'
                                ]),
                                html.Br(),
                                html.P([
                                    'You can learn more about the project and access the forecast data in the form of static maps and CSV files at ',
                                    html.A('GrassCast', href='https://grasscast.unl.edu', target='_blank'), '.'
                                ]),
                                html.P([
                                    'To know what forecast scenario is more likely to occur, you can visit the ',
                                    html.A('long-range precipitation outlooks provided by NOAA', href='https://www.cpc.ncep.noaa.gov/products/predictions/long_range/interactive/index.php', target='_blank'), '.'
                                ]),
                            ]
                        )
                    ],
                    className="resources-picture-container"
                ),
                html.Hr(),
                html.H3('Market Data'),
                html.Div(
                    [
                        html.Img(
                            className="resources-picture",
                            src='static/resources_img2.png',
                            alt='resources_img2'
                        ),
                        html.Div(
                            [
                                html.P([
                                    html.A('USDA Market News', href='https://www.ams.usda.gov/market-news', target='_blank'),
                                    ' provides essential resources for those interested in livestock market information. ',
                                    'You can access detailed historical data and reports on sales, nominal prices, volumes, and market trends for various ',
                                    'agricultural categories and commodities. This ',
                                    html.A('data is available for download', href='https://www.marketnews.usda.gov/mnp/ls-report-config?category=Calves', target='_blank'),
                                    ' in .xls, .txt, .xml, and .pdf formats, covering records from 2000 to 2019 depending on the commodity. For the most recent data—2019 and ',
                                    'onwards—, USDA provides free access to the ',
                                    html.A('My Market News API', href='https://mymarketnews.ams.usda.gov', target='_blank'), '. This API is a powerful tool for ',
                                    'developers and analysts, offering customized market data feeds and integration capabilities for several systems ',
                                    'or applications. These resources—feeding FoodSight’s markets page— are invaluable for stakeholders in the ',
                                    'livestock industry, providing real-time and detailed market data to support buying, selling, and production decisions.'
                                ]),
                            ]
                        )
                    ],
                    className="resources-picture-container"
                ),
                html.Hr(),
                html.H3('Decision Support Tool'),
                html.Div(
                    [
                        html.Img(
                            className="resources-picture",
                            src='static/resources_img3.png',
                            alt='resources_img2'
                        ),
                        html.Div(
                            [
                                html.P([
                                    'Several farming and ranching decision support tools have been released and are publicly available online. For ',
                                    'the FoodSight beta version, we explored the potential interest of users in combining insights from the forecast ',
                                    'and market pages for informed ranching management decisions, especially during drought events. Therefore, we ',
                                    'incorporated guidelines and suggestions derived from \'Strategies for Beef Cattle Herds During Times of Drought\', ',
                                    'a tool designed by Jeffrey E. Tranel, Rod Sharp, & John Deering from the Department of Agriculture and Business ',
                                    'Management at Colorado State University. The goal of this decision tool is to assist cow producers in comparing the financial implications of different management strategies ',
                                    'during droughts when grazing forage is scarce.'
                                ]),
                                html.Br(),
                                html.P([
                                    'See ',
                                    html.A('Strategies for Beef Cattle Herds During Times of Drought', href='https://www.extension.colostate.edu', target='_blank'), 
                                    ' for more information. Tool available in Excel format.'
                                ])
                            ]
                        )
                    ],
                    className="resources-picture-container"
                ),
                html.Hr(),
                    html.Div([
                        html.P([
                            "Visit the ",
                            html.A("Project's Notebook", href='https://pcarbomestre.github.io/blog-posts/FoodSight-notebook/foodsight_notebook.html', target="_blank"),
                            " for more details on the resources and the data processing pipeline, or visit the project's ",
                            html.A("GitHub repository", href='https://github.com/pcarbomestre/FoodSight-ERI-UCSB', target="_blank"),
                            "."
                        ]),
                    ])
            ]
        ),
    ]
)



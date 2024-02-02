# ------------------------------------------------------------------------------
# Libraries
import dash
from dash import  dcc, html, Input, Output, State, callback
from dash import dash_table 
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
from datetime import datetime
import plotly.graph_objects as go
import math
import pandas as pd

dash.register_page(__name__)

# ------------------------------------------------------------------------------
# Define variables

# Get current month and year
now = datetime.now()
current_month = now.month
current_year = now.year

# ------------------------------------------------------------------------------
# Layout

layout = html.Div(
    [
        html.Div(
            id="app-decision-container",
            children=[
                html.Div(
                    id="upper-row-container",
                    children=[
                        html.Div(
                            id="decision-input-container",
                            children=[
                                dbc.Button(
                                    "Input information +",
                                    id="unfold-button",
                                    className="unfold-button",
                                ),
                                dbc.Collapse(
                                    html.Div(
                                        id="decision-input-contents",
                                        children=[
                                        # COWS
                                        html.Div([
                                            html.H4("COWS", id="button-cows", className='decision-collapse-button'),
                                            html.Hr(),
                                            html.Div([
                                                 html.Table([
                                                    html.Tr([html.Td('Herd Size (head)'), html.Td(dcc.Input(value=200, type='number', id='herd-size'))]),
                                                    html.Tr([html.Td('Average Cow Weight (lbs)'), html.Td(dcc.Input(value=1200, type='number', id='avg-cow-weight'))]),
                                                    html.Tr([html.Td('Current Value of Cows (per cow)'), html.Td(dcc.Input(value=950, type='number', id='current-value-cow'))]),
                                                    html.Tr([html.Td('Number of Cows Culled in a Normal Year'), html.Td(dcc.Input(value=15, type='number', id='cows-culled'))]),
                                                    html.Tr([html.Td('Annual "Cow" Costs'), html.Td(dcc.Input(value=650, type='number', id='annual-cow-costs'))]),
                                                ],className='table-wrapper')
                                            ], id="collapse-cows"),
                                        ], className='upper-row-section'),
                                        # CALVES
                                        html.Div([
                                            html.H4("CALVES", id="button-calves", className='decision-collapse-button'),
                                            html.Hr(),
                                            html.Div([
                                                html.Div([  # This div represents column one
                                                    html.Table([
                                                        html.Tr([html.Td('Average Weaning Percentage'), html.Td(dcc.Input(value=80, type='number', id='avg-weaning-percentage'))]),
                                                        html.Tr([html.Td('Average Percent of Calves Sold'), html.Td(dcc.Input(value=75, type='number', id='percent-calves-sold'))]),
                                                        html.Tr([html.Td('Average Weight Currently (lbs)'), html.Td(dcc.Input(value=375, type='number', id='current-weight-calves'))]),
                                                        html.Tr([html.Td('Average Weight at Weaning (lbs)'), html.Td(dcc.Input(value=700, type='number', id='weight-at-weaning'))]),
                                                    ],className='table-wrapper'),
                                                ], className='calves-column'),
                                                html.Div([  # This div represents column two
                                                    html.Table([
                                                        html.Tr([html.Td('Prices (per lb) Current'), html.Td(dcc.Input(value=1.45, type='number', id='current-price-per-lb'))]),
                                                        html.Tr([html.Td('Expected at Weaning, This Year'), html.Td(dcc.Input(value=1.32, type='number', id='price-weaning-year1'))]),
                                                        html.Tr([html.Td('Expected at Weaning, Year 2'), html.Td(dcc.Input(value=1.25, type='number', id='price-weaning-year2'))]),
                                                        html.Tr([html.Td('Expected at Weaning, Years 3-5'), html.Td(dcc.Input(value=1.20, type='number', id='price-weaning-years3-5'))])
                                                    ],className='table-wrapper'),
                                                ], className='calves-column'),
                                            ], id="collapse-calves"),
                                        ], className='upper-row-section'),
                                        dbc.Tooltip(
                                            "Price at weaning ($/lb)",
                                            target="price-weaning-year1",
                                        ),
                                        dbc.Tooltip(
                                            "Price at weaning ($/lb)",
                                            target="price-weaning-year2",
                                        ),
                                        dbc.Tooltip(
                                            "Price at weaning ($/lb)",
                                            target="price-weaning-years3-5",
                                        ),
                                        # DROUGHT
                                        html.Div([
                                            html.H4("DROUGHT", id="button-drought", className='decision-collapse-button'),
                                            html.Hr(),
                                            html.Div([
                                                html.Table([
                                                    html.Tr([html.Td('Current Month'), html.Td(dcc.Input(value=current_month, type='number', id='current-month'))]),
                                                    html.Tr([html.Td('Current Year'), html.Td(dcc.Input(value=current_year, type='number', id='current-year'))]),
                                                    html.Tr([html.Td('Drought Ends Month'), html.Td(dcc.Input(value=current_month, type='number', id='drought-end-month'))]),
                                                    html.Tr([html.Td('Drought Ends Year'), html.Td(dcc.Input(value=current_year+1,max=current_year+4, type='number', id='drought-end-year'))]),
                                                ],className='table-wrapper'),
                                            ], id="collapse-drought"),
                                        ], className='upper-row-section'),
                                        dbc.Tooltip(
                                            "Calculations assume that cows are replaced in December of year that drought ends.",
                                            target="button-drought",
                                        ),
                                        # OTHER INFORMATION
                                        html.Div([
                                            html.H4("OTHER INFORMATION", id="button-other-info", className='decision-collapse-button'),
                                            html.Hr(),
                                            html.Div([
                                                html.Table([
                                                    html.Tr([html.Td('Interest Rate for Borrowed Money'), html.Td(dcc.Input(value=6.50, type='number', id='interest-borrowed-money'))]),
                                                    html.Tr([html.Td('Interest Rate for Invested Money'), html.Td(dcc.Input(value=2.25, type='number', id='interest-invested-money'))]),
                                                    html.Tr([html.Td('Average Tax Basis of Cows (per cow)'), html.Td(dcc.Input(value=0, type='number', id='tax-basis-cow'))]),
                                                    html.Tr([html.Td('Total Income Tax Rate (U.S. & State)'), html.Td(dcc.Input(value=19, type='number', id='income-tax-rate'))]),
                                                    html.Tr([html.Td('Capital Gains Tax Rate (U.S. & State)'), html.Td(dcc.Input(value=20, type='number', id='capital-gains-tax-rate'))]),
                                                ],className='table-wrapper'),
                                            ], id="collapse-other-info"),
                                        ], className='upper-row-section'),
                                    ],className='tables-input-container'),  
                                    id="collapse-input", is_open=False
                                )
                            ],
                        ),
                    ], className="row-decision"
                ),
                html.Div(
                    id="lower-row-container",
                    children=[
                        html.Div(
                            id="options-container",
                            children=[
                            html.Div(className='row-container', children=[
                                dbc.Button(
                                    "OPTION 1: PURCHASE ADDITIONAL FEED",
                                    id='toggle-button1',
                                    color="primary",  
                                    size="lg",  
                                    className="mb-3"  
                                ),
                                dbc.Collapse(
                                    id='collapse-content1',
                                    is_open=False,  
                                    children=[
                                        html.Div(className='table-container', children=[
                                            html.Table([
                                                html.Tr([
                                                    html.Th(''),
                                                    html.Th('lbs/day'),
                                                    html.Th('Price per Ton')
                                                ]),
                                                html.Tr([
                                                    html.Td('Hay'),
                                                    html.Td(dcc.Input(id='hay-lbs-day', type='number', value=22.00)),
                                                    html.Td(dcc.Input(id='hay-per-ton', type='number', value=200))
                                                ]),
                                                html.Tr([
                                                    html.Td('Other'),
                                                    html.Td(dcc.Input(id='other-lbs-day', type='number', value=0.00)),
                                                    html.Td(dcc.Input(id='other-per-ton', type='number', value=0))
                                                ]),
                                                html.Tr([
                                                    html.Td('Additional Cost ($/cow/day)'),
                                                    html.Td(''),
                                                    html.Td(html.Div(id='additional-cost-option1'))
                                                ]),
                                                dcc.Store(id='additional-cost-option1-stored'),
                                            ])
                                        ]),
                                        html.Div(className='graph-container', children=[
                                            dash_table.DataTable(
                                                id='option1-table-container',
                                                columns=[
                                                    {"name": ["Additional Feeding", "(days)"], "id": "Add'l Feed", 'type': 'numeric'},
                                                    {"name": ["Additional costs ($)", "Per Cow"], "id": "Per Cow", 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)},
                                                    {"name": ["Additional costs ($)", "Per Herd"], "id": "Per Herd", 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)},
                                                ],
                                                style_table={'overflowX': 'auto'},
                                                merge_duplicate_headers=True,
                                                style_as_list_view=True,
                                                # Styles:
                                                style_cell={
                                                    'textAlign': 'center',
                                                    'font-family': 'Arial',  
                                                    'height': '30px'
                                                },
                                                style_header={
                                                    'border-left': '1px solid',
                                                    'border-right': '1px solid',
                                                    'font-family': 'Arial',  
                                                    'fontWeight': 'bold'
                                                },
                                                style_data={
                                                    'border-left': '1px solid',
                                                    'border-right': '1px solid'
                                                }
                                            ),
                                        ]),
                                    ]
                                ),
                                html.Div(id='summary-option1', children=[
                                    html.Img(className= "option-decision-picture",
                                            src='static/option1.png', alt='Option 1 Image'),
                                    html.P('Learn the cost of feeding your herd based on hay prices and the duration of the drought.',
                                           className= "option-decision-description",),
                                ])
                            ]),
                            # Container for the second row
                            html.Div(className='row-container', children=[
                                dbc.Button(
                                    "OPTION 2: TRUCK PAIRS TO RENTED PASTURE",
                                    id='toggle-button2',
                                    color="primary",  
                                    size="lg",  
                                    className="mb-3" 
                                ),
                                dbc.Collapse(
                                    id='collapse-content2',
                                    is_open=False,  
                                    children=[
                                # Container for the second table
                                        html.Div(className='table-container', children=[
                                            html.Table([
                                                html.Tr([
                                                    html.Td('Distance to/from Pasture (miles)'),
                                                    html.Td(dcc.Input(id='distance-to-pasture', type='number', value=300))
                                                ]),
                                                html.Tr([
                                                    html.Td('Trucking Cost (per loaded mile)'),
                                                    html.Td(dcc.Input(id='trucking-cost', type='number', value=4.75))
                                                ]),
                                                html.Tr([
                                                    html.Td('Pasture Rent (per AUM)'),
                                                    html.Td(dcc.Input(id='pasture-rent', type='number', value=25.00))
                                                ]),
                                                html.Tr([
                                                    html.Td('Days on Rented Pasture (per year)'),
                                                    html.Td(dcc.Input(id='days-rented-pasture', type='number', value=120))
                                                ]),
                                                html.Tr([
                                                    html.Td('Additional Calf Death Loss, Year 1 (hd)'),
                                                    html.Td(dcc.Input(id='calf-death-loss', type='number', value=2))
                                                ]),
                                                html.Tr([
                                                    html.Td('Adjustment for Calf Weaning Weights'),
                                                    html.Td(dcc.Input(id='weaning-weight-adjustment', type='number', value=-10))
                                                ]),
                                                html.Tr([
                                                    html.Td('Total Other (not rent) Costs'),
                                                    html.Td(dcc.Input(id='total-other-costs', type='number', value=300))
                                                ]),
                                                html.Tr([
                                                    html.Td('Total Days/Months of Drought'),
                                                html.Td([
                                                        html.Div(id='drought-days', style={'display': 'inline-block'}),
                                                        html.Span(' / ', style={'margin': '0 5px'}),
                                                        html.Div(id="drought-months", style={'display': 'inline-block'})
                                                    ])
                                                ])
                                            ])
                                        ]),
                                        dash_table.DataTable(
                                            id='option2-table-container',
                                            columns=[
                                                {'name': '', 'id': ''},
                                                {'name':  ["Additional costs ($)",'Per Cow'], 'id': 'Per Cow', 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)},
                                                {'name':  ["Additional costs ($)",'Per Herd'], 'id': 'Per Herd', 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)}
                                            ],
                                            style_table={'overflowX': 'auto'},
                                            merge_duplicate_headers=True,
                                            style_cell={
                                                'textAlign': 'center',
                                                'font-family': 'Arial',
                                            },
                                            style_header={
                                                'border-left': '1px solid',
                                                'border-right': '1px solid',
                                                'font-family': 'Arial',
                                                'fontWeight': 'bold',
                                            },
                                            style_data={
                                                'border-left': '1px solid',
                                                'border-right': '1px solid'
                                            },
                                            style_as_list_view=True,
                                            style_data_conditional=[  # Style the last row with a darker background color
                                                {
                                                    'if': {'row_index': 6}, 
                                                    'fontWeight': 'bold',
                                                    'backgroundColor': '#efb750',
                                                    'height': '30px'
                                                }
                                            ],

                                        ),
                                        dcc.Store(id='total-per-herd-option2'),

                                    ]
                                ),
                                html.Div(id='summary-option2', children=[
                                    html.Img(className= "option-decision-picture",
                                            src='static/option3.png', alt='Option 3 Image'),
                                    html.P('Explore the expenses associated with relocating cattle to leased lands, taking into account factors such as distance, transportation expenses, rental costs, and the duration of the drought.',
                                           className= "option-decision-description",),
                                ])
                            ]),
                            html.Div(className='row-container', children=[
                                dbc.Button(
                                    "OPTION 3: SELL PAIRS & REPLACE COWS",
                                    id='toggle-button3',
                                    color="primary",  
                                    size="lg",  
                                    className="mb-3" 
                                ),
                                dbc.Collapse(
                                    id='collapse-content3',
                                    is_open=False,  
                                    children=[
                                        html.Div(className='table-container', children=[
                                            html.Table([
                                                html.Tr([
                                                    html.Td('Reduced Operating Costs, Year 1 (per cow)'),
                                                    html.Td(dcc.Input(id='reduced-operating-costs-year1', type='number', value=100))
                                                ]),
                                                html.Tr([
                                                    html.Td('Operating Costs, Year 2 (total)'),
                                                    html.Td(dcc.Input(id='operating-costs-year2', type='number', value=5000))
                                                ]),
                                                html.Tr([
                                                    html.Td('Operating Costs, Years 3-5 (total)'),
                                                    html.Td(dcc.Input(id='operating-costs-years3-5', type='number', value=5000))
                                                ]),
                                                html.Tr([
                                                    html.Td('Selling Costs (per cow)'),
                                                    html.Td(dcc.Input(id='selling-costs', type='number', value=20))
                                                ]),
                                                html.Tr([
                                                    html.Td('Cost of Replacement Animals (per cow)'),
                                                    html.Td(dcc.Input(id='cost-replacement-animals', type='number', value=1000))
                                                ])
                                            ])
                                        ]),
                                        dbc.Tooltip(
                                            "It is assumed that cows are replaced on last day of the second year after they are sold. For example, cows sold in 2018 are replaced on 12/31/2020.",
                                            target="cost-replacement-animals",
                                        ),
                                        dash_table.DataTable(
                                            id='option3-table-container',
                                            columns=[
                                                {"name": "", "id": ""},
                                                {"name": ["Additional costs ($)",'Per Cow'], "id": "Additional Costs Per Cow",'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)},
                                                {"name": ["Additional costs ($)",'Per Herd'], "id": "Additional Costs Per Herd",'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)}
                                            ],
                                            style_table={'overflowX': 'auto'},
                                            merge_duplicate_headers=True,
                                            style_cell={
                                                'textAlign': 'center',
                                                'font-family': 'Arial',
                                            },
                                            style_header={
                                                'border-left': '1px solid',
                                                'border-right': '1px solid',
                                                'font-family': 'Arial',
                                                'fontWeight': 'bold',
                                            },
                                            style_data={
                                                'border-left': '1px solid',
                                                'border-right': '1px solid'
                                            },
                                            style_as_list_view=True,
                                            style_data_conditional=[  # Style the last row with a darker background color
                                                {
                                                    'if': {'row_index': [4,10]}, 
                                                    'fontWeight': 'bold',
                                                    'backgroundColor': '#efb750',
                                                },
                                                {
                                                    'if': {'row_index': [11]}, 
                                                    'fontWeight': 'bold',
                                                    'backgroundColor': '#cf8b0e',
                                                    'color':'white',
                                                    'border-bottom': '1px solid black',
                                                    'border-top': '1px solid black',
                                                    'border-left': '1px solid black',
                                                    'border-right': '1px solid black',
                                                },
                                                {
                                                    'if': {
                                                        'column_id': 'Additional Costs Per Cow',
                                                        'filter_query': '{Additional Costs Per Cow} < 0'
                                                    },
                                                    'color': 'green',
                                                },
                                                {
                                                    'if': {
                                                        'column_id': 'Additional Costs Per Herd',
                                                        'filter_query': '{Additional Costs Per Herd} < 0'
                                                    },
                                                    'color': 'green'
                                                },
                                            ]

                                        )
                                    ]
                                ),
                                html.Div(id='summary-option3', children=[
                                    html.Img(className= "option-decision-picture",
                                            src='static/option2.png', alt='Option 2 Image'),
                                    html.P('Consider selling pairs and replacing cows. Examine the resulting revenues and the additional costs for the upcoming year and a three-year projection.',
                                           className= "option-decision-description",),
                                ])
                            ]),

                            # Hidden option 2
                            dcc.Store(id='actual-calves-sold'),
                            dcc.Store(id='actual-selling-weight'),
                            dcc.Store(id='expected-calf-sales'),
                            dcc.Store(id='actual-calf-sales'),
                            dcc.Store(id='difference-sales'),
                            dcc.Store(id='pairs-per-truck'),
                            dcc.Store(id='cows-per-truck'),
                            dcc.Store(id='trucks-needed-pairs'),
                            dcc.Store(id='trucks-needed-cows'),
                            dcc.Store(id='calves-to-sell'),
                       
                            # Hidden option 3
                            dcc.Store(id='store-expected-calf-sales-current-year'),
                            dcc.Store(id='store-actual-calf-sales'),
                            dcc.Store(id='store-difference'),
                            dcc.Store(id='store-expected-calf-sales-year2'),
                            dcc.Store(id='store-expected-calf-sales-year3'),
                            dcc.Store(id='store-cow-sales'),
                            dcc.Store(id='store-interest-income-year1'),
                            dcc.Store(id='store-interest-income-year2'),
                            dcc.Store(id='store-interest-income-year3'),

                            # Hidden drought times
                            dcc.Store(id='hidden-time-table-store'),
                            dcc.Store(id='drought-months-store'),
                            dcc.Store(id='drought-days-store'),
                            dcc.Store(id='drought-months-store2'),
                            dcc.Store(id='drought-days-store2'),
                            dcc.Store(id='drought-months-store3'),
                            dcc.Store(id='drought-days-store3'),
                            dcc.Store(id='drought-months-store4'),
                            dcc.Store(id='drought-days-store4'),

                            dcc.Store(id='output-comparison-tablesummary-data-store'),

                            html.Div(children=[
                                dcc.Graph(id='truck-table-container'),
                                dcc.Graph(id='hidden3-table-container'),
                                dcc.Graph(id='drought-table-container'),
                            ], style={'display': 'none'}),
                        ])
                    ],className="row-decision"
                ),
                html.Div(
                    id="bottom-row-container",
                        children=[
                            html.Div(
                                id="comparison-summary-container",
                                children=[
                                    dbc.Button(
                                        html.Span([
                                            "Compare the different strategies   ",
                                            html.I(id='dropdown-icon', className='fas fa-chevron-down ml-2')  # using Font Awesome for the icon
                                        ]),
                                        id='comparison-section-button',
                                        color="primary",
                                        size="lg",
                                        className="mb-3"
                                    ),
                                    dbc.Collapse(
                                    id='collapse-comparison-section',
                                    is_open=False,  
                                        children=[
                                            html.Div(id='output-comparison-summary'),
                                            html.Div(id= "summary-table", children=[
                                                dash_table.DataTable(
                                                    id='output-comparison-tablesummary-data',
                                                    columns = [
                                                        {'name': ["",""], 'id': ""},
                                                        {'name': ["","Normal conditions"], 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                        {'name': ["","Buy feed"], 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                        {'name': ["","Rent pasture"], 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                        {'name': ["Sell cows","Replace"], 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                        {'name': ["Sell cows","Do not replace"], 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                    ],                    
                                                    style_cell={
                                                        'textAlign': 'center',
                                                        'font-family': 'Arial',
                                                        # 'backgroundColor': '#bfbbb4',

                                                    },
                                                    style_header={
                                                        'font-family': 'Arial',
                                                        'fontWeight': 'bold',
                                                        # 'backgroundColor': '#8f8d89',
                                                    },
                                                    style_as_list_view=True,
                                                    merge_duplicate_headers=True,
                                                    style_data_conditional=[
                                                        {
                                                            'if': {'row_index': 2},  # Row 3 (indexing starts at 0)
                                                            'suffix': '%',
                                                        },
                                                        {
                                                            'if': {'row_index': [0, 3, 5, 7]},
                                                            'border-bottom': '1px solid black',
                                                        },
                                                        {
                                                            'if': {'column_id': 'Normal conditions',
                                                                'filter_query': '{Normal conditions} < 0'},
                                                            'color': 'red'
                                                        },
                                                        {
                                                            'if': {'column_id': 'Buy feed',
                                                                'filter_query': '{Buy feed} < 0'},
                                                            'color': 'red'
                                                        },
                                                        {
                                                            'if': {'column_id': 'Rent pasture',
                                                                'filter_query': '{Rent pasture} < 0'},
                                                            'color': 'red'
                                                        },
                                                        {
                                                            'if': {'column_id': 'Replace',
                                                                'filter_query': '{Replace} < 0'},
                                                            'color': 'red'
                                                        },
                                                        {
                                                            'if': {'column_id': 'Do not replace',
                                                                'filter_query': '{Do not replace} < 0'},
                                                            'color': 'red'
                                                        },
                                                    ],
                                                    style_table={'overflowX': 'scroll'}
                                                ),
                                            ], ),
                                            html.P('The table above provides a summary of the net worth changes over a 5-year period, comparing the three options outlined above, alongside the projected worth in the absence of any droughts. For further details, press the button below.',
                                                className= "option-decision-description",
                                                id="table-summary-description"),
                                            html.Div(children=[
                                                dbc.Button(
                                                    "Explore net worth changes by year +",
                                                    id='comparison-details-section-button',
                                                    color="primary",  
                                                    size="lg",  
                                                    className="mb-3" 
                                                ),
                                                dbc.Collapse(
                                                id='collapse-comparison-details-section',
                                                is_open=False,  
                                                    children=[
                                                        html.Div(
                                                            id="comparisons-container",
                                                            children=[
                                                            
                                                                html.H4("Current (Applicable) Net Worth", className='decision-collapse-button'),
                                                                html.Hr(),

                                                                dash_table.DataTable(
                                                                    id='output-comparison-table-currentsummary-data',
                                                                    columns=[
                                                                        {'name': ["",""], 'id': ""},
                                                                        {'name': ["","Normal conditions"], 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': ["","Buy feed"], 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': ["","Rent pasture"], 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': ["Sell cows", "Replace"], 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': ["Sell cows", "Do not replace"], 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                    ],
                                                                    merge_duplicate_headers=True,
                                                                    style_cell={
                                                                        'textAlign': 'center',
                                                                        'font-family': 'Arial',
                                                                    },
                                                                    style_header={
                                                                        'font-family': 'Arial',
                                                                        'fontWeight': 'bold',
                                                                    },
                                                                    style_as_list_view=True,
                                                                    style_data_conditional=[
                                                                        {'if': {'column_id': ""}, 'width': '30%'},  # setting width for the first column
                                                                        # {'if': {'column_type': 'numeric'}, 'width': '15%'},  # setting width for the rest of the columns
                                    
                                                                        {
                                                                            'if': {'row_index': [0, 1, 2, 3]},
                                                                            'fontWeight': 'bold',
                                                                            'backgroundColor': '#efb750',
                                                                        },
                                                                        {
                                                                            'if': {'row_index': 3},
                                                                            'backgroundColor': '#cf8b0e',
                                                                            'color': 'white',
                                                                            'border-bottom': '1px solid black',
                                                                            'border-top': '1px solid black',
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Normal conditions',
                                                                                'filter_query': '{Normal conditions} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Buy feed',
                                                                                'filter_query': '{Buy feed} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Rent pasture',
                                                                                'filter_query': '{Rent pasture} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Replace',
                                                                                'filter_query': '{Replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Do not replace',
                                                                                'filter_query': '{Do not replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                    ],
                                                                    style_table={ 
                                                                                'minWidth': '100px',
                                                                                'overflowX': 'auto'
                                                                                }
                                                                ),
                                                                html.Div([
                                                                    html.H4(id="compare-label", className='decision-collapse-button'),
                                                                    dbc.Button(
                                                                        "+ Details",
                                                                        id='compare-button1',
                                                                        className = "compare-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                    ),
                                                                ], className= "compare-label-container"),
                                                                html.Hr(),
                                                                dbc.Collapse(
                                                                    id='compare-collapse1',
                                                                    is_open=False,  
                                                                    children=[
                                                                        # Table for output-comparison-table-data with styles for rows 5-12
                                                                        dash_table.DataTable(
                                                                            id='output-comparison-table-data',
                                                                            columns=[
                                                                                {'name': "", 'id': ""},
                                                                                {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                            ],
                                                                            style_cell={
                                                                                'textAlign': 'center',
                                                                                'font-family': 'Arial',
                                                                            },
                                                                            style_header={
                                                                                'font-family': 'Arial',
                                                                                'fontWeight': 'bold'
                                                                            },
                                                                            style_as_list_view=True,
                                                                            style_data_conditional=[
                                                                                {'if': {'column_id': ""}, 'width': '30%'},
                                                                                {
                                                                                    'if': {'row_index': [1, 3]},
                                                                                    'border-bottom': '1px solid black',
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Normal conditions',
                                                                                        'filter_query': '{Normal conditions} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Buy feed',
                                                                                        'filter_query': '{Buy feed} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Rent pasture',
                                                                                        'filter_query': '{Rent pasture} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Replace',
                                                                                        'filter_query': '{Replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Do not replace',
                                                                                        'filter_query': '{Do not replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                            ],
                                                                            style_table={ 
                                                                                'minWidth': '300px',
                                                                                'overflowX': 'auto'
                                                                                }
                                                                        ),
                                                                    ]
                                                                ),
                                                                # Table for output-comparison-table-summary-data with styles for rows 13-16
                                                                dash_table.DataTable(
                                                                    id='output-comparison-table-summary-data',
                                                                    columns=[
                                                                        {'name': "", 'id': ""},
                                                                        {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                    ],
                                                                    style_cell={
                                                                        'textAlign': 'center',
                                                                        'font-family': 'Arial',
                                                                    },
                                                                    style_header={
                                                                        'font-family': 'Arial',
                                                                        'fontWeight': 'bold',
                                                                        'height': '1px !important',  
                                                                        'lineHeight': '0 !important',  
                                                                        'opacity': '0',
                                                                        'border-top': '1px solid white',
                                                                    },
                                                                    style_as_list_view=True,
                                                                    style_data_conditional=[
                                                                        {'if': {'column_id': ""}, 'width': '30%'},
                                                                        {
                                                                            'if': {'row_index': [0, 1, 2]},
                                                                            'fontWeight': 'bold',
                                                                            'backgroundColor': '#efb750',
                                                                        },
                                                                        {
                                                                            'if': {'row_index': 2},
                                                                            'backgroundColor': '#cf8b0e',
                                                                            'color': 'white',
                                                                            'border-bottom': '1px solid black',
                                                                            'border-top': '1px solid black',
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Normal conditions',
                                                                                'filter_query': '{Normal conditions} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Buy feed',
                                                                                'filter_query': '{Buy feed} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Rent pasture',
                                                                                'filter_query': '{Rent pasture} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Replace',
                                                                                'filter_query': '{Replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Do not replace',
                                                                                'filter_query': '{Do not replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                    ]
                                                                ),
                                                                html.Div([
                                                                    html.H4(id="compare-label2", className='decision-collapse-button'),
                                                                    dbc.Button(
                                                                        "+ Details",
                                                                        id='compare-button2',
                                                                        className = "compare-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                    ),
                                                                ], className= "compare-label-container"),
                                                                html.Hr(),
                                                                dbc.Collapse(
                                                                    id='compare-collapse2',
                                                                    is_open=False,  
                                                                    children=[
                                                                        # Table for output-comparison-table-data with styles for rows 5-12
                                                                        dash_table.DataTable(
                                                                            id='output-comparison-table2-data',
                                                                            columns=[
                                                                                {'name': "", 'id': ""},
                                                                                {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                            ],
                                                                            style_cell={
                                                                                'textAlign': 'center',
                                                                                'font-family': 'Arial',
                                                                            },
                                                                            style_header={
                                                                                'font-family': 'Arial',
                                                                                'fontWeight': 'bold',
                                                                            },
                                                                            style_as_list_view=True,
                                                                            style_data_conditional=[
                                                                                {'if': {'column_id': ""}, 'width': '30%'},
                                                                                {
                                                                                    'if': {'row_index': [2, 4]},
                                                                                    'border-bottom': '1px solid black',
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Normal conditions',
                                                                                        'filter_query': '{Normal conditions} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Buy feed',
                                                                                        'filter_query': '{Buy feed} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Rent pasture',
                                                                                        'filter_query': '{Rent pasture} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Replace',
                                                                                        'filter_query': '{Replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Do not replace',
                                                                                        'filter_query': '{Do not replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                            ],
                                                                            style_table={ 
                                                                                'minWidth': '300px',
                                                                                'overflowX': 'auto'
                                                                                }
                                                                        ),
                                                                    ]
                                                                ),
                                                                dash_table.DataTable(
                                                                    id='output-comparison-table2-summary-data',
                                                                    columns=[
                                                                        {'name': "", 'id': ""},
                                                                        {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                    ],
                                                                    style_cell={
                                                                        'textAlign': 'center',
                                                                        'font-family': 'Arial',
                                                                    },
                                                                    style_header={
                                                                        'font-family': 'Arial',
                                                                        'fontWeight': 'bold',
                                                                        'height': '1px !important',  
                                                                        'lineHeight': '0 !important',  
                                                                        'opacity': '0',
                                                                        'border-top': '1px solid white',
                                                                    },
                                                                    style_as_list_view=True,
                                                                    style_data_conditional=[
                                                                        {'if': {'column_id': ""}, 'width': '30%'},
                                                                        {
                                                                            'if': {'row_index': [0, 1, 2]},
                                                                            'fontWeight': 'bold',
                                                                            'backgroundColor': '#efb750',
                                                                        },
                                                                        {
                                                                            'if': {'row_index': 2},
                                                                            'backgroundColor': '#cf8b0e',
                                                                            'color': 'white',
                                                                            'border-bottom': '1px solid black',
                                                                            'border-top': '1px solid black',
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Normal conditions',
                                                                                'filter_query': '{Normal conditions} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Buy feed',
                                                                                'filter_query': '{Buy feed} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Rent pasture',
                                                                                'filter_query': '{Rent pasture} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Replace',
                                                                                'filter_query': '{Replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Do not replace',
                                                                                'filter_query': '{Do not replace} < 0'},
                                                                            'color': 'red'
                                                                        }
                                                                    ]
                                                                ),
                                                                html.Div([
                                                                    html.H4(id="compare-label3", className='decision-collapse-button'),
                                                                    dbc.Button(
                                                                        "+ Details",
                                                                        id='compare-button3',
                                                                        className = "compare-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                    ),
                                                                ], className= "compare-label-container"),
                                                                html.Hr(),
                                                                dbc.Collapse(
                                                                    id='compare-collapse3',
                                                                    is_open=False,  
                                                                    children=[
                                                                        # Table for output-comparison-table-data with styles for rows 5-12
                                                                        dash_table.DataTable(
                                                                            id='output-comparison-table3-data',
                                                                            columns=[
                                                                                {'name': "", 'id': ""},
                                                                                {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                            ],
                                                                            style_cell={
                                                                                'textAlign': 'center',
                                                                                'font-family': 'Arial',
                                                                            },
                                                                            style_header={
                                                                                'font-family': 'Arial',
                                                                                'fontWeight': 'bold',
                                                                            },
                                                                            style_as_list_view=True,
                                                                            style_data_conditional=[
                                                                                {'if': {'column_id': ""}, 'width': '30%'},
                                                                                {
                                                                                    'if': {'row_index': [2, 4]},
                                                                                    'border-bottom': '1px solid black',
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Normal conditions',
                                                                                        'filter_query': '{Normal conditions} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Buy feed',
                                                                                        'filter_query': '{Buy feed} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Rent pasture',
                                                                                        'filter_query': '{Rent pasture} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Replace',
                                                                                        'filter_query': '{Replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Do not replace',
                                                                                        'filter_query': '{Do not replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                            ],
                                                                            style_table={ 
                                                                                'minWidth': '300px',
                                                                                'overflowX': 'auto'
                                                                                }
                                                                        ),
                                                                    ]
                                                                ),
                                                                dash_table.DataTable(
                                                                    id='output-comparison-table3-summary-data',
                                                                    columns=[
                                                                        {'name': "", 'id': ""},
                                                                        {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                    ],
                                                                    style_cell={
                                                                        'textAlign': 'center',
                                                                        'font-family': 'Arial',
                                                                    },
                                                                    style_header={
                                                                        'font-family': 'Arial',
                                                                        'fontWeight': 'bold',
                                                                        'height': '1px !important',  
                                                                        'lineHeight': '0 !important',  
                                                                        'opacity': '0',
                                                                        'border-top': '1px solid white',
                                                                    },
                                                                    style_as_list_view=True,
                                                                    style_data_conditional=[
                                                                        {'if': {'column_id': ""}, 'width': '30%'},
                                                                        {
                                                                            'if': {'row_index': [0, 1, 2]},
                                                                            'fontWeight': 'bold',
                                                                            'backgroundColor': '#efb750',
                                                                        },
                                                                        {
                                                                            'if': {'row_index': 2},
                                                                            'backgroundColor': '#cf8b0e',
                                                                            'color': 'white',
                                                                            'border-bottom': '1px solid black',
                                                                            'border-top': '1px solid black',
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Normal conditions',
                                                                                'filter_query': '{Normal conditions} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Buy feed',
                                                                                'filter_query': '{Buy feed} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Rent pasture',
                                                                                'filter_query': '{Rent pasture} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Replace',
                                                                                'filter_query': '{Replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Do not replace',
                                                                                'filter_query': '{Do not replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                    ]
                                                                ),
                                                                html.Div([
                                                                    html.H4(id="compare-label4", className='decision-collapse-button'),
                                                                    dbc.Button(
                                                                        "+ Details",
                                                                        id='compare-button4',
                                                                        className = "compare-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                    ),
                                                                ], className= "compare-label-container"),
                                                                html.Hr(),
                                                                dbc.Collapse(
                                                                    id='compare-collapse4',
                                                                    is_open=False,  
                                                                    children=[
                                                                        # Table for output-comparison-table-data with styles for rows 5-12
                                                                        dash_table.DataTable(
                                                                            id='output-comparison-table4-data',
                                                                            columns=[
                                                                                {'name': "", 'id': ""},
                                                                                {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                            ],
                                                                            style_cell={
                                                                                'textAlign': 'center',
                                                                                'font-family': 'Arial',
                                                                            },
                                                                            style_header={
                                                                                'font-family': 'Arial',
                                                                                'fontWeight': 'bold',
                                                                            },
                                                                            style_as_list_view=True,
                                                                            style_data_conditional=[
                                                                                {'if': {'column_id': ""}, 'width': '30%'},
                                                                                {
                                                                                    'if': {'row_index': [2, 4]},
                                                                                    'border-bottom': '1px solid black',
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Normal conditions',
                                                                                        'filter_query': '{Normal conditions} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Buy feed',
                                                                                        'filter_query': '{Buy feed} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Rent pasture',
                                                                                        'filter_query': '{Rent pasture} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Replace',
                                                                                        'filter_query': '{Replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Do not replace',
                                                                                        'filter_query': '{Do not replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                            ],
                                                                            style_table={ 
                                                                                'minWidth': '300px',
                                                                                'overflowX': 'auto'
                                                                                }
                                                                        ),
                                                                    ]
                                                                ),
                                                                dash_table.DataTable(
                                                                    id='output-comparison-table4-summary-data',
                                                                    columns=[
                                                                        {'name': "", 'id': ""},
                                                                        {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                    ],
                                                                    style_as_list_view=True,
                                                                    style_cell={
                                                                        'textAlign': 'center',
                                                                        'font-family': 'Arial',
                                                                    },
                                                                    style_header={
                                                                        'font-family': 'Arial',
                                                                        'fontWeight': 'bold',
                                                                        'height': '1px !important',  
                                                                        'lineHeight': '0 !important',  
                                                                        'opacity': '0',
                                                                        'border-top': '1px solid white',
                                                                    },
                                                                    style_data_conditional=[
                                                                        {'if': {'column_id': ""}, 'width': '30%'},
                                                                        {
                                                                            'if': {'row_index': [0, 1, 2]},
                                                                            'fontWeight': 'bold',
                                                                            'backgroundColor': '#efb750',
                                                                        },
                                                                        {
                                                                            'if': {'row_index': 2},
                                                                            'backgroundColor': '#cf8b0e',
                                                                            'color': 'white',
                                                                            'border-bottom': '1px solid black',
                                                                            'border-top': '1px solid black',
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Normal conditions',
                                                                                'filter_query': '{Normal conditions} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Buy feed',
                                                                                'filter_query': '{Buy feed} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Rent pasture',
                                                                                'filter_query': '{Rent pasture} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Replace',
                                                                                'filter_query': '{Replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Do not replace',
                                                                                'filter_query': '{Do not replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                    ]
                                                                ),
                                                                html.Div([
                                                                    html.H4(id="compare-label5", className='decision-collapse-button'),
                                                                    dbc.Button(
                                                                        "+ Details",
                                                                        id='compare-button5',
                                                                        className = "compare-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                    ),
                                                                ], className= "compare-label-container"),
                                                                html.Hr(),
                                                                dbc.Collapse(
                                                                    id='compare-collapse5',
                                                                    is_open=False,  
                                                                    children=[
                                                                        # Table for output-comparison-table-data with styles for rows 5-12
                                                                        dash_table.DataTable(
                                                                            id='output-comparison-table5-data',
                                                                            columns=[
                                                                                {'name': "", 'id': ""},
                                                                                {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                                {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                            ],
                                                                            style_cell={
                                                                                'textAlign': 'center',
                                                                                'font-family': 'Arial',
                                                                            },
                                                                            style_header={
                                                                                'font-family': 'Arial',
                                                                                'fontWeight': 'bold',
                                                                            },
                                                                            style_as_list_view=True,
                                                                            style_data_conditional=[
                                                                                {'if': {'column_id': ""}, 'width': '30%'},
                                                                                {
                                                                                    'if': {'row_index': [2, 4]},
                                                                                    'border-bottom': '1px solid black',
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Normal conditions',
                                                                                        'filter_query': '{Normal conditions} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Buy feed',
                                                                                        'filter_query': '{Buy feed} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Rent pasture',
                                                                                        'filter_query': '{Rent pasture} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Replace',
                                                                                        'filter_query': '{Replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                                {
                                                                                    'if': {'column_id': 'Do not replace',
                                                                                        'filter_query': '{Do not replace} < 0'},
                                                                                    'color': 'red'
                                                                                },
                                                                            ],
                                                                            style_table={ 
                                                                                'minWidth': '300px',
                                                                                'overflowX': 'auto'
                                                                            }
                                                                        ),
                                                                    ]
                                                                ),
                                                                dash_table.DataTable(
                                                                    id='output-comparison-table5-summary-data',
                                                                    columns=[
                                                                        {'name': "", 'id': ""},
                                                                        {'name': "Normal conditions", 'id': "Normal conditions", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Buy feed", 'id': "Buy feed", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Rent pasture", 'id': "Rent pasture", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Replace", 'id': "Replace", 'type': 'numeric', 'format': {'specifier': '.0f'}},
                                                                        {'name': "Do not replace", 'id': "Do not replace", 'type': 'numeric', 'format': {'specifier': '.0f'}}
                                                                    ],
                                                                    style_as_list_view=True,
                                                                    style_cell={
                                                                        'textAlign': 'center',
                                                                        'font-family': 'Arial',
                                                                    },
                                                                    style_header={
                                                                        'font-family': 'Arial',
                                                                        'fontWeight': 'bold',
                                                                        'height': '1px !important',  
                                                                        'lineHeight': '0 !important',  
                                                                        'opacity': '0',
                                                                        'border-top': '1px solid white',
                                                                    },
                                                                    style_data_conditional=[
                                                                        {'if': {'column_id': ""}, 'width': '30%'},
                                                                        {
                                                                            'if': {'row_index': [0, 1, 2]},
                                                                            'fontWeight': 'bold',
                                                                            'backgroundColor': '#efb750',
                                                                        },
                                                                        {
                                                                            'if': {'row_index': 2},
                                                                            'backgroundColor': '#cf8b0e',
                                                                            'color': 'white',
                                                                            'border-bottom': '1px solid black',
                                                                            'border-top': '1px solid black',
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Normal conditions',
                                                                                'filter_query': '{Normal conditions} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Buy feed',
                                                                                'filter_query': '{Buy feed} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Rent pasture',
                                                                                'filter_query': '{Rent pasture} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Replace',
                                                                                'filter_query': '{Replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                        {
                                                                            'if': {'column_id': 'Do not replace',
                                                                                'filter_query': '{Do not replace} < 0'},
                                                                            'color': 'red'
                                                                        },
                                                                    ]
                                                                ),

                                                            ]
                                                        )
                                                    ]
                                                )
                                            ], style={'display': 'flex','flex-direction': 'column', 'justifyContent': 'center', 'width': '100%'}
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ]
                )
            ],
        ),
    ]
)


# ------------------------------------------------------------------------------
# Callbacks

@callback(
    [
        Output('collapse-content1', 'is_open'),
        Output('summary-option1', 'style'),
        Output('collapse-content2', 'is_open'),
        Output('summary-option2', 'style'),
        Output('collapse-content3', 'is_open'),
        Output('summary-option3', 'style')
    ],
    [
        Input('toggle-button1', 'n_clicks'),
        Input('toggle-button2', 'n_clicks'),
        Input('toggle-button3', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def combined_toggle(n1, n2, n3):
    def toggle_logic(n):
        is_open = n is not None and n % 2 == 1
        return (True, {"display": "none"}) if is_open else (False, {"display": "block"})
    
    return toggle_logic(n1) + toggle_logic(n2) + toggle_logic(n3)


@callback(
    [Output("collapse-input", "is_open"), Output("unfold-button", "children")],
    [Input("unfold-button", "n_clicks")],
    [dash.dependencies.State("collapse-input", "is_open")]
)
def toggle_collapse(n, is_open):
    if n:
        if is_open:
            return not is_open, "Input information +"
        else:
            return not is_open, "Input information -"
    return is_open, "Input information +"


@callback(
    [
        Output("compare-collapse1", "is_open"),
        Output("compare-collapse2", "is_open"),
        Output("compare-collapse3", "is_open"),
        Output("compare-collapse4", "is_open"),
        Output("compare-collapse5", "is_open"),
        Output("compare-button1", "children"),
        Output("compare-button2", "children"),
        Output("compare-button3", "children"),
        Output("compare-button4", "children"),
        Output("compare-button5", "children"),
    ],
    [
        Input("compare-button1", "n_clicks"),
        Input("compare-button2", "n_clicks"),
        Input("compare-button3", "n_clicks"),
        Input("compare-button4", "n_clicks"),
        Input("compare-button5", "n_clicks"),
    ],
    prevent_initial_call=True
)
def toggle_collapses(n1, n2, n3, n4, n5):
    # Determine visibility based on clicks
    is_open = [(n % 2 == 1) if n else False for n in [n1, n2, n3, n4, n5]]

    # Determine button text based on visibility
    labels = ["- Details" if open else "+ Details" for open in is_open]

    return is_open + labels



@callback(
    [Output('collapse-comparison-section', 'is_open'),
     Output('dropdown-icon', 'className')],
    [Input('comparison-section-button', 'n_clicks')],
    [State('collapse-comparison-section', 'is_open')]
)
def toggle_collapse(n, is_open):
    if n:
        if is_open:
            return not is_open, 'fas fa-chevron-down ml-2'  # Close and show the down icon
        else:
            return not is_open, 'fas fa-chevron-up ml-2'  # Open and show the up icon
    return is_open, 'fas fa-chevron-down ml-2'  # Default state

@callback(
    [
        Output("collapse-comparison-details-section", "is_open"),
        Output("comparison-details-section-button", "children")
    ],
    [Input("comparison-details-section-button", "n_clicks")],
    prevent_initial_call=True
)
def toggle_collapse(n):
    if n:
        is_open = n % 2 == 1  # Opens on odd number of clicks, closes on even number
        label = "Explore net worth changes by year -" if is_open else "Explore net worth changes by year +"
        return is_open, label
    return False, "Explore net worth changes by year +"



@callback(
    Output('compare-label', 'children'),
    Output('compare-label2', 'children'),
    Output('compare-label3', 'children'),
    Output('compare-label4', 'children'),
    Output('compare-label5', 'children'),

    [Input('current-year', 'value')]
)
def update_cows_label(current_year):
    return current_year, current_year+1, current_year+2, current_year+3, current_year+4


@callback(
    [Output('additional-cost-option1', 'children'),
     Output('additional-cost-option1-stored', 'data'),
     Output('option1-table-container', 'data')],
    [Input('hay-lbs-day', 'value'),
     Input('hay-per-ton', 'value'),
     Input('other-lbs-day', 'value'),
     Input('other-per-ton', 'value'),
     Input('hidden-time-table-store', 'data'),
     Input('herd-size', 'value')]
)
def update_additional_cost(hay_lbs_day, hay_per_ton, other_lbs_day, other_per_ton,
                           stored_data, herd_size):
    hay_cost_per_day = hay_lbs_day * (hay_per_ton / 2000)
    other_cost_per_day = other_lbs_day * (other_per_ton / 2000)
    
    additional_cost = hay_cost_per_day + other_cost_per_day

    # Convert stored data back to figure
    days_data = stored_data['data'][0]['cells']['values'][2]

    # M28, M29, M30 calculations
    M28 = days_data[0]
    M30 = days_data[-1]
    M29 = (M30 + M28) / 2

    M_values = [M28, M29, M30]

    # Q and R calculations
    Q_values = [additional_cost * val for val in M_values]
    R_values = [q_val * herd_size for q_val in Q_values]

    # Create DataFrame
    df = pd.DataFrame({
        "Add'l Feed": M_values,
        "Per Cow": Q_values,
        "Per Herd": R_values
    })

    return f"{additional_cost:.2f}", additional_cost, df.to_dict('records')



@callback(
    Output('option2-table-container', 'data'),
    Output('total-per-herd-option2', 'data'),
    [
        Input('distance-to-pasture', 'value'),
        Input('trucking-cost', 'value'),
        Input('trucks-needed-pairs', 'data'),
        Input('trucks-needed-cows', 'data'),
        Input('pasture-rent', 'value'),
        Input('days-rented-pasture', 'value'),
        Input('herd-size', 'value'),
        Input('total-other-costs', 'value'),
        Input('difference-sales', 'data'),
        Input('interest-borrowed-money', 'value')
    ]
)
def update_table(distance_to_pasture, trucking_cost, trucks_needed_pairs, trucks_needed_cows, pasture_rent, days_rented_pasture, herd_size, total_other_costs, difference_sales, interest_rate):
    # Calculations
    trucking_pairs_to_pasture_per_herd = distance_to_pasture * trucking_cost * trucks_needed_pairs
    trucking_pairs_to_pasture_per_cow = trucking_pairs_to_pasture_per_herd / herd_size

    trucking_cows_to_home_per_herd = distance_to_pasture * trucking_cost * trucks_needed_cows
    trucking_cows_to_home_per_cow = trucking_cows_to_home_per_herd / herd_size

    pasture_rent_per_herd = (pasture_rent / 30) * days_rented_pasture * herd_size
    pasture_rent_per_cow = pasture_rent_per_herd / herd_size

    other_costs_per_herd = total_other_costs
    other_costs_per_cow = other_costs_per_herd / herd_size

    lost_revenues_per_herd = difference_sales
    lost_revenues_per_cow = lost_revenues_per_herd / herd_size

    interest_per_herd = (trucking_pairs_to_pasture_per_herd + trucking_cows_to_home_per_herd + pasture_rent_per_herd + other_costs_per_herd) * (((interest_rate/100) / 360) * days_rented_pasture)
    interest_per_cow = interest_per_herd / herd_size

    total_per_herd = trucking_pairs_to_pasture_per_herd + trucking_cows_to_home_per_herd + pasture_rent_per_herd + other_costs_per_herd + lost_revenues_per_herd + interest_per_herd
    total_per_cow = total_per_herd / herd_size

    per_cow = [trucking_pairs_to_pasture_per_cow, trucking_cows_to_home_per_cow, pasture_rent_per_cow, other_costs_per_cow, lost_revenues_per_cow, interest_per_cow, total_per_cow]
    per_herd = [trucking_pairs_to_pasture_per_herd, trucking_cows_to_home_per_herd, pasture_rent_per_herd, other_costs_per_herd, lost_revenues_per_herd, interest_per_herd, total_per_herd]
    
    df = pd.DataFrame({
        '': ['Trucking Pairs to Pasture', 'Trucking Cows to Home', 'Pasture Rent', 'Other Costs', 'Lost Revenues', 'Interest', 'Total'],
        'Per Cow': per_cow,
        'Per Herd': per_herd
    })


    return df.to_dict('records'), total_per_herd


@callback(
    Output('option3-table-container', 'data'),
    [
        Input('store-difference', 'data'),
        Input('reduced-operating-costs-year1', 'value'),
        Input('selling-costs', 'value'),
        Input('store-cow-sales', 'data'),
        Input('hidden-time-table-store', 'data'),
        Input('interest-invested-money', 'value'),
        Input('herd-size', 'value'),
        Input('cows-culled', 'value'),
        Input('current-value-cow', 'value'),
        Input('store-interest-income-year1', 'data'),
        Input('store-interest-income-year2', 'data'),
        Input('store-interest-income-year3', 'data'),
        Input('store-expected-calf-sales-year2', 'data'),
        Input('store-expected-calf-sales-year3', 'data'),
        Input('operating-costs-year2', 'value'),
        Input('operating-costs-years3-5', 'value'),
        Input('annual-cow-costs', 'value'),
        Input('cost-replacement-animals', 'value')
    ]
)
def update_table(store_difference, reduced_operating_costs_year1, selling_costs, store_cow_sales, stored_data, 
                 interest_invested_money, herd_size, cows_culled, current_value_cow, 
                 store_interest_income_year1, store_interest_income_year2, store_interest_income_year3, 
                 store_expected_calf_sales_year2, store_expected_calf_sales_year3, 
                 operating_costs_year2, operating_costs_year3_5, annual_cow_costs, cost_replacement_animals):

    days_data = stored_data['data'][0]['cells']['values'][2]
    days_interest = days_data[0]

    # Formulas for Additional Costs Per Herd
    reduced_calf_sales_herd = store_difference
    reduced_op_costs_this_year_herd = reduced_operating_costs_year1 * herd_size
    additional_costs_selling_cows_herd = selling_costs * herd_size
    interest_cow_sales_herd = -1 * (store_cow_sales * days_interest * ((interest_invested_money/100) / 360))
    total_year1_herd = sum([reduced_calf_sales_herd, reduced_op_costs_this_year_herd, additional_costs_selling_cows_herd, interest_cow_sales_herd])
    revenues_from_cow_sales_herd = -1 * ((herd_size - cows_culled) * current_value_cow)
    interest_income_years_2_3_herd = -1 * (store_interest_income_year1 + store_interest_income_year2 + store_interest_income_year3)
    expected_calf_sales_years_2_3_herd = store_expected_calf_sales_year2 + store_expected_calf_sales_year3
    reduced_op_expenses_years_2_3_herd = -1 * ((2 * (herd_size * annual_cow_costs)) - (operating_costs_year2 + operating_costs_year3_5))
    replacement_cows_herd = cost_replacement_animals * herd_size
    total_years_2_3_herd = sum([revenues_from_cow_sales_herd, interest_income_years_2_3_herd, expected_calf_sales_years_2_3_herd, reduced_op_expenses_years_2_3_herd, replacement_cows_herd])

    # Formulas for Additional Costs Per Cow
    reduced_calf_sales_cow = reduced_calf_sales_herd / herd_size
    reduced_op_costs_this_year_cow = reduced_op_costs_this_year_herd / herd_size
    additional_costs_selling_cows_cow = additional_costs_selling_cows_herd / herd_size
    interest_cow_sales_cow = interest_cow_sales_herd / herd_size
    total_year1_cow = total_year1_herd / herd_size
    revenues_from_cow_sales_cow = revenues_from_cow_sales_herd / herd_size
    interest_income_years_2_3_cow = interest_income_years_2_3_herd / herd_size
    expected_calf_sales_years_2_3_cow = expected_calf_sales_years_2_3_herd / herd_size
    reduced_op_expenses_years_2_3_cow = reduced_op_expenses_years_2_3_herd / herd_size
    replacement_cows_cow = replacement_cows_herd / herd_size
    total_years_2_3_cow = total_years_2_3_herd / herd_size

    # Construct the table data
    data = [
        ["Reduced Calf Sales This Year", reduced_calf_sales_cow, reduced_calf_sales_herd],
        ["Reduced Operating Costs, This Year", reduced_op_costs_this_year_cow, reduced_op_costs_this_year_herd],
        ["Additional Costs for Selling Cows", additional_costs_selling_cows_cow, additional_costs_selling_cows_herd],
        ["Interest on Cow Sales Revenues", interest_cow_sales_cow, interest_cow_sales_herd],
        ["Total, Year 1", total_year1_cow, total_year1_herd],
        ["Revenues from Cow Sales", revenues_from_cow_sales_cow, revenues_from_cow_sales_herd],
        ["Interest Income, Years 2+3", interest_income_years_2_3_cow, interest_income_years_2_3_herd],
        ["Expected Calf Sales, Years 2+3", expected_calf_sales_years_2_3_cow, expected_calf_sales_years_2_3_herd],
        ["Reduced Operating Expenses, Yrs 2+3", reduced_op_expenses_years_2_3_cow, reduced_op_expenses_years_2_3_herd],
        ["Replacement Cows", replacement_cows_cow, replacement_cows_herd],
        ["Total, Years 2 & 3", total_years_2_3_cow, total_years_2_3_herd],
        ["Total for 3 Years", total_year1_cow + total_years_2_3_cow, total_year1_herd + total_years_2_3_herd]
    ]

    df = pd.DataFrame(data, columns=["", "Additional Costs Per Cow", "Additional Costs Per Herd"])
    
    return df.to_dict('records')





# Hidden tables

@callback(
    [Output('drought-table-container', 'figure'),
     Output('hidden-time-table-store', 'data'),
     Output('drought-days', 'children'),
     Output('drought-months', 'children'),
     Output('drought-days-store', 'data'),
     Output('drought-months-store', 'data'),
     Output('drought-days-store2', 'data'),
     Output('drought-months-store2', 'data'),
     Output('drought-days-store3', 'data'),
     Output('drought-months-store3', 'data'),
     Output('drought-days-store4', 'data'),
     Output('drought-months-store4', 'data')],
    [Input('current-month', 'value'),
     Input('current-year', 'value'),
     Input('drought-end-month', 'value'),
     Input('drought-end-year', 'value')]
)
def update_table(current_month, current_year, drought_end_month, drought_end_year):

    V = []
    W = []
    X = []

    # Row 1 calculations
    V.append(current_year)
    W.append(12 - current_month)
    X.append(W[0] * 30)

    # Rows 2 to 5 calculations
    for i in range(4):
        next_year = V[-1] + 1
        if drought_end_year > next_year:
            V.append(next_year)
        else:
            V.append(drought_end_year if V[-1] != drought_end_year else 0)
        
        if V[-1] < drought_end_year:
            W.append(0 if V[-1] < 2000 else 12)
        else:
            W.append(drought_end_month)
        
        X.append(W[-1] * 30)

    # Last row calculations
    V.append("")
    W.append(sum(W))
    X.append(sum(X))

    table = go.Figure(go.Table(
        header=dict(values=['Year', 'Months', 'Days']),
        cells=dict(values=[V, W, X])
    ))

    return table, table.to_dict(), X[-1],  W[-1], X[1],  W[1], X[2],  W[2], X[3],  W[3], X[4],  W[4]







## Calves sold and Trucks
@callback(
    [
        Output('actual-calves-sold', 'data'),
        Output('actual-selling-weight', 'data'),
        Output('expected-calf-sales', 'data'),
        Output('actual-calf-sales', 'data'),
        Output('difference-sales', 'data'),
        Output('pairs-per-truck', 'data'),
        Output('cows-per-truck', 'data'),
        Output('trucks-needed-pairs', 'data'),
        Output('trucks-needed-cows', 'data'),
        Output('calves-to-sell', 'data'),
        Output('truck-table-container', 'figure')
    ],
    [
        Input('calf-death-loss', 'value'),
        Input('weight-at-weaning', 'value'),
        Input('weaning-weight-adjustment', 'value'),
        Input('price-weaning-year1', 'value'),
        Input('avg-cow-weight', 'value'),
        Input('current-weight-calves', 'value'),
        Input('herd-size', 'value'),
        Input('percent-calves-sold', 'value')
    ]
)
def update_values(calf_death_loss, weight_at_weaning, weaning_weight_adjustment, price_weaning_year1, avg_cow_weight, current_weight_calves, herd_size, percent_calves_sold):
    
    calves_to_sell = herd_size * (percent_calves_sold/100)
    actual_calves_sold = calves_to_sell - calf_death_loss
    actual_selling_weight = weight_at_weaning * (1 + (weaning_weight_adjustment/100))
    expected_calf_sales = calves_to_sell * weight_at_weaning * price_weaning_year1
    actual_calf_sales = actual_calves_sold * actual_selling_weight * price_weaning_year1
    difference_sales = expected_calf_sales - actual_calf_sales
    pairs_per_truck = math.ceil(40000 / (avg_cow_weight + current_weight_calves))
    cows_per_truck = math.ceil(40000 / avg_cow_weight)
    trucks_needed_pairs = math.ceil(herd_size / pairs_per_truck)
    trucks_needed_cows = math.ceil(herd_size / cows_per_truck)


    # Create table
    table = go.Figure(data=[go.Table(
        header=dict(values=['Parameter', 'Value']),
        cells=dict(values=[
            ['Calves to Sell', 'Actual Calves Sold', 'Actual Selling Weight', 'Expected Calf Sales', 'Actual Calf Sales', 'Difference in Sales', 'Pairs per Truck', 'Cows per Truck', 'Trucks Needed for Pairs', 'Trucks Needed for Cows'],
            [calves_to_sell, actual_calves_sold, actual_selling_weight, expected_calf_sales, actual_calf_sales, difference_sales, pairs_per_truck, cows_per_truck, trucks_needed_pairs, trucks_needed_cows]
        ])
    )])

    return actual_calves_sold, actual_selling_weight, expected_calf_sales, actual_calf_sales, difference_sales, pairs_per_truck, cows_per_truck, trucks_needed_pairs, trucks_needed_cows, calves_to_sell, table

## Hidden 3
@callback(
        Output('store-expected-calf-sales-current-year', 'data'),
        Output('store-actual-calf-sales', 'data'),
        Output('store-difference', 'data'),
        Output('store-expected-calf-sales-year2', 'data'),
        Output('store-expected-calf-sales-year3', 'data'),
        Output('store-cow-sales', 'data'),
        Output('store-interest-income-year1', 'data'),
        Output('store-interest-income-year2', 'data'),
        Output('store-interest-income-year3', 'data'),
        Output('hidden3-table-container', 'figure'),
    [
        Input('herd-size', 'value'),
        Input('percent-calves-sold', 'value'),
        Input('weight-at-weaning', 'value'),
        Input('price-weaning-year1', 'value'),
        Input('avg-weaning-percentage', 'value'),
        Input('current-weight-calves', 'value'),
        Input('current-price-per-lb', 'value'),
        Input('price-weaning-year2', 'value'),
        Input('price-weaning-years3-5', 'value'),
        Input('current-value-cow', 'value'),
        Input('hidden-time-table-store', 'data'),
        Input('interest-invested-money', 'value')
    ]
)
def update_table(herd_size, percent_calves_sold, weight_at_weaning, price_weaning_year1, avg_weaning_percentage,
                 current_weight_calves, current_price_per_lb, price_weaning_year2, price_weaning_years3_5,
                 current_value_cow, stored_data, interest_invested_money):

    days_data = stored_data['data'][0]['cells']['values'][2]
    X17 = days_data[0]

    expected_calf_sales_current_year = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year1
    actual_calf_sales = (herd_size * (avg_weaning_percentage/100)) * current_weight_calves * current_price_per_lb
    difference = expected_calf_sales_current_year - actual_calf_sales

    expected_calf_sales_year2 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2
    expected_calf_sales_year3 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    cow_sales = herd_size * current_value_cow

    initial_money_invested = cow_sales
    interest_income_year1 = initial_money_invested * X17 * ((interest_invested_money/100) / 360)
    interest_income_year2 = (initial_money_invested + interest_income_year1) * (interest_invested_money/100)
    interest_income_year3 = (initial_money_invested + interest_income_year1 + interest_income_year2) * (interest_invested_money/100)

    # Create the table
    table = go.Figure(data=[go.Table(
        header=dict(values=['Parameter', 'Value']),
        cells=dict(values=[
            ['Expected Calf Sales, Current Year', 'Actual Calf Sales', 'Difference', 'Expected Calf Sales, Year 2',
             'Expected Calf Sales, Year 3', 'Cow Sales', 'Initial Money Invested', 'Interest Income, Year 1',
             'Interest Income, Year 2', 'Interest Income, Year 3'],
            [expected_calf_sales_current_year, actual_calf_sales, difference, expected_calf_sales_year2,
             expected_calf_sales_year3, cow_sales, initial_money_invested, interest_income_year1,
             interest_income_year2, interest_income_year3]
        ])
    )])

    return expected_calf_sales_current_year, actual_calf_sales, difference, expected_calf_sales_year2, expected_calf_sales_year3, cow_sales, interest_income_year1, interest_income_year2, interest_income_year3, table 


@callback(
    Output('output-comparison-table', 'figure'),
    Output('output-comparison-table2', 'figure'),
    [
        Input('reduced-operating-costs-year1', 'value'),
        Input('drought-end-year', 'value'),
        Input('current-year', 'value'),
        Input('hidden-time-table-store', 'data'),
        Input('herd-size', 'value'),
        Input('current-value-cow', 'value'),
        Input('annual-cow-costs', 'value'),
        Input('percent-calves-sold', 'value'),
        Input('weight-at-weaning', 'value'),
        Input('price-weaning-year1', 'value'),
        Input('price-weaning-year2', 'value'),
        Input('current-weight-calves', 'value'),
        Input('current-price-per-lb', 'value'),
        Input('additional-cost-option1-stored', 'data'),
        Input('calf-death-loss', 'value'),
        Input('weaning-weight-adjustment', 'value'),
        Input('total-per-herd-option2', 'data'),
        Input('store-actual-calf-sales', 'data'),
        Input('tax-basis-cow', 'value'),
        Input('capital-gains-tax-rate', 'value'),
        Input('cost-replacement-animals', 'value'),
        Input('drought-months-store', 'data'), 
        Input('drought-days-store', 'data'), 
        Input('pasture-rent', 'value'),
        Input('operating-costs-year2', 'value'),
        Input('interest-borrowed-money', 'value'),
        Input('interest-invested-money', 'value')

    ]
)
def update_table(reduced_operating_costs_year1, drought_end_year, current_year, stored_data, herd_size, current_value_cow, 
                 annual_cow_costs, percent_calves_sold, weight_at_weaning, price_weaning_year1, price_weaning_year2,
                 current_weight_calves, current_price_per_lb, additional_cost_option1,calf_death_loss,weaning_weight_adjustment,
                 total_per_herd_option2, option3_actual_calf_sales,tax_basis_cow,capital_gains_tax_rate,cost_replacement_animals,
                 drought_months_store,drought_days_store, pasture_rent, operating_costs_year2,interest_borrowed_money,
                 interest_invested_money):

    days_data = stored_data['data'][0]['cells']['values'][2]
    X17 = days_data[0]

    # Calculations
    ## First table
    cows_calc = herd_size * current_value_cow
    calves_calc = (percent_calves_sold/100) * current_weight_calves * current_price_per_lb
    cash_calc = -(herd_size * annual_cow_costs - herd_size * reduced_operating_costs_year1)
    total_64_66 = cows_calc + calves_calc + cash_calc

    cows_calc_row = [cows_calc, cows_calc, cows_calc, cows_calc, cows_calc]
    calves_calc_row = [calves_calc, calves_calc, calves_calc, calves_calc, calves_calc]
    cash_calc_row = [cash_calc, cash_calc, cash_calc, cash_calc, cash_calc]
    total_64_66_row = [c + v + k for c, v, k in zip(cows_calc_row, calves_calc_row, cash_calc_row)]

    revenues_from_calves_colE = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year1
    revenues_from_calves_colO = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_year1 if current_year < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year1
    revenues_from_calves_row = [revenues_from_calves_colE, revenues_from_calves_colE, revenues_from_calves_colO, option3_actual_calf_sales, option3_actual_calf_sales]

    operating_costs = -herd_size * annual_cow_costs
    operating_costs_adj = -((herd_size * annual_cow_costs) + (X17 * additional_cost_option1 * herd_size))
    operating_costs_row = [operating_costs, operating_costs_adj, -((herd_size * annual_cow_costs) + total_per_herd_option2), -herd_size * (annual_cow_costs - reduced_operating_costs_year1), -herd_size * (annual_cow_costs - reduced_operating_costs_year1)]
    
    profits_row = [c + v for c, v in zip(revenues_from_calves_row, operating_costs_row)]
    taxes_row = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row]
    taxes_after_income_row = [c - v for c, v in zip(profits_row, taxes_row)]
    capital_sales_row = [0,0,0,cows_calc,cows_calc]
    capital_gains_row = [0,0,0,0,(herd_size * (current_value_cow - tax_basis_cow)) * (capital_gains_tax_rate/100)]

    ending_net_worth_cows_row = [c - v for c, v in zip(cows_calc_row, capital_sales_row)]
    ending_net_worth_cash_row = [c + v - k for c, v, k in zip(taxes_after_income_row, capital_sales_row,capital_gains_row)]
    total_78_79_row = [c + v for c, v in zip(ending_net_worth_cows_row, ending_net_worth_cash_row)]

    ## Second table

    # Table Data
    rows1 = [
        "Cows", "Calves", "Cash", "Total", 
        current_year, "Revenues from Calves", 
        "Operating Costs (typical + adjustments)", "Profits", 
        "Taxes (SE, US Income, CO Income)", "After Tax Income", 
        "Capital Sales - Cow Sales", "Capital Gains", 
        "Ending Net Worth - Cows", "Ending Net Worth - Cash", "Total"
    ]
    data_values1 = [
        cows_calc_row,
        calves_calc_row,
        cash_calc_row,
        total_64_66_row,
        ["", "", "", "", ""],
        revenues_from_calves_row,
        operating_costs_row,
        profits_row,
        taxes_row,
        taxes_after_income_row,
        capital_sales_row,
        capital_gains_row,
        ending_net_worth_cows_row,
        ending_net_worth_cash_row,
        total_78_79_row
    ]

    # Combine row headers and data values
    table_data1 = [[row] + data_val for row, data_val in zip(rows1, data_values1)]

    # Create table figure
    fig1 = go.Figure(data=[go.Table(
        header=dict(values=["E", "M", "N", "O", "P", "Q"]),
        cells=dict(values=list(map(list, zip(*table_data1)))) # transpose the table data
    )])

    # Second table

    revenues_from_calves_colE_repl = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2
    revenues_from_calves_colO_repl = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_year2 if current_year+1 < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2
    revenues_from_calves_colQ_repl = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2 if current_year > drought_end_year else 0

    revenues_from_calves_row_repl = [revenues_from_calves_colE_repl, revenues_from_calves_colE_repl, revenues_from_calves_colO_repl, revenues_from_calves_colQ_repl, 0]


    operating_costs_repl = -herd_size * annual_cow_costs
    operating_costs_adj_N_repl = -((herd_size * annual_cow_costs) + (drought_days_store * additional_cost_option1 * herd_size)) if drought_days_store > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_O_repl = -((herd_size * annual_cow_costs) + (drought_months_store * pasture_rent * herd_size)) if drought_days_store > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_Q_repl = -operating_costs_year2 if revenues_from_calves_row_repl[-2]==0 else -(herd_size * annual_cow_costs)

    operating_costs_row_repl = [operating_costs_repl, operating_costs_adj_N_repl, operating_costs_adj_O_repl, operating_costs_adj_Q_repl ,-operating_costs_year2]

    interest_income_expenses = [(c*(interest_invested_money/100) if c>0 else c*(interest_borrowed_money/100)) for c in ending_net_worth_cash_row]
    
    profits_row_repl = [c + v + k for c, v, k in zip(revenues_from_calves_row_repl, operating_costs_row_repl,interest_income_expenses)]
    
    
    taxes_row_repl = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row_repl]
    taxes_after_income_row_repl = [c - v for c, v in zip(profits_row_repl, taxes_row_repl)]
    purchase_females= herd_size*cost_replacement_animals if current_year+1==drought_end_year else 0 
    purchase_females_row = [0,0,0,purchase_females ,0]

    ending_net_worth_cows_1to3 = herd_size*cost_replacement_animals if purchase_females > 0 else cows_calc+0
    ending_net_worth_cows_4to5 = [c + v for c, v in zip(ending_net_worth_cows_row[-2:], purchase_females_row[-2:])]


    ending_net_worth_cows_row_final = [ending_net_worth_cows_1to3,ending_net_worth_cows_1to3,ending_net_worth_cows_1to3,
                                       ending_net_worth_cows_4to5[0],ending_net_worth_cows_4to5[1]]
    ending_net_worth_cash_row_final = [c + v for c, v in zip(ending_net_worth_cash_row,taxes_after_income_row_repl)]
    total_78_79_row_final = [c + v for c, v in zip(ending_net_worth_cows_row_final, ending_net_worth_cash_row_final)]

    rows2 = [
        (current_year+1), "Revenues from Calves", 
        "Operating expenses","Interest Income/Expenses", "Profits", 
        "Taxes (SE, US Income, CO Income)", "After Tax Income", 
        "Purchase Replacement Females", 
        "Ending Net Worth - Cows", "Ending Net Worth - Cash", "Total"
    ]
    data_values2 = [
        ["", "", "", "", ""],
        revenues_from_calves_row_repl,
        operating_costs_row_repl,
        interest_income_expenses,
        profits_row_repl,
        taxes_row_repl,
        taxes_after_income_row_repl,
        purchase_females_row,
        ending_net_worth_cows_row_final,
        ending_net_worth_cash_row_final,
        total_78_79_row_final
    ]

    # Combine row headers and data values
    table_data2 = [[row] + data_val for row, data_val in zip(rows2, data_values2)]

    # Create table figure
    fig2 = go.Figure(data=[go.Table(
        header=dict(values=["E", "M", "N", "O", "P", "Q"]),
        cells=dict(values=list(map(list, zip(*table_data2)))) # transpose the table data
    )])



    return fig1, fig2


@callback(
    Output('output-comparison-table-currentsummary-data', 'data'),
    Output('output-comparison-table-data', 'data'),
    Output('output-comparison-table-summary-data', 'data'),

    Output('output-comparison-table2-data', 'data'),
    Output('output-comparison-table2-summary-data', 'data'),

    Output('output-comparison-table3-data', 'data'),
    Output('output-comparison-table3-summary-data', 'data'),

    Output('output-comparison-table4-data', 'data'),
    Output('output-comparison-table4-summary-data', 'data'),

    Output('output-comparison-table5-data', 'data'),
    Output('output-comparison-table5-summary-data', 'data'),

    Output('output-comparison-tablesummary-data', 'data'),
    Output('output-comparison-tablesummary-data-store', 'data'),

    [
        Input('reduced-operating-costs-year1', 'value'),
        Input('drought-end-year', 'value'),
        Input('current-year', 'value'),
        Input('hidden-time-table-store', 'data'),
        Input('herd-size', 'value'),
        Input('current-value-cow', 'value'),
        Input('annual-cow-costs', 'value'),
        Input('percent-calves-sold', 'value'),
        Input('weight-at-weaning', 'value'),
        Input('price-weaning-year1', 'value'),
        Input('price-weaning-year2', 'value'),
        Input('price-weaning-years3-5', 'value'),
        Input('current-weight-calves', 'value'),
        Input('current-price-per-lb', 'value'),
        Input('additional-cost-option1-stored', 'data'),
        Input('calf-death-loss', 'value'),
        Input('weaning-weight-adjustment', 'value'),
        Input('total-per-herd-option2', 'data'),
        Input('store-actual-calf-sales', 'data'),
        Input('tax-basis-cow', 'value'),
        Input('capital-gains-tax-rate', 'value'),
        Input('cost-replacement-animals', 'value'),
        Input('drought-days-store', 'data'),
        Input('drought-months-store', 'data'), 
        Input('drought-days-store2', 'data'),
        Input('drought-months-store2', 'data'),
        Input('drought-days-store3', 'data'),
        Input('drought-months-store3', 'data'),
        Input('drought-days-store4', 'data'),
        Input('drought-months-store4', 'data'),
        Input('pasture-rent', 'value'),
        Input('operating-costs-year2', 'value'),
        Input('interest-borrowed-money', 'value'),
        Input('interest-invested-money', 'value')
    ]
)
def update_table(reduced_operating_costs_year1, drought_end_year, current_year, stored_data, herd_size, current_value_cow, 
                 annual_cow_costs, percent_calves_sold, weight_at_weaning, price_weaning_year1, price_weaning_year2,price_weaning_years3_5,
                 current_weight_calves, current_price_per_lb, additional_cost_option1,calf_death_loss,weaning_weight_adjustment,
                 total_per_herd_option2, option3_actual_calf_sales,tax_basis_cow,capital_gains_tax_rate,cost_replacement_animals,
                 drought_days_store, drought_months_store, drought_days_store2, drought_months_store2, drought_days_store3, drought_months_store3, drought_days_store4, drought_months_store4,
                 pasture_rent, operating_costs_year2,interest_borrowed_money,
                 interest_invested_money):

    days_data = stored_data['data'][0]['cells']['values'][2]
    X17 = days_data[0]

    # Calculations
    ## First table
    cows_calc = herd_size * current_value_cow
    calves_calc = (percent_calves_sold/100) * current_weight_calves * current_price_per_lb
    cash_calc = -(herd_size * annual_cow_costs - herd_size * reduced_operating_costs_year1)
    total_64_66 = cows_calc + calves_calc + cash_calc

    cows_calc_row = [cows_calc, cows_calc, cows_calc, cows_calc, cows_calc]
    calves_calc_row = [calves_calc, calves_calc, calves_calc, calves_calc, calves_calc]
    cash_calc_row = [cash_calc, cash_calc, cash_calc, cash_calc, cash_calc]
    total_64_66_row = [c + v + k for c, v, k in zip(cows_calc_row, calves_calc_row, cash_calc_row)]

    revenues_from_calves_colE = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year1
    revenues_from_calves_colO = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_year1 if current_year < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year1
    revenues_from_calves_row = [revenues_from_calves_colE, revenues_from_calves_colE, revenues_from_calves_colO, option3_actual_calf_sales, option3_actual_calf_sales]

    operating_costs = -herd_size * annual_cow_costs
    operating_costs_adj = -((herd_size * annual_cow_costs) + (X17 * additional_cost_option1 * herd_size))
    operating_costs_row = [operating_costs, operating_costs_adj, -((herd_size * annual_cow_costs) + total_per_herd_option2), -herd_size * (annual_cow_costs - reduced_operating_costs_year1), -herd_size * (annual_cow_costs - reduced_operating_costs_year1)]
    
    profits_row = [c + v for c, v in zip(revenues_from_calves_row, operating_costs_row)]
    taxes_row = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row]
    taxes_after_income_row = [c - v for c, v in zip(profits_row, taxes_row)]
    capital_sales_row = [0,0,0,cows_calc,cows_calc]
    capital_gains_row = [0,0,0,0,(herd_size * (current_value_cow - tax_basis_cow)) * (capital_gains_tax_rate/100)]

    ending_net_worth_cows_row = [c - v for c, v in zip(cows_calc_row, capital_sales_row)]
    ending_net_worth_cash_row = [c + v - k for c, v, k in zip(taxes_after_income_row, capital_sales_row,capital_gains_row)]
    total_78_79_row = [c + v for c, v in zip(ending_net_worth_cows_row, ending_net_worth_cash_row)]

    data_values1_current_summary = [
        ["Cows"] + cows_calc_row,
        ["Calves"] + calves_calc_row,
        ["Cash"] + cash_calc_row,
        ["Total ($)"] + total_64_66_row,
    ]

    df1_current_summary = pd.DataFrame(data_values1_current_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])


    data_values1 = [
        ["Revenues from Calves"] + revenues_from_calves_row,
        ["Operating Costs (typical + adjustments)"] + operating_costs_row,
        ["Profits"] + profits_row,
        ["Taxes (SE, US Income, CO Income)"] + taxes_row,
        ["After Tax Income"] + taxes_after_income_row,
        ["Capital Sales - Cow Sales"] + capital_sales_row,
        ["Capital Gains"] + capital_gains_row,
    ]

    data_values1_summary = [
        ["Ending Net Worth - Cows"] + ending_net_worth_cows_row,
        ["Ending Net Worth - Cash"] + ending_net_worth_cash_row,
        ["Total ($)"] + total_78_79_row
    ]

    # Combine row headers and data values
    df1 = pd.DataFrame(data_values1, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])
    df1_summary = pd.DataFrame(data_values1_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])

    ## Second table

    revenues_from_calves_colE_repl = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2
    revenues_from_calves_colO_repl = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_year2 if current_year+1 < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2
    revenues_from_calves_colQ_repl = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_year2 if current_year+1 > drought_end_year else 0

    revenues_from_calves_row_repl = [revenues_from_calves_colE_repl, revenues_from_calves_colE_repl, revenues_from_calves_colO_repl, revenues_from_calves_colQ_repl, 0]

    operating_costs_repl = -herd_size * annual_cow_costs
    operating_costs_adj_N_repl = -((herd_size * annual_cow_costs) + (drought_days_store * additional_cost_option1 * herd_size)) if drought_days_store > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_O_repl = -((herd_size * annual_cow_costs) + (drought_months_store * pasture_rent * herd_size)) if drought_days_store > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_Q_repl = -operating_costs_year2 if revenues_from_calves_row_repl[-2]==0 else -(herd_size * annual_cow_costs)

    operating_costs_row_repl = [operating_costs_repl, operating_costs_adj_N_repl, operating_costs_adj_O_repl, operating_costs_adj_Q_repl ,-operating_costs_year2]

    interest_income_expenses = [(c*(interest_invested_money/100) if c>0 else c*(interest_borrowed_money/100)) for c in ending_net_worth_cash_row]
    
    profits_row_repl = [c + v + k for c, v, k in zip(revenues_from_calves_row_repl, operating_costs_row_repl,interest_income_expenses)]
    
    taxes_row_repl = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row_repl]
    taxes_after_income_row_repl = [c - v for c, v in zip(profits_row_repl, taxes_row_repl)]
    purchase_females= herd_size*cost_replacement_animals if current_year+1==drought_end_year else 0 
    purchase_females_row = [0,0,0,purchase_females ,0]

    ending_net_worth_cows_1to3 = herd_size*cost_replacement_animals if purchase_females > 0 else cows_calc+0
    ending_net_worth_cows_4to5 = [c + v for c, v in zip(ending_net_worth_cows_row[-2:], purchase_females_row[-2:])]
    ending_net_worth_cows_row_final = [ending_net_worth_cows_1to3,ending_net_worth_cows_1to3,ending_net_worth_cows_1to3,
                                       ending_net_worth_cows_4to5[0],ending_net_worth_cows_4to5[1]]
    ending_net_worth_cash_row_final = [c + v for c, v in zip(ending_net_worth_cash_row,taxes_after_income_row_repl)]
    total_78_79_row_final = [c + v for c, v in zip(ending_net_worth_cows_row_final, ending_net_worth_cash_row_final)]

    data_values2 = [
        ["Revenues from Calves"] + revenues_from_calves_row_repl,
        ["Operating expenses"] + operating_costs_row_repl,
        ["Interest Income/Expenses"] + interest_income_expenses,
        ["Profits"] + profits_row_repl,
        ["Taxes (SE, US Income, CO Income)"] + taxes_row_repl,
        ["After Tax Income"] + taxes_after_income_row_repl,
        ["Purchase Replacement Females"] + purchase_females_row,
    ]

    data_values2_summary = [
        ["Ending Net Worth - Cows"] + ending_net_worth_cows_row_final,
        ["Ending Net Worth - Cash"] + ending_net_worth_cash_row_final,
        ["Total ($)"] + total_78_79_row_final
    ]

    # Combine row headers and data values
    df2 = pd.DataFrame(data_values2, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])
    df2_summary = pd.DataFrame(data_values2_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])


    ## third table

    revenues_from_calves_colE_tbl3 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    revenues_from_calves_colO_tbl3 = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_years3_5 if current_year+2 < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    revenues_from_calves_colQ_tbl3 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5 if current_year+2 > drought_end_year else 0

    revenues_from_calves_row_tbl3 = [revenues_from_calves_colE_tbl3, revenues_from_calves_colE_tbl3, revenues_from_calves_colO_tbl3, revenues_from_calves_colQ_tbl3, 0]

    operating_costs_tbl3 = -herd_size * annual_cow_costs
    operating_costs_adj_N_tbl3 = -((herd_size * annual_cow_costs) + (drought_days_store2 * additional_cost_option1 * herd_size)) if drought_days_store2 > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_O_tbl3 = -((herd_size * annual_cow_costs) + (drought_months_store2 * pasture_rent * herd_size)) if drought_days_store2 > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_Q_tbl3 = -operating_costs_year2 if revenues_from_calves_row_tbl3[-2]==0 else -(herd_size * annual_cow_costs)

    operating_costs_row_tbl3 = [operating_costs_tbl3, operating_costs_adj_N_tbl3, operating_costs_adj_O_tbl3, operating_costs_adj_Q_tbl3 ,-operating_costs_year2]

    interest_income_expenses_row_tbl3 = [(c*(interest_invested_money/100) if c>0 else c*(interest_borrowed_money/100)) for c in ending_net_worth_cash_row_final]
    
    profits_row_tbl3 = [c + v + k for c, v, k in zip(revenues_from_calves_row_tbl3, operating_costs_row_tbl3,interest_income_expenses_row_tbl3)]
    
    taxes_row_tbl3 = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row_tbl3]
    taxes_after_income_row_tbl3 = [c - v for c, v in zip(profits_row_tbl3, taxes_row_tbl3)]
    purchase_females_tbl3= herd_size*cost_replacement_animals if current_year+2==drought_end_year else 0 
    purchase_females_row_tbl3 = [0,0,0,purchase_females_tbl3 ,0]

    ending_net_worth_cows_1to3_tbl3 = herd_size*cost_replacement_animals if purchase_females_tbl3 > 0 else ending_net_worth_cows_row_final[0]+purchase_females_row_tbl3[-2]
    ending_net_worth_cows_4to5_tbl3 = [c + v for c, v in zip(ending_net_worth_cows_row_final[-2:], purchase_females_row_tbl3[-2:])]
    ending_net_worth_cows_row_tbl3_final = [ending_net_worth_cows_1to3_tbl3,ending_net_worth_cows_1to3_tbl3,ending_net_worth_cows_1to3_tbl3,
                                       ending_net_worth_cows_4to5_tbl3[0],ending_net_worth_cows_4to5_tbl3[1]]
    ending_net_worth_cash_row_tbl3_final = [c + v - k for c, v, k in zip(ending_net_worth_cash_row_final,taxes_after_income_row_tbl3, purchase_females_row_tbl3)]
    total_78_79_row_tbl3_final = [c + v for c, v in zip(ending_net_worth_cows_row_tbl3_final, ending_net_worth_cash_row_tbl3_final)]

    data_values3 = [
        ["Revenues from Calves"] + revenues_from_calves_row_tbl3,
        ["Operating expenses"] + operating_costs_row_tbl3,
        ["Interest Income/Expenses"] + interest_income_expenses_row_tbl3,
        ["Profits"] + profits_row_tbl3,
        ["Taxes (SE, US Income, CO Income)"] + taxes_row_tbl3,
        ["After Tax Income"] + taxes_after_income_row_tbl3,
        ["Purchase replacement Females"] + purchase_females_row_tbl3,
    ]

    data_values3_summary = [
        ["Ending Net Worth - Cows"] + ending_net_worth_cows_row_tbl3_final,
        ["Ending Net Worth - Cash"] + ending_net_worth_cash_row_tbl3_final,
        ["Total ($)"] + total_78_79_row_tbl3_final
    ]

    # Combine row headers and data values
    df3 = pd.DataFrame(data_values3, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])
    df3_summary = pd.DataFrame(data_values3_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])

    ## fourth table

    revenues_from_calves_colE_tbl4 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    revenues_from_calves_colO_tbl4 = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_years3_5 if current_year+3 < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    revenues_from_calves_colQ_tbl4 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5 if current_year+3 > drought_end_year else 0

    revenues_from_calves_row_tbl4 = [revenues_from_calves_colE_tbl4, revenues_from_calves_colE_tbl4, revenues_from_calves_colO_tbl4, revenues_from_calves_colQ_tbl4, 0]

    operating_costs_tbl4 = -herd_size * annual_cow_costs
    operating_costs_adj_N_tbl4 = -((herd_size * annual_cow_costs) + (drought_days_store3 * additional_cost_option1 * herd_size)) if drought_days_store3 > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_O_tbl4 = -((herd_size * annual_cow_costs) + (drought_months_store3 * pasture_rent * herd_size)) if drought_days_store3 > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_Q_tbl4 = -operating_costs_year2 if revenues_from_calves_row_tbl4[-2]==0 else -(herd_size * annual_cow_costs)

    operating_costs_row_tbl4 = [operating_costs_tbl4, operating_costs_adj_N_tbl4, operating_costs_adj_O_tbl4, operating_costs_adj_Q_tbl4 ,-operating_costs_year2]

    interest_income_expenses_row_tbl4 = [(c*(interest_invested_money/100) if c>0 else c*(interest_borrowed_money/100)) for c in ending_net_worth_cash_row_tbl3_final]
    
    profits_row_tbl4 = [c + v + k for c, v, k in zip(revenues_from_calves_row_tbl4, operating_costs_row_tbl4,interest_income_expenses_row_tbl4)]
    
    taxes_row_tbl4 = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row_tbl4]
    taxes_after_income_row_tbl4 = [c - v for c, v in zip(profits_row_tbl4, taxes_row_tbl4)]
    purchase_females_tbl4= herd_size*cost_replacement_animals if current_year+3==drought_end_year else 0 
    purchase_females_row_tbl4 = [0,0,0,purchase_females_tbl4 ,0]

    ending_net_worth_cows_1to3_tbl4 = herd_size*cost_replacement_animals if purchase_females_tbl4 > 0 else ending_net_worth_cows_row_tbl3_final[0]+purchase_females_row_tbl4[-2]
    ending_net_worth_cows_4to5_tbl4 = [c + v for c, v in zip(ending_net_worth_cows_row_tbl3_final[-2:], purchase_females_row_tbl4[-2:])]
    ending_net_worth_cows_row_tbl4_final = [ending_net_worth_cows_1to3_tbl4,ending_net_worth_cows_1to3_tbl4,ending_net_worth_cows_1to3_tbl4,
                                       ending_net_worth_cows_4to5_tbl4[0],ending_net_worth_cows_4to5_tbl4[1]]
    ending_net_worth_cash_row_tbl4_final = [c + v - k for c, v, k in zip(ending_net_worth_cash_row_tbl3_final,taxes_after_income_row_tbl4, purchase_females_row_tbl4)]
    total_78_79_row_tbl4_final = [c + v for c, v in zip(ending_net_worth_cows_row_tbl4_final, ending_net_worth_cash_row_tbl4_final)]

    data_values4 = [
        ["Revenues from Calves"] + revenues_from_calves_row_tbl4,
        ["Operating expenses"] + operating_costs_row_tbl4,
        ["Interest Income/Expenses"] + interest_income_expenses_row_tbl4,
        ["Profits"] + profits_row_tbl4,
        ["Taxes (SE, US Income, CO Income)"] + taxes_row_tbl4,
        ["After Tax Income"] + taxes_after_income_row_tbl4,
        ["Purchase replacement Females"] + purchase_females_row_tbl4,
    ]

    data_values4_summary = [
        ["Ending Net Worth - Cows"] + ending_net_worth_cows_row_tbl4_final,
        ["Ending Net Worth - Cash"] + ending_net_worth_cash_row_tbl4_final,
        ["Total ($)"] + total_78_79_row_tbl4_final
    ]

    # Combine row headers and data values
    df4 = pd.DataFrame(data_values4, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])
    df4_summary = pd.DataFrame(data_values4_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])


    ## fifth table

    revenues_from_calves_colE_tbl5 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    revenues_from_calves_colO_tbl5 = ((herd_size * (percent_calves_sold/100)) - calf_death_loss) * (weight_at_weaning * (1 + (weaning_weight_adjustment/100))) * price_weaning_years3_5 if current_year+4 < drought_end_year else (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5
    revenues_from_calves_colQ_tbl5 = (herd_size * (percent_calves_sold/100)) * weight_at_weaning * price_weaning_years3_5 if current_year+4 > drought_end_year else 0

    revenues_from_calves_row_tbl5 = [revenues_from_calves_colE_tbl5, revenues_from_calves_colE_tbl5, revenues_from_calves_colO_tbl5, revenues_from_calves_colQ_tbl5, 0]

    operating_costs_tbl5 = -herd_size * annual_cow_costs
    operating_costs_adj_N_tbl5 = -((herd_size * annual_cow_costs) + (drought_days_store4 * additional_cost_option1 * herd_size)) if drought_days_store4 > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_O_tbl5 = -((herd_size * annual_cow_costs) + (drought_months_store3 * pasture_rent * herd_size)) if drought_days_store4 > 0 else -(herd_size * annual_cow_costs)
    operating_costs_adj_Q_tbl5 = -operating_costs_year2 if revenues_from_calves_row_tbl5[-2]==0 else -(herd_size * annual_cow_costs)

    operating_costs_row_tbl5 = [operating_costs_tbl5, operating_costs_adj_N_tbl5, operating_costs_adj_O_tbl5, operating_costs_adj_Q_tbl5 ,-operating_costs_year2]

    interest_income_expenses_row_tbl5 = [(c*(interest_invested_money/100) if c>0 else c*(interest_borrowed_money/100)) for c in ending_net_worth_cash_row_tbl4_final]
    
    profits_row_tbl5 = [c + v + k for c, v, k in zip(revenues_from_calves_row_tbl5, operating_costs_row_tbl5,interest_income_expenses_row_tbl5)]
    
    taxes_row_tbl5 = [(c*(0.124+0.15+0.04) if c > 0 else 0) for c in profits_row_tbl5]
    taxes_after_income_row_tbl5 = [c - v for c, v in zip(profits_row_tbl5, taxes_row_tbl5)]
    purchase_females_tbl5= herd_size*cost_replacement_animals if current_year+4==drought_end_year else 0 
    purchase_females_row_tbl5 = [0,0,0,purchase_females_tbl5 ,0]

    ending_net_worth_cows_1to3_tbl5 = herd_size*cost_replacement_animals if purchase_females_tbl5 > 0 else ending_net_worth_cows_row_tbl4_final[0]+purchase_females_row_tbl5[-2]
    ending_net_worth_cows_4to5_tbl5 = [c + v for c, v in zip(ending_net_worth_cows_row_tbl4_final[-2:], purchase_females_row_tbl5[-2:])]
    ending_net_worth_cows_row_tbl5_final = [ending_net_worth_cows_1to3_tbl5,ending_net_worth_cows_1to3_tbl5,ending_net_worth_cows_1to3_tbl5,
                                       ending_net_worth_cows_4to5_tbl5[0],ending_net_worth_cows_4to5_tbl5[1]]
    ending_net_worth_cash_row_tbl5_final = [c + v - k for c, v, k in zip(ending_net_worth_cash_row_tbl4_final,taxes_after_income_row_tbl5, purchase_females_row_tbl5)]
    total_78_79_row_tbl5_final = [c + v for c, v in zip(ending_net_worth_cows_row_tbl5_final, ending_net_worth_cash_row_tbl5_final)]




    data_values5 = [
        ["Revenues from Calves"] + revenues_from_calves_row_tbl5,
        ["Operating expenses"] + operating_costs_row_tbl5,
        ["Interest Income/Expenses"] + interest_income_expenses_row_tbl5,
        ["Profits"] + profits_row_tbl5,
        ["Taxes (SE, US Income, CO Income)"] + taxes_row_tbl5,
        ["After Tax Income"] + taxes_after_income_row_tbl5,
        ["Purchase replacement Females"] + purchase_females_row_tbl5,
    ]

    data_values5_summary = [
        ["Ending Net Worth - Cows"] + ending_net_worth_cows_row_tbl5_final,
        ["Ending Net Worth - Cash"] + ending_net_worth_cash_row_tbl5_final,
        ["Total ($)"] + total_78_79_row_tbl5_final
    ]

    # Combine row headers and data values
    df5 = pd.DataFrame(data_values5, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])
    df5_summary = pd.DataFrame(data_values5_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])

    # Summary table

    summary_total_row = [c - v for c, v in zip(total_78_79_row_tbl5_final, total_64_66_row)]
    summary_percow_row = [c / herd_size for c in summary_total_row]
    summary_percent_row = [(c / v)*100 for c, v in zip(summary_total_row, total_64_66_row)]


    data_values_summary = [
        ["Change in net worth over 5 years"] + ["", "", "", "", ""],
        ["Total ($)"] + summary_total_row,
        ["$/cow"] + summary_percow_row,
        ["Percentage change over 5 years (%)"] + summary_percent_row,
        
    ]

    # Combine row headers and data values
    df_summary = pd.DataFrame(data_values_summary, columns=["","Normal conditions", "Buy feed", "Rent pasture", "Replace", "Do not replace"])

    return (df1_current_summary.to_dict(orient='records'), df1.to_dict(orient='records'), df1_summary.to_dict(orient='records'), 
            df2.to_dict(orient='records'), df2_summary.to_dict(orient='records'), 
            df3.to_dict(orient='records'), df3_summary.to_dict(orient='records'),
            df4.to_dict(orient='records'), df4_summary.to_dict(orient='records'),
            df5.to_dict(orient='records'), df5_summary.to_dict(orient='records'),
            df_summary.to_dict(orient='records'),df_summary.to_dict(orient='records'))



def direction(value):
    """Return 'increase' or 'decrease' based on the sign of the value."""
    return 'increase' if value > 0 else 'decrease'



@callback(
    dash.dependencies.Output('output-comparison-summary', 'children'),
    [dash.dependencies.Input('output-comparison-tablesummary-data-store', 'data')]
)
def update_output(data):
    # Convert the data back to a DataFrame
    df_summary = pd.DataFrame(data)

    # Extract the "Percentage change (over 5 years)" row
    percentage_change_row = df_summary.iloc[3, 1:].astype(float)
    
    # Get the column name and the value of the minimum and maximum
    min_col_name = percentage_change_row.idxmin()
    min_value = round(percentage_change_row[min_col_name], 0)
    min_col_name_display = (
        "acquiring feed" if min_col_name == "Buy feed" else
        "renting additional pasture" if min_col_name == "Rent pasture" else
        "replacing cows" if min_col_name == "Replace" else
        "not replacing cows"
    )

    max_col_name = percentage_change_row.idxmax()
    max_value = round(percentage_change_row[max_col_name], 0)
    max_col_name_display = (
        "acquiring feed" if max_col_name == "Buy feed" else
        "renting additional pasture" if max_col_name == "Rent pasture" else
        "replacing cows" if max_col_name == "Replace" else
        "not replacing cows"
    )

    # Determine the direction of change (increase or decrease)
    min_direction = direction(min_value)
    max_direction = direction(max_value)
    min_arrow_direction = "up" if min_direction == "increase" else "down"
    max_arrow_direction = "up" if max_direction == "increase" else "down"

    # sentence = (f"The least profitable option is '{min_col_name}', showing a {min_direction} of {abs(min_value)}% over 5 years. "
    #        f"Conversely, the most profitable option is '{max_col_name}', with a {max_direction} of {abs(max_value)}%.")

    # variables_style = {"color": "#cf8b0e", "font-size": "20px","vertical-align": "middle"}
    # text_style = {"font-size": "15px","vertical-align": "middle"}



    
    sentence = html.Div(id="summary-decision-text", children=[
        html.Span(f"When considering strategies in the face of a potential drought—based on the parameters outlined earlier—, ", className="text-style"),
        html.Span(f"{min_col_name_display}", className="variable-style"),
        html.Span(f" is expected to be the least profitable choice, with a projected net worth ", className="text-style"),
        html.I(className=f"fa fa-arrow-{min_arrow_direction}", style={"color": "#cf8b0e", "font-size": "15px", "vertical-align": "middle"}),
        html.Span(f" {min_direction} of ", className="variable-style"),
        html.Span(f"{abs(min_value)}%", className="variable-style"),
        html.Span(f" over 5 years. Conversely, the strategy of ", className="text-style"),
        html.Span(f"{max_col_name_display}", className="variable-style"),
        html.Span(f" holds promise, with a potential net worth ", className="text-style"),
        html.I(className=f"fa fa-arrow-{max_arrow_direction}", style={"color": "#cf8b0e", "font-size": "15px", "vertical-align": "middle"}),
        html.Span(f" {max_direction} of ", className="variable-style"),
        html.Span(f"{abs(max_value)}%.", className="variable-style")
    ])


    
    return sentence
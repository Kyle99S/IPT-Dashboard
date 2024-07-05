import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import base64
import io

# Initialize the global data variables
data = pd.DataFrame()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1("COVID-19 Survey Student Responses Dashboard", className=""),
    dcc.Upload(
        id='upload-data', 
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files', className="")
        ], style={
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center',
            'gap': '.3em',
            'height': '100%',
        }),
        style={
            'width': '100%',
            'height': '10em',
            'border': 'dashed .12rem #3FA2F6',
            'borderRadius': '.25rem',
            'textAlign': 'center',
            'backgroundColor': 'hsl(207, 81%, 95%)',
        },
        multiple=False
    ),
    dbc.Container([
        dbc.Label('Enter Table Name:', html_for="table-name-input"),
        dbc.Input(id='table-name-input', type='text', placeholder="Enter Table Name")
    ], style={'margin': '10px', 'display': 'none'}),
    dbc.Button('Purge Data', id='purge-button', n_clicks=0, class_name="btn btn-danger"),
    dash_table.DataTable(id='data-table', page_size=10, 
                         style_table={'overflowY': 'scroll'},
                         style_data={'padding': '.55rem', 'font-family': 'Poppins'},
                         style_header={'padding': '.55rem', 'backgroundColor': '#3FA2F6', 'color': '#FAFAFA', 'font-family': 'Poppins'}),
    dcc.Tabs(id="tabs", value='tab-1', children=[]),
    dbc.Container(id='tabs-content', class_name="w-100 d-flex justify-content-center")
], class_name="d-flex flex-column py-3", style={'gap': '1.25em'})

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename:
            df = pd.read_json(io.BytesIO(decoded))
        else:
            return None
        return df
    except Exception as e:
        print(e)
        return None

@app.callback(
    [Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('tabs', 'children'),
     Output('tabs-content', 'children')],
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('tabs', 'value'),
     Input('purge-button', 'n_clicks')],
    [State('table-name-input', 'value'),
     State('data-table', 'data')]
)
def update_output(contents, filename, tab, n_clicks, table_name_input, current_data):
    global data, table_name

    # If the purge button is clicked, reset the data and table name
    if n_clicks > 0:
        data = pd.DataFrame()
        table_name = ""
        return [], [], [], html.Div("Data has been purged. Upload new data to view the dashboard.")

    # If new data is uploaded, parse and process it
    if contents is not None:
        df = parse_contents(contents, filename)
        if df is not None:
            df.dropna(axis=0, inplace=True)
            if "Prefered social media platform" in df.columns:
                df["Prefered social media platform"] = df["Prefered social media platform"].replace({"Whatsapp": "WhatsApp"})
            if "Time spent on TV" in df.columns:
                df["Time spent on TV"] = df["Time spent on TV"].replace({"n": "0", "N": "0", "No tv": "0", " ": "0"})
                df["Time spent on TV"] = df["Time spent on TV"].astype("float64")
            if "Do you find yourself more connected with your family, close friends , relatives  ?" in df.columns:
                df["Are they connected with family and friends"] = df["Do you find yourself more connected with your family, close friends , relatives  ?"]
                df.drop(columns=["Do you find yourself more connected with your family, close friends , relatives  ?"], inplace=True)
            data = df
            table_name = table_name_input if table_name_input else " "
            columns = [{"name": i, "id": i} for i in df.columns]
            data_rows = df.to_dict('records')
        else:
            data = pd.DataFrame()
            columns = []
            data_rows = []
    else:
        data = pd.DataFrame(current_data)
        columns = [{"name": i, "id": i} for i in data.columns]
        data_rows = current_data

    if data.empty:
        return data_rows, columns, [], html.Div("No data available.")

    tabs = [
        dcc.Tab(label=f'{table_name} - Online Class Experience', value='tab-1'),
        dcc.Tab(label=f'{table_name} - Self Study vs Social Media', value='tab-2'),
        dcc.Tab(label=f'{table_name} - Age of Subject, Time spent on Fitness and Health Issues', value='tab-3'),
        dcc.Tab(label=f'{table_name} - Time spent on Online Class vs Medium', value='tab-4'),
        dcc.Tab(label=f'{table_name} - Time Spent on Sleep vs Time Spent on Social Media and Preferred Social media', value='tab-5'),
    ]

    if tab == 'tab-1':
        if "Rating of Online Class experience" in data.columns:
            fig = px.pie(data, names="Rating of Online Class experience", 
                         title="Rating of Online Class Experience",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            tab_content = html.Div([dcc.Graph(figure=fig)])
        else:
            tab_content = html.Div("No data available for Rating of Online Class experience.")
    elif tab == 'tab-2':
        if "Time spent on self study" in data.columns and "Time spent on social media" in data.columns and "Time spent on fitness" in data.columns:
            fig = px.scatter(data, x="Time spent on self study", y="Time spent on social media", 
                             color="Time spent on fitness", 
                             title="Self Study vs Social Media",
                             labels={
                                 "Time spent on self study": "Time Spent on Self Study (hours)",
                                 "Time spent on social media": "Time Spent on Social Media (hours)"
                             },
                             color_continuous_scale=px.colors.sequential.Plasma)
            tab_content = html.Div([dcc.Graph(figure=fig)])
        else:
            tab_content = html.Div("No data available for Self Study vs Social Media.")
    elif tab == 'tab-3':
        if "Age of Subject" in data.columns and "Time spent on fitness" in data.columns and "Health issue during lockdown" in data.columns:
            fig = px.scatter(data, x="Age of Subject", y="Time spent on fitness", 
                             color="Health issue during lockdown", 
                             title="Time spent on fitness, Age of Subject, and Health Issues",
                             labels={
                                 "Age of Subject": "Age of Subject (years)",
                                 "Time spent on fitness": "Time spent on fitness"
                             },
                             color_discrete_sequence=px.colors.qualitative.Set2)
            tab_content = html.Div([dcc.Graph(figure=fig)])
        else:
            tab_content = html.Div("No data available for Stress Busters.")
    elif tab == 'tab-4':
        if "Time spent on Online Class" in data.columns and "Medium for online class" in data.columns:
            fig = px.box(data, x="Medium for online class", y="Time spent on Online Class",
                         title="Time Spent on Online Class vs Medium for Online Class",
                         labels={
                             "Medium for online class": "Medium for Online Class",
                             "Time spent on Online Class": "Time Spent on Online Class (hours)"
                         },
                         color="Medium for online class")
            tab_content = html.Div([dcc.Graph(figure=fig)])
        else:
            tab_content = html.Div("No data available for Time Spent on Online Class vs Medium for Online Class.")
    elif tab == 'tab-5':
        if "Time spent on sleep" in data.columns and "Time spent on social media" in data.columns and "Prefered social media platform" in data.columns:
            fig = go.Figure()
            platforms = data["Prefered social media platform"].unique()
            for platform in platforms:
                filtered_data = data[data["Prefered social media platform"] == platform]
                fig.add_trace(go.Bar(
                    x=["Time spent on sleep", "Time spent on social media"], 
                    y=[filtered_data["Time spent on sleep"].mean(), filtered_data["Time spent on social media"].mean()],
                    name=platform
                ))
            
            fig.update_layout(
                title="Average Time Spent on Sleep vs Social Media by Platform",
                xaxis_title="Activity",
                yaxis_title="Average Time Spent (hours)",
                barmode='group'
            )
            tab_content = html.Div([dcc.Graph(figure=fig)])
        else:
            tab_content = html.Div("No data available for Time Spent on Sleep vs Time Spent on Social Media.")

    return data_rows, columns, tabs, tab_content

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

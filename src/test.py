# imports
from dash import dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash
from dash import dash_table
from dash.dependencies import Input, Output, State
import re

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from collections import defaultdict

from datetime import *
import datetime

pio.renderers.default = "iframe"
# -----------------------------------------------------------

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

####################
# Helper Functions #
####################


def remove_special_characters(string):
    # Define the pattern for special characters
    pattern = r"[^a-zA-Z0-9]"

    # Use regex to remove special characters
    cleaned_string = re.sub(pattern, "", string)

    return cleaned_string


# ---------------------------------------------------
# reading the data
data = pd.read_csv("../data/module_data_augmented.csv")

# dtype conversion
categorical_cols = [
    "course_id",
    "module_id",
    "module_name",
    "state",
    "student_id",
    "student_name",
    "items_id",
    "items_title",
    "items_type",
    "items_module_id",
    "item_cp_req_type",
    "item_cp_req_completed",
    "course_name",
]

# convert the timestamp to datetime format
# fix the column data types
data["completed_at"] = pd.to_datetime(data["completed_at"], format="%d-%m-%Y %H:%M")

for col in categorical_cols:
    data[col] = data[col].astype("category")

# remove special characters from course_name
data["course_name"] = data["course_name"].apply(remove_special_characters)

# Make the mapping of any id to the corresponding names
course_dict = defaultdict(str)
for _, row in data.iterrows():
    course_dict[str(row["course_id"])] = row["course_name"]


####################
#     Layout       #
####################

# Styling

# Define the style for the tabs
tab_style = {
    "height": "30px",
    "padding": "8px",
}

# Define the style for the selected tab
selected_tab_style = {
    "height": "30px",
    "padding": "5px",
    "borderTop": "2px solid #13233e",
    "borderBottom": "2px solid #13233e",
    "backgroundColor": "#13233e",
    "color": "white",
}

# Define header style
heading_style = {
    "borderTop": "2px solid #aab4c2",
    "borderBottom": "2px solid #aab4c2",
    "backgroundColor": "#aab4c2",
    "color": "white",
    "padding": "5px",
    "text-align": "center",
}

# Define Tab text style
text_style = {
    "font-size": "16px",
    "font-weight": "bold",
    "color": "#13233e",
    "padding": "5px",
}


# Style Html Div
div_style = {
    "display": "flex",
    "justify-content": "center",
    "align-items": "center",
}

# dropdpown options

course_options = [
    {"label": course_name, "value": course_id}
    for course_id, course_name in course_dict.items()
]
# course_options.extend([{"label": "All", "value": "All"}])

# student_options = [
#     {"label": student_name, "value": student_id}
#     for student_id, student_name in student_dict.items()
# ]
# student_options.extend([{"label": "All", "value": "All"}])

# # module checkbox options
# module_options = [
#     {"label": module_name, "value": module_id}
#     for module_id, module_name in module_dict.items()
# ]


##############
# Callbacks  #
##############
@app.callback(
    Output("module-checkboxes", "options"),
    Input("course-dropdown", "value"),
)
def update_checklist(val):
    # Edge case, if no value selected in course-dropdown
    if val is None:
        module_options = [{"label": "No Course selected", "value": 0}]
        return module_options

    # filter by the course selected
    subset_data = data.copy()

    selected_course = remove_special_characters(course_dict[val])

    subset_data = subset_data[subset_data.course_name == selected_course]

    # Create dictionaries accordingly to selected_course
    module_dict, item_dict, student_dict = (defaultdict(str) for _ in range(3))

    for _, row in subset_data.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_module_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    if val != None:
        module_options = [
            {"label": module_name, "value": module_id}
            for module_id, module_name in module_dict.items()
        ]
    return module_options


@app.callback(
    Output("student-dropdown", "options"),
    Input("course-dropdown", "value"),
)
def update_student_dropdown(val):
    # Edge case, if no value selected in course-dropdown
    if val is None:
        student_options = [{"label": "No Course selected", "value": 0}]
        return student_options

    # filter by the course selected
    subset_data = data.copy()

    selected_course = remove_special_characters(course_dict[val])

    subset_data = subset_data[subset_data.course_name == selected_course]

    # Create dictionaries accordingly to selected_course
    module_dict, item_dict, student_dict = (defaultdict(str) for _ in range(3))

    for _, row in subset_data.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_module_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    if val != None:
        student_options = [
            {"label": student_name, "value": student_id}
            for student_id, student_name in student_dict.items()
        ]
    return student_options


# @app.callback(
#     Output("output", "children"),
#     Input("button", "n_clicks"),
#     State("button", "children"),
# )
# def update_buttonclick(n_clicks, button_text):
#     if n_clicks is None:
#         return ""
#     else:
#         return f"Button clicked {n_clicks} times"


# -----------------------------------------------------------------
# Layout
app.layout = dbc.Container(
    fluid=True,
    children=[
        html.Div(
            children=[
                html.H2(
                    "Module Progress Demo Dashboard",
                    style=heading_style,
                ),
            ],
            style={"padding": "0.05px"},
        ),
        html.Div(
            className="dashboard-filters-container",
            children=[
                html.Label(
                    "Overall filters ",
                    style=text_style,
                )
            ],
        ),
        dbc.Row(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="course-dropdown",
                            options=course_options,  # list of dropdown, labels are show, value is conveyed
                            value=course_options[0]["label"],  # default selection
                            style={"width": "400px", "fontsize": "1px"},
                        )
                    ],
                    style={"width": "35%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id="student-dropdown",
                            options=[],
                            value=" ",
                            style={"width": "400px", "fontsize": "1px"},
                        ),
                    ],
                    style={"width": "35%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        dbc.Button(
                            "Export Report",
                            id="report-button",
                            color="primary",
                            className="mr-2",
                        ),
                    ],
                    style={"width": "30%", "display": "inline-block"},
                ),
            ],
            className="mb-3",  # Add spacing between rows
        ),
        dbc.Row(
            [
                dcc.Tabs(
                    id="tabs",
                    value="Pages",
                    children=[
                        dcc.Tab(
                            label="View Modules",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[],
                        ),
                        dcc.Tab(
                            label="View Items",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[],
                        ),
                    ],
                ),
                html.Br(),
                html.Label(
                    "Select Modules ",
                    style=text_style,
                ),
                dbc.Col(
                    [
                        dbc.Checklist(
                            id="module-checkboxes",
                            options=[],  # default empty checklist
                            value=[],
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        dcc.Graph(
                            id="plot1",
                            style={
                                "width": "50%",
                                "height": "300px",
                                "display": "inline-block",
                                "border": "2px solid #ccc",
                                "border-radius": "5px",
                                "padding": "10px",
                            },
                        ),
                        dcc.Graph(
                            id="plot2",
                            style={
                                "width": "50%",
                                "height": "300px",
                                "display": "inline-block",
                                "border": "2px solid #ccc",
                                "border-radius": "5px",
                                "padding": "10px",
                            },
                        ),
                    ],
                    width=9,
                ),
            ],
            className="mb-3",  # Add spacing between rows
        ),
        dbc.Row(
            [
                dbc.Col(width=3),
                dbc.Col(
                    [
                        dcc.Graph(
                            id="plot3",
                            style={
                                "width": "100%",
                                "height": "300px",
                                "display": "inline-block",
                                "border": "2px solid #ccc",
                                "border-radius": "5px",
                                "padding": "10px",
                            },
                        )
                    ],
                    width=9,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Attributions: Ranjit Sundaramurthi",
                            style={
                                "font-size": "12px",
                                "font-weight": "normal",
                                "color": "#13233e",
                                "padding": "5px",
                            },
                        ),
                        html.Label(
                            "Licence: MIT",
                            style={
                                "font-size": "12px",
                                "font-weight": "normal",
                                "color": "#13233e",
                                "padding": "5px",
                            },
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.Label(
                            "Other Content here",
                            style={
                                "font-size": "12px",
                                "font-weight": "normal",
                                "color": "#13233e",
                                "padding": "5px",
                            },
                        )
                    ],
                    width=9,
                ),
            ]
        ),
    ],
    className="mt-3",
)


if __name__ == "__main__":
    app.run_server(debug=True)

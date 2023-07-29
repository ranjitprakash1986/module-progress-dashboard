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


def get_dicts(df):
    """
    Creates and returns the df dictionaries mapping ids to names,
    module number, module name, item name and student name, in that order specifically
    """
    # Initialize dicts
    global module_num
    module_num, module_dict, item_dict, student_dict = (
        defaultdict(str) for _ in range(4)
    )

    for _, row in df.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_module_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    # map the module id to a module number for labeling
    for i, k in enumerate(module_dict.keys()):
        module_num[k] = f"Module:{i+1}"

    return module_num, module_dict, item_dict, student_dict


def get_sub_dicts(df):
    """
    df is data after being by course and selected modules.
    Creates and returns the dictionaries mapping ids to names,
    module name, item name and student name, in that order specifically
    """
    # Initialize dicts

    module_dict, item_dict, student_dict = (defaultdict(str) for _ in range(3))

    for _, row in df.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_module_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    return module_dict, item_dict, student_dict


def get_completed_percentage(df, module, state="completed"):
    """
    Returns the state percentage of module in df
    """
    # df is the filtered_data after selections
    df_module = df[df.module_id.astype(str) == module]

    # df is a subset dataframe that contains a specific module as selected in the dropdown
    # If other modules are iterated the size of the dataframe will be 0
    if df_module.shape[0] == 0:
        return 0

    total_module_students = df_module.student_id.unique().size
    percentage = (
        df_module[df_module.state == state].student_id.unique().size
        / total_module_students
    )
    return percentage


def get_completed_percentage_date(df, module, date):
    """
    Returns the completed percentage of a module in df until a specified date

    Inputs
    ------
    df: dataframe
    module: str, name of the module
    date: datetime.date, date till which the completion percentage of each module is desired

    Returns
    -------
    percentage: float, percentage value

    """

    # Convert the date to datetime with time component set to midnight
    datetime_date = datetime.datetime.combine(date, datetime.datetime.min.time())

    # CHANGE TO MODULE ID INSTEAD OF NAME
    df_module = df[df.module_id.astype(str) == module]
    total_module_students = df_module.student_id.unique().size

    # If there is not a single row with completion date then we get a datetime error since blanks are not compared to date
    # In order to get around this edge case, return 0
    if df_module[df_module.state == "completed"].size == 0:
        return 0.0

    percentage = (
        df_module[
            (df_module.state == "completed")
            & (df_module["completed_at"].dt.date <= date)
        ]
        .student_id.unique()
        .size
        / total_module_students
    )

    return percentage


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

# All accessible vairables

module_status = ["locked", "unlocked", "started", "completed"]

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

# Define text style
text_style = {
    "font-size": "16px",
    "font-weight": "bold",
    "color": "#13233e",
    "padding": "5px",
}

sidebar_text_style = {
    "font-size": "10px",
    "display": "inline-block",
    # "font-weight": "bold",
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

# Colorblind friendly colors Ref: https://jacksonlab.agronomy.wisc.edu/2016/05/23/15-level-colorblind-friendly-palette/
color_palette_1 = [
    "#000000",
    "#004949",
    "#009292",
    "#ff6db6",
    "#ffb6db",
    "#490092",
    "#006ddb",
    "#b66dff",
    "#6db6ff",
    "#b6dbff",
    "#920000",
    "#924900",
    "#db6d00",
    "#24ff24",
    "#ffff6d",
]

# Ref: https://stackoverflow.com/questions/65013406/how-to-generate-30-distinct-colors-that-are-color-blind-friendly
color_palette_2 = [
    "#999999",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
]

# Ref: https://stackoverflow.com/questions/65013406/how-to-generate-30-distinct-colors-that-are-color-blind-friendly
color_palette_3 = [
    "#000000",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
]

date_spacing = "D7"  # Weekly spacing, adjust as per your requirement
axis_label_font_size = 12


##############
# Callbacks  #
##############
@app.callback(
    Output("module-checkboxes", "options"),
    Output("module-checkboxes", "value"),
    Input("course-dropdown", "value"),
)
def update_checklist(val):
    # Edge case, if no value selected in course-dropdown
    if val is None:
        module_options = [
            {"label": "No Course selected", "value": "No Course selected"}
        ]
        def_value = module_options
        return module_options, def_value

    # filter by the course selected
    subset_data = data.copy()

    selected_course = remove_special_characters(course_dict[val])

    subset_data = subset_data[subset_data.course_name == selected_course]

    # Create dictionaries accordingly to selected_course
    module_num, module_dict, item_dict, student_dict = get_dicts(subset_data)

    if val != None:
        module_options = [
            {
                "label": f"{module_num[module_id]}" + " " + f"{module_name}",
                "value": module_id,
            }
            for module_id, module_name in module_dict.items()
        ]

    # define a global color map for the modules
    global module_colors
    module_colors = {
        module_num[module_id]: color_palette_3[i]
        for module_id, i in zip(module_num.keys(), np.arange(len(module_num.keys())))
    }

    # Checking
    # print(module_colors)

    # Add the 'All' option at the beginning (Reconsider later)
    # module_options.insert(0, {"label": "All", "value": "All"})

    # default value, selects all the items in the checklist
    def_value = [module_options[i]["value"] for i in range(len(module_options))]
    return module_options, def_value


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
    module_num, module_dict, item_dict, student_dict = get_dicts(subset_data)

    if val != None:
        student_options = [
            {"label": student_name, "value": student_id}
            for student_id, student_name in student_dict.items()
        ]

    # Add the 'All' option at beginning of the list
    student_options.insert(0, {"label": "All", "value": "All"})

    return student_options


# filter the data based on user selections
@app.callback(
    Output("course-specific-data", "data"),
    [Input("course-dropdown", "value"), Input("module-checkboxes", "value")],
)
def update_filtered_data(selected_course, selected_modules):
    # Filter the DataFrame based on user selections

    filtered_df = data[
        (data["course_id"].astype(str) == selected_course)
        & (data["module_id"].astype(str).isin(selected_modules))
    ]

    # Convert the filtered DataFrame to JSON serializable format
    filtered_data = filtered_df.to_json(date_format="iso", orient="split")

    return filtered_data


# filter the data based on user selections
# @app.callback(
#     Output("student-specific-data", "data"),
#     [
#         Input("course-dropdown", "value"),
#         Input("module-dropdown", "value"),
#         Input("student-dropdown", "value"),
#     ],
# )
# def update_student_filtered_data(selected_course, selected_module, selected_student):
#     # Filter the DataFrame based on user selections

#     filtered_df = data[
#         (data["course_id"].astype(str) == selected_course)
#         & (data["module_id"].astype(str) == selected_module)
#         & (data["student_id"].astype(str) == selected_student)
#     ]

#     # Convert the filtered DataFrame to JSON serializable format
#     filtered_data = filtered_df.to_json(date_format="iso", orient="split")

#     return filtered_data


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


# Plot 1
@app.callback(
    Output("plot3", "figure"),
    [
        Input("course-specific-data", "data"),
        Input("date-slider", "start_date"),
        Input("date-slider", "end_date"),
    ],
)
def update_timeline(filtered_data, start_date, end_date):
    """
    Returns a lineplot of trend of module completion
    """
    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    assert isinstance(start_date, datetime.date)
    assert isinstance(end_date, datetime.date)

    # Create dictionaries accordingly to selected_course
    module_dict, item_dict, student_dict = get_sub_dicts(filtered_df)

    # For each module, create a lineplot with date on the x axis, percentage completion on y axis
    result_time = pd.DataFrame(columns=["Date", "Module", "Percentage Completion"])

    for module in module_dict.keys():
        timestamps = filtered_df[filtered_df.module_id.astype(str) == module][
            "completed_at"
        ].dt.date.unique()
        timestamps = [
            x for x in timestamps if type(x) != pd._libs.tslibs.nattype.NaTType
        ]

        filtered_timestamps = [
            timestamp for timestamp in timestamps if start_date <= timestamp <= end_date
        ]

        for date in filtered_timestamps:
            value = round(
                get_completed_percentage_date(filtered_df, module, date) * 100, 1
            )

            new_df = pd.DataFrame(
                [[date, module_num.get(module), value]],
                columns=["Date", "Module", "Percentage Completion"],
            )

            result_time = pd.concat([result_time, new_df], ignore_index=True)

    # Checking
    # print(f"Checking \n {result_time}")

    # Plotting
    fig_1 = go.Figure()
    for i, (module, group) in enumerate(result_time.groupby("Module")):
        sorted_group = group.sort_values("Date")

        if len(sorted_group) == 1:
            fig_1.add_trace(
                go.Scatter(
                    x=sorted_group["Date"],
                    y=sorted_group["Percentage Completion"],
                    mode="markers",
                    name=module,
                    marker=dict(
                        color=module_colors[module]
                    ),  # alt method: color_palette_1[i % len(color_palette_1)]
                )
            )

        else:
            fig_1.add_trace(
                go.Scatter(
                    x=sorted_group["Date"],
                    y=sorted_group["Percentage Completion"],
                    mode="lines",
                    name=module,
                    line=dict(color=module_colors[module]),
                )
            )

    fig_1.update_layout(
        title="Percentage Completion by Module",
        xaxis=dict(
            title="Date", tickangle=-90, title_font=dict(size=axis_label_font_size)
        ),
        yaxis=dict(title="Percentage", title_font=dict(size=axis_label_font_size)),
        plot_bgcolor="rgba(240, 240, 240, 0.8)",  # Light gray background color
        xaxis_gridcolor="rgba(200, 200, 200, 0.2)",  # Faint gridlines
        yaxis_gridcolor="rgba(200, 200, 200, 0.2)",  # Faint gridlines
        margin=dict(l=50, r=50, t=50, b=50),  # Add margin for a border line
        paper_bgcolor="white",  # Set the background color of the entire plot
    )

    # Set start and end dates with an offset of 1 days on either sides of the range for the display x-axis
    fig_1.update_xaxes(
        range=[
            (start_date - datetime.timedelta(days=1)),
            (end_date + datetime.timedelta(days=1)),
        ]
    )

    # Specify custom spacing between dates on the x-axis
    fig_1.update_xaxes(dtick=date_spacing)

    # Convert the figure to a JSON serializable format
    fig_1_json = fig_1.to_dict()

    return fig_1_json


# Plot 2
@app.callback(
    Output("plot2", "figure"),
    [Input("course-specific-data", "data"), Input("date-picker", "date")],
)
def update_box_plot(filtered_data, date_selected):
    """
    Returns a box plot of the completion duration of selected modules in the selected course
    """
    if isinstance(date_selected, str):
        date_selected = datetime.datetime.strptime(date_selected, "%Y-%m-%d")

    assert isinstance(date_selected, datetime.datetime)

    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    # Create dictionaries accordingly to selected_course
    module_num, module_dict, item_dict, student_dict = get_dicts(filtered_df)

    # filter the data by state = "completed"
    subset_data = filtered_df[filtered_df.state == "completed"]

    # Improvement: accept course start data as input
    course_start_date = date_selected
    course_start_time = datetime.time(0, 30)
    course_combined_datetime = course_start_date.combine(
        course_start_date, course_start_time
    )

    # compute the duration
    subset_data["duration"] = round(
        (subset_data["completed_at"] - course_combined_datetime)
        / np.timedelta64(1, "D"),
        0,
    )

    # Next we want to keep only one unique row per student, thereby there are no repetition for the same student
    subset_data = subset_data[
        ["module_id", "module_name", "state", "duration", "student_id"]
    ].drop_duplicates()
    subset_data["module"] = subset_data["module_id"].apply(
        lambda x: module_num.get(str(x))
    )

    # Checking
    # print(subset_data.head())

    # Plot
    # Create the box plot using Plotly Express
    fig_2 = px.box(
        subset_data,
        y="module",
        x="duration",
        points="all",
        title="Boxplot of module completion duration (days)",
        hover_data=["duration"],
    )
    fig_2.update_traces(boxpoints="outliers", boxmean=True)

    # Sort the y-axis in descending order
    fig_2.update_yaxes(categoryorder="category descending")

    # Customize the hover template
    hover_template = (
        "<b>%{y}</b><br>" + "Duration: %{x} days<br>" + "<extra></extra>"
    )  # The <extra></extra> tag removes the "trace 0" label

    fig_2.update_traces(hovertemplate=hover_template)

    fig_2_json = fig_2.to_dict()

    return fig_2_json


# Plot 3
@app.callback(
    Output("plot1", "figure"),
    [Input("course-specific-data", "data"), Input("status-radio", "value")],
)
def update_module_completion_barplot(filtered_data, value):
    """
    Plots a horizontal barplot of student percentage module completion per module
    """
    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    if value not in module_status and value != "All":
        print("Check radio button value for module status, it is invalid")

    if value == "All":
        radio_selection = module_status

    if value in module_status:
        radio_selection = value

    result = {}
    modules = list(filtered_df.module_id.unique().astype(str))

    # Create dictionaries accordingly to selected_course
    module_dict, item_dict, student_dict = get_sub_dicts(filtered_df)

    for module in modules:
        result[module_num.get(module)] = [
            round(
                get_completed_percentage(filtered_df, module, module_status[i]) * 100, 1
            )
            for i in range(len(module_status))
        ]

    df_mod = (
        pd.DataFrame(result, index=module_status)
        .T.reset_index()
        .rename(columns={"index": "Module"})
    )

    # Checking
    # print(df_mod)

    # Melt the DataFrame to convert columns to rows
    melted_df = pd.melt(
        df_mod,
        id_vars="Module",
        value_vars=radio_selection,
        var_name="Status",
        value_name="Percentage Completion",
    )

    # Checking
    # print(melted_df)

    # Define the color mapping
    color_mapping = {
        module_status[i]: color_palette_2[i] for i in range(len(module_status))
    }

    # Create a horizontal bar chart using Plotly
    fig_3 = px.bar(
        melted_df,
        y="Module",
        x="Percentage Completion",
        color="Status",
        orientation="h",
        labels={"Percentage Completion": "Percentage Completion (%)"},
        title="Percentage of Students for Each Module",
        category_orders={"Module": sorted(melted_df["Module"].unique())},
        color_discrete_map=color_mapping,  # Set the color mapping
    )

    fig_3.update_layout(
        showlegend=True,  # Show the legend indicating the module status colors
        legend_title="Status",  # Customize the legend title,
        # legend_traceorder="reversed",  # Reverse the order of the legend items
    )

    # Modify the plotly configuration to change the background color
    fig_3.update_layout(
        plot_bgcolor="rgb(255, 255, 255)",
        xaxis=dict(title_font=dict(size=axis_label_font_size)),
        yaxis=dict(title_font=dict(size=axis_label_font_size)),
        xaxis_range=[0, 100],
    )

    # Convert the figure to a JSON serializable format
    fig_3_json = fig_3.to_dict()

    return fig_3_json


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
                            value=course_options[0]["value"],  # default value
                            style={"width": "350px", "fontsize": "1px"},
                        )
                    ],
                    style={"width": "35%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id="student-dropdown",
                            options=[],
                            value="",
                            style={"width": "350px", "fontsize": "1px"},
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
                dcc.Store(id="course-specific-data"),
                dcc.Store(id="student-specific-data"),
                dcc.Tabs(
                    id="tabs",
                    value="Pages",
                    children=[
                        dcc.Tab(
                            label="About Me",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                html.Br(),
                                html.Label(
                                    "This is an About me",
                                    style=text_style,
                                ),
                            ],
                        ),
                        dcc.Tab(
                            label="View Modules",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                html.Br(),
                                html.Label(
                                    "Test 1",
                                    style=text_style,
                                ),
                            ],
                        ),
                        dcc.Tab(
                            label="View Items",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                html.Br(),
                                html.Label(
                                    "Test 2",
                                    style=text_style,
                                ),
                            ],
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        html.Br(),
                        html.Label(
                            "Select Course Start Date",
                            style=text_style,
                        ),
                        dcc.DatePickerSingle(
                            id="date-picker",
                            date="2023-01-01",  # Set the initial date to today's date
                            max_date_allowed=max(
                                pd.to_datetime(data["completed_at"])
                            ).date(),
                            display_format="YYYY-MM-DD",  # Specify the format in which the date will be displayed
                            style={
                                "marginLeft": "20px"  # Add 20px space to the left of the DatePickerSingle box
                            },
                        ),
                        html.Br(),
                        html.Label(
                            "Select Modules ",
                            style=text_style,
                        ),
                        dbc.Checklist(
                            id="module-checkboxes",
                            #    options=[],  # default empty checklist
                            #    value="", # default selected value
                        ),
                        html.Br(),
                        html.Label(
                            "Select Module State",
                            style=text_style,
                        ),
                        dcc.RadioItems(
                            id="status-radio",
                            options=[
                                {"label": " " + "All", "value": "All"},
                                *(
                                    {
                                        "label": " " + f"{module_status[i]}",
                                        "value": f"{module_status[i]}",
                                    }
                                    for i in range(len(module_status))
                                ),  # Adding extra items with list comprehension Ref: https://stackoverflow.com/questions/50504844/add-extra-items-in-list-comprehension
                            ],
                            value="All",
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
                dbc.Col(
                    [
                        html.Br(),
                        html.Label(
                            "Select Lineplot dates",
                            style=text_style,
                        ),
                        dcc.DatePickerRange(
                            id="date-slider",
                            min_date_allowed=min(
                                pd.to_datetime(data["completed_at"])
                            ).date(),
                            max_date_allowed=max(
                                pd.to_datetime(data["completed_at"])
                            ).date(),
                            start_date=min(pd.to_datetime(data["completed_at"])).date(),
                            end_date=max(pd.to_datetime(data["completed_at"])).date(),
                            clearable=True,
                            style=text_style,
                        ),
                    ],
                    width=3,
                ),
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

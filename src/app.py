# imports
from dash import dash, html, dcc, Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash
from dash import dash_table
from dash.dependencies import Input, Output, State
import re
import os

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
    """
    Removes sepcial characters from the provided string

    Parameters:
        string (str): string from which special characters are to be removed

    Returns:
        cleaned_string (str): string without special characters
    """
    # Define the pattern for special characters
    pattern = r"[^a-zA-Z0-9]"

    # Use regex to remove special characters
    cleaned_string = re.sub(pattern, "", string)

    return cleaned_string


def get_dicts(df):
    """
    Creates and returns dictionaries,

    Parameters:
        df (dataframe): passed pandas dataframe

    Returns:
        module_num, module_dict, item_num, item_dict, student_dict (dict): Created dictionaries
    """

    # Initialize dicts
    module_num, module_dict, item_num, item_dict, student_dict = (
        defaultdict(str) for _ in range(5)
    )

    # Dictionary to map id to names
    for _, row in df.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    # Dictionary to map the module id to a module number used for labeling
    for i, k in enumerate(module_dict.keys()):
        module_num[k] = f"Module {i+1}:"

    # Dictionary to map the item id to a item number used for labeling
    for i, k in enumerate(item_dict.keys()):
        item_num[k] = f"Item {i+1}:"

    return module_num, module_dict, item_num, item_dict, student_dict


def get_item_completion_percentage(df, item):
    """
    Returns the percentage of students who completed 'item'

    Parameters:
        df (dataframe): passed pandas dataframe
        item (str): name of item

    Returns:
        percentage (float): computed percentage
    """

    # filter df by the provided item
    df_item = df[df.items_id.astype(str) == item]

    # Handling edge case
    if df_item.shape[0] == 0:
        return 0

    # total students who are/will work on item
    total_item_students = df_item.student_id.unique().size

    # compute percentage
    percentage = (
        df_item[df_item.item_cp_req_completed == 1.0].student_id.unique().size
        / total_item_students
    )
    return percentage


def get_completed_percentage(df, module, state="completed"):
    """
    Returns the percentage of students with module in given state

    Parameters:
        df (dataframe): passed pandas dataframe
        module (str): module_id
        state (str): module state

    Returns:
        percentage (float): computed percentage
    """
    # filter the dataframe with the passed module
    df_module = df[df.module_id.astype(str) == module]

    # Handling edge case
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

    Parameters:
        df (dataframe): passed pandas dataframe
        module (str): module_id
        date (datetime.date): date till which the completion percentage is to be computed

    Returns:
        percentage (float): computed percentage
    """

    # Convert the date to datetime with time component set to midnight
    datetime_date = datetime.datetime.combine(date, datetime.datetime.min.time())

    # filter df
    df_module = df[df.module_id.astype(str) == module]

    total_module_students = df_module.student_id.unique().size

    # Handling edge case, when no module is computed.
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
data = pd.read_csv("data/module_data.csv")

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


############################
#  Defining vairables      #
############################

module_status = ["completed", "started", "unlocked", "locked"]

# Make the mapping of any id to the corresponding names
global course_dict
global module_dict
global item_dict

course_dict, module_dict, item_dict = (defaultdict(str) for _ in range(3))

for _, row in data.iterrows():
    course_dict[str(row["course_id"])] = row["course_name"]
    module_dict[str(row["module_id"])] = row["module_name"]
    item_dict[str(row["items_id"])] = row["items_title"]


####################
#     Layout       #
####################

# Styling

# Define the style for the tabs
tab_style = {
    "height": "50px",
    "padding": "8px",
    "textAlign": "center",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "border-radius": "10px",
    "margin-right": "10px",
    "margin-left": "10px",
}

# Define the style for the selected tab
selected_tab_style = {
    "height": "50px",
    "padding": "5px",
    "borderTop": "2px solid #13233e",
    "borderBottom": "2px solid #13233e",
    "backgroundColor": "#13233e",
    "color": "white",
    "textAlign": "center",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "border-radius": "10px",
    "margin-right": "10px",
    "margin-left": "10px",
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

sub_heading_style = {
    "font-size": "20px",
    "font-weight": "bold",
    "color": "#13233e",
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
    "color": "#13233e",
    "padding": "5px",
}


# Style Html Div
div_style = {
    "display": "flex",
    "justify-content": "center",
    "align-items": "center",
}

# Dropdpown options

course_options = [
    {"label": course_name, "value": course_id}
    for course_id, course_name in course_dict.items()
]


# Colorblind friendly colors
# Ref: https://jacksonlab.agronomy.wisc.edu/2016/05/23/15-level-colorblind-friendly-palette/
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

# Plots font style, adjust as per your requirement
axis_label_font_size = 14
title_font_size = 16


##############
# Callbacks  #
##############


@app.callback(
    Output("module-checkboxes", "options"),
    Output("module-checkboxes", "value"),
    Input("course-dropdown", "value"),
)
def update_module_checklist(val):
    """
    Updates the module checklist in the 'View Modules'

    Parameters:
        val (str): Selected Course

    Returns:
        module_options (list): Module Checkboxes options
        def_value (list): Module checkbox default selections
    """

    # Handling edge case
    if val is None:
        module_options = [
            {"label": "No Course selected", "value": "No Course selected"}
        ]
        def_value = module_options
        return module_options, def_value

    # filter the data by selected course
    subset_data = data.copy()
    selected_course = remove_special_characters(course_dict[val])
    subset_data = subset_data[subset_data.course_name == selected_course]

    # Create dictionaries
    global module_num
    module_num, module_dict, item_num, item_dict, student_dict = get_dicts(subset_data)

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

    # default value, selects all the items in the checklist
    def_value = [module_options[i]["value"] for i in range(len(module_options))]
    return module_options, def_value


# # Update items checklist
@app.callback(
    Output("item-checkboxes", "options"),
    Output("item-checkboxes", "value"),
    [Input("course-dropdown", "value"), Input("module-dropdown", "value")],
)
def update_item_checklist(selected_course, selected_module):
    """
    Updates the module checklist in the 'View Items' tab

    Parameters:
        selected_course (str): Selected Course
        selected_module (str): Selected Module

    Returns:
        item_options (list): Item Checkboxes options
        def_value (list): Item checkbox default selections
    """

    # Handling edge case
    if selected_course is None or selected_module is None:
        item_options = [
            {
                "label": "Either Course or Module not selected",
                "value": "No Course selected",
            }
        ]
        def_value = item_options
        return item_options, def_value

    # filter by the course selected and selected module
    subset_data = data.copy()
    selected_course = remove_special_characters(course_dict[selected_course])

    subset_data = subset_data[
        (subset_data.course_name == selected_course)
        & (subset_data.module_id.astype(str) == selected_module)
    ]

    # Define dictionaries for items under the selcted course and selected module
    items_pos = defaultdict(str)
    items_id_name = defaultdict(str)

    for _, row in subset_data.iterrows():
        items_pos[str(row["items_id"])] = f"Item {row['items_position']}:"
        items_id_name[str(row["items_id"])] = row["items_title"]

    if selected_course != None and selected_module != None:
        item_options = [
            {
                "label": f"{items_pos[item_id]}" + " " + f"{item_name}",
                "value": item_id,
            }
            for item_id, item_name in items_id_name.items()
        ]

    # define a global color map for the items
    global item_colors
    item_colors = {
        items_pos[item_id]: color_palette_3[i]
        for item_id, i in zip(items_pos.keys(), np.arange(len(items_pos.keys())))
    }

    # default selection
    def_value = [item_options[i]["value"] for i in range(len(item_options))]
    return item_options, def_value


# Update module-dropdown options
@app.callback(
    Output("module-dropdown", "options"),
    Output("module-dropdown", "value"),
    Input("course-dropdown", "value"),
)
def update_module_dropdown(val):
    """
    Updates the module dropdown in the 'View Items' tab

    Parameters:
        val (str): Selected Course

    Returns:
        module_options (list): Module selection options
        def_value (str): Module default selection
    """

    # Handling edge case
    if val is None:
        module_options = [{"label": "No Course selected", "value": 0}]
        return module_options

    # filter by the course selected
    subset_data = data.copy()
    selected_course = remove_special_characters(course_dict[val])
    subset_data = subset_data[subset_data.course_name == selected_course]

    # Initialize dicts
    module_dict = defaultdict(str)

    for _, row in subset_data.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )

    if val != None:
        module_options = [
            {"label": module_name, "value": module_id}
            for module_id, module_name in module_dict.items()
        ]

    def_value = module_options[0]["value"]

    return module_options, def_value


# Update student-dropdown options
@app.callback(
    Output("student-dropdown-students-tab", "options"),
    Output("student-dropdown-modules-tab", "options"),
    Input("course-dropdown", "value"),
)
def update_student_dropdown_modules(val):
    """
    Updates the student dropdown

    Parameters:
        val (str): Selected Course

    Returns:
        student_options (list): Student selection options
    """

    # Handling edge case
    if val is None:
        student_options = [{"label": "No Course selected", "value": 0}]
        return student_options, student_options

    # filter by the course selected
    subset_data = data.copy()
    selected_course = remove_special_characters(course_dict[val])
    subset_data = subset_data[subset_data.course_name == selected_course]

    # Initialize dicts
    global student_dict
    student_dict = defaultdict(str)

    for _, row in subset_data.iterrows():
        student_dict[str(row["student_id"])] = row["student_name"]

    if val != None:
        student_options = [
            {"label": student_name, "value": student_id}
            for student_id, student_name in student_dict.items()
        ]

    # Add 'All' option in student_dict
    student_dict["All"] = "All"

    # Add the 'All' option at beginning of the list
    student_options.insert(0, {"label": "All", "value": "All"})

    return student_options, student_options


# Filter the data based on user selections
@app.callback(
    Output("student-specific-data", "data"),
    [
        Input("course-dropdown", "value"),
        Input("student-dropdown-students-tab", "value"),
    ],
)
def update_student_filtered_data(selected_course, selected_students):
    """
    Returns a filtered dataset by selected course and selected students

    Parameters:
        selected_course (str): Selected Course
        selected_students (str): Selected Students

    Returns:
        filtered_data (json): filtered data for storage
    """

    # Filter the data based on user selections
    if (
        selected_students == "All"
    ):  # don't need to filter by students, all are considered
        filtered_df = data[(data["course_id"].astype(str) == selected_course)]
    else:
        filtered_df = data[
            (data["course_id"].astype(str) == selected_course)
            & (data["student_id"].astype(str) == selected_students)
        ]

    # Convert the filtered DataFrame to JSON serializable format
    filtered_data = filtered_df.to_json(date_format="iso", orient="split")

    return filtered_data


# filter the data based on user selections
@app.callback(
    Output("course-specific-data", "data"),
    [
        Input("course-dropdown", "value"),
        Input("student-dropdown-modules-tab", "value"),
        Input("module-checkboxes", "value"),
    ],
)
def update_course_filtered_data(selected_course, selected_students, selected_modules):
    """
    Returns a filtered dataset by selected course, selected students and selected modules

    Parameters:
        selected_course (str): Selected Course
        selected_students (str): Selected Students
        selected_students (list): Selected Modules

    Returns:
        filtered_data (json): filtered data for storage
    """

    # Filter the DataFrame based on user selections
    if (
        selected_students == "All"
    ):  # don't need to filter by students, all are considered
        filtered_df = data[
            (data["course_id"].astype(str) == selected_course)
            & (data["module_id"].astype(str).isin(selected_modules))
        ]
    else:
        filtered_df = data[
            (data["course_id"].astype(str) == selected_course)
            & (data["student_id"].astype(str) == selected_students)
            & (data["module_id"].astype(str).isin(selected_modules))
        ]

    # Convert the filtered DataFrame to JSON serializable format
    filtered_data = filtered_df.to_json(date_format="iso", orient="split")

    return filtered_data


# Filter the data based on user selections
@app.callback(
    Output("module-specific-data", "data"),
    [
        Input("course-dropdown", "value"),
        Input("module-dropdown", "value"),
        Input("item-checkboxes", "value"),
    ],
)
def update_module_filtered_data(selected_course, selected_module, selected_items):
    """
    Returns a filtered dataset by selected course, selected students, selected modules and selected items

    Parameters:
        selected_course (str): Selected Course
        selected_module (str): Selected Modules
        selected_items (list): Selected Items

    Returns:
        filtered_data (json): filtered data for storage
    """

    filtered_df = data[
        (data["course_id"].astype(str) == selected_course)
        & (data["module_id"].astype(str) == selected_module)
        & (data["items_id"].astype(str).isin(selected_items))
    ]

    # Convert the filtered DataFrame to JSON serializable format
    filtered_data = filtered_df.to_json(date_format="iso", orient="split")

    return filtered_data


# Plot 3, Timeline plot
@app.callback(
    Output("plot3", "figure"),
    Output("export-button", "n_clicks", allow_duplicate=True),
    [
        Input("course-specific-data", "data"),
        Input("date-slider", "start_date"),
        Input("date-slider", "end_date"),
        Input("course-dropdown", "value"),
        Input("student-dropdown-modules-tab", "value"),
        Input("export-button", "n_clicks"),
        State("tabs", "value"),
    ],
    prevent_initial_call=True,
)
def update_timeline(
    filtered_data,
    start_date,
    end_date,
    course_selected,
    student_selected,
    n_clicks,
    active_tab,
):
    """
    Returns a lineplot of module completion by percentage of students.

    Parameters:
        filtered_data (json): filtered data
        start_date (str): Selected start date
        end_date (str): Selected end date
        course_selected (str): course_id
        student_selected (str): student_id
        n_clicks (int): button click none or 1
        active_tab ('str'): tab_id


    Returns:
        fig_3_json (json): JSON serializable format of plot
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

    # Initialize dicts
    module_dict = defaultdict(str)

    for _, row in filtered_df.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )

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

    # Plotting
    fig_3 = go.Figure()
    for i, (module, group) in enumerate(result_time.groupby("Module")):
        sorted_group = group.sort_values("Date")

        if len(sorted_group) == 1:
            fig_3.add_trace(
                go.Scatter(
                    x=sorted_group["Date"],
                    y=sorted_group["Percentage Completion"],
                    mode="markers",
                    name=module,
                    marker=dict(color=module_colors[module]),
                )
            )

        else:
            fig_3.add_trace(
                go.Scatter(
                    x=sorted_group["Date"],
                    y=sorted_group["Percentage Completion"],
                    mode="lines",
                    name=module,
                    line=dict(color=module_colors[module]),
                )
            )

    fig_3.update_layout(
        title={
            "text": f"Module completion timeline by {student_dict.get(student_selected)}",
            "font": {"size": title_font_size},
        },
        xaxis=dict(
            title="Date", tickangle=0, title_font=dict(size=axis_label_font_size)
        ),
        yaxis=dict(
            title="Percentage Completion", title_font=dict(size=axis_label_font_size)
        ),
        plot_bgcolor="rgba(240, 240, 240, 0.8)",  # Light gray background color
        xaxis_gridcolor="rgba(200, 200, 200, 0.2)",  # Faint gridlines
        yaxis_gridcolor="rgba(200, 200, 200, 0.2)",  # Faint gridlines
        margin=dict(l=50, r=50, t=50, b=50),  # Add margin for a border line
        paper_bgcolor="white",  # Set the background color of the entire plot
    )

    # Specify custom spacing between dates on the x-axis
    tick_dates = pd.date_range(start_date, end_date, freq="7D")
    tick_labels = [date.strftime("%Y-%m-%d") for date in tick_dates]
    fig_3.update_xaxes(tickvals=tick_dates, ticktext=tick_labels)

    # Convert the figure to a JSON serializable format
    fig_3_json = fig_3.to_dict()

    # Create the folder to save the image if not exists
    download_path = f"results/{course_dict.get(course_selected)}/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if n_clicks and active_tab == "view-modules":
        image_name = (
            f"Module completion timeline by {student_dict.get(student_selected)}.png"
        )
        pio.write_image(fig_3, "".join([download_path, image_name]))

    return fig_3_json, None


# Plot 2, Duration Bar Chart
@app.callback(
    Output("plot2", "figure"),
    Output("export-button", "n_clicks", allow_duplicate=True),
    [
        Input("course-specific-data", "data"),
        Input("course-dropdown", "value"),
        Input("student-dropdown-modules-tab", "value"),
        Input("export-button", "n_clicks"),
    ],
    State("tabs", "value"),
    prevent_initial_call=True,
)
def update_barchart_duration(
    filtered_data, course_selected, student_selected, n_clicks, active_tab
):
    """
    Returns a barchart of the aveerage days to completion of selected modules in the selected course

    Parameters:
        filtered_data (json): filtered data
        course_selected (str): course_id
        student_selected (str): student_id
        n_clicks (int): button click none or 1
        active_tab ('str'): tab_id


    Returns:
        fig_2_json (json): JSON serializable format of plot
    """

    # Handling edge case
    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    # filter the data by state = "completed"
    filtered_df = filtered_df[filtered_df.state == "completed"]

    # Ensure that the course has a unique start date
    assert (
        filtered_df["course_start_date"].unique().size == 1
    ), "More than one course start date found for this course"

    course_start_date = filtered_df["course_start_date"].unique()[0]

    if isinstance(course_start_date, str):
        course_start_date = datetime.datetime.strptime(
            course_start_date, "%Y-%m-%dT%H:%M:%SZ"
        )

    assert isinstance(course_start_date, datetime.datetime)

    # Convert 'completed_at' column to datetime
    filtered_df["completed_at"] = pd.to_datetime(
        filtered_df["completed_at"], format="mixed"
    )

    filtered_df = filtered_df.assign(
        duration=(filtered_df["completed_at"] - course_start_date).map(lambda x: x.days)
    )

    # We want to keep only one unique row per student, thereby there are no repetition for the same student
    filtered_df = filtered_df[
        ["module_id", "module_name", "state", "duration", "student_id"]
    ].drop_duplicates()
    filtered_df["module"] = filtered_df["module_id"].apply(
        lambda x: module_num.get(str(x))
    )

    # Calculate the mean duration for each module
    mean_duration_df = filtered_df.groupby("module")["duration"].mean().reset_index()

    # Sort the modules by the label
    sorted_modules = sorted(mean_duration_df["module"])

    # Create the bar chart using Plotly Express
    fig_2 = px.bar(
        mean_duration_df,
        x="duration",
        y="module",
        orientation="h",
        labels={"duration": "Average Duration (Days)", "module": "Module"},
        category_orders={"module": sorted_modules},
    )

    fig_2.update_layout(
        title={
            "text": f"Days to complete module by {student_dict.get(student_selected)}",
            "font": {"size": title_font_size},
        },
        xaxis_title_font=dict(
            size=axis_label_font_size
        ),  # Adjust the x-axis title font size
        yaxis_title_font=dict(
            size=axis_label_font_size
        ),  # Adjust the y-axis title font size
        plot_bgcolor="rgba(240, 240, 240, 0.8)",  # Light gray background color
        xaxis_gridcolor="rgba(200, 200, 200, 0.2)",  # Faint gridlines
        yaxis_gridcolor="rgba(200, 200, 200, 0.2)",  # Faint gridlines
        margin=dict(l=50, r=50, t=50, b=50),  # Add margin for a border line
        paper_bgcolor="white",  # Set the background color of the entire plot
    )

    # Customize the hover template
    hover_template = (
        "<b>%{y}</b><br>" + "Mean Duration: %{x:.2f} days<br>" + "<extra></extra>"
    )  # The <extra></extra> tag removes the "trace 0" label

    fig_2.update_traces(hovertemplate=hover_template)

    fig_2_json = fig_2.to_dict()

    # Create the folder to save the image if not exists
    download_path = f"results/{course_dict.get(course_selected)}/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if n_clicks and active_tab == "view-modules":
        image_name = (
            f"Days to complete module by {student_dict.get(student_selected)}.png"
        )
        pio.write_image(fig_2, "".join([download_path, image_name]))

    return fig_2_json, None


# Plot 1, Modules Barplot
@app.callback(
    Output("plot1", "figure"),
    Output("export-button", "n_clicks", allow_duplicate=True),
    [
        Input("course-specific-data", "data"),
        Input("status-radio", "value"),
        Input("course-dropdown", "value"),
        Input("student-dropdown-modules-tab", "value"),
        Input("export-button", "n_clicks"),
    ],
    State("tabs", "value"),
    prevent_initial_call=True,
)
def update_module_completion_barplot(
    filtered_data, value, course_selected, student_selected, n_clicks, active_tab
):
    """
    Returns a stacked horizontal barplot of percentage of student completion of selected modules

    Parameters:
        filtered_data (json): filtered data
        value (str): Selected module status
        course_selected (str): course_id
        student_selected (str): student_id
        n_clicks (int): button click none or 1
        active_tab ('str'): tab_id


    Returns:
        fig_1_json (json): JSON serializable format of plot
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

    # Melt the DataFrame to convert columns to rows
    melted_df = pd.melt(
        df_mod,
        id_vars="Module",
        value_vars=radio_selection,
        var_name="Status",
        value_name="Percentage Completion",
    )

    # Define the color mapping
    color_mapping = {
        module_status[len(module_status) - (i + 1)]: color_palette_2[i]
        for i in range(len(module_status))
    }

    # Create a horizontal bar chart using Plotly
    fig_1 = px.bar(
        melted_df,
        y="Module",
        x="Percentage Completion",
        color="Status",
        orientation="h",
        labels={"Percentage Completion": "Percentage Completion"},
        category_orders={"Module": sorted(melted_df["Module"].unique())},
        color_discrete_map=color_mapping,  # Set the color mapping
    )

    fig_1.update_layout(
        showlegend=True,  # Show the legend indicating the module status colors
        legend_title="Status",  # Customize the legend title,
        legend_traceorder="reversed",  # Reverse the order of the legend items
    )

    # Modify the plotly configuration to change the background color
    fig_1.update_layout(
        title={
            "text": f"Percentage completion for {student_dict.get(student_selected)}",
            "font": {"size": title_font_size},
        },
        xaxis=dict(title_font=dict(size=axis_label_font_size)),
        yaxis=dict(title_font=dict(size=axis_label_font_size)),
        xaxis_range=[0, 100],
        plot_bgcolor="rgba(240, 240, 240, 0.8)",
        xaxis_gridcolor="rgba(200, 200, 200, 0.2)",
        yaxis_gridcolor="rgba(200, 200, 200, 0.2)",
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor="white",
    )

    # Convert the figure to a JSON serializable format
    fig_1_json = fig_1.to_dict()

    # Create the folder to save the image if not exists
    download_path = f"results/{course_dict.get(course_selected)}/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if n_clicks and active_tab == "view-modules":
        image_name = (
            f"Percentage completion for {student_dict.get(student_selected)}.png"
        )
        pio.write_image(fig_1, "".join([download_path, image_name]))

    return fig_1_json, None


# Plot 4, Item Bar Chart
@app.callback(
    Output("plot4", "figure"),
    Output("export-button", "n_clicks", allow_duplicate=True),
    [
        Input("module-specific-data", "data"),
        Input("course-dropdown", "value"),
        Input("module-dropdown", "value"),
        Input("export-button", "n_clicks"),
    ],
    State("tabs", "value"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def update_item_completion_barplot(
    filtered_data, course_selected, module_selected, n_clicks, active_tab
):
    """
    Returns a barplot of percentage of students who completed the items

    Parameters:
        filtered_data (json): filtered data
        course_selected (str): course_id
        module_selected (str): module_id
        n_clicks (int): button click none or 1
        active_tab ('str'): tab_id


    Returns:
        fig_4_json (json): JSON serializable format of plot
    """
    # Handling edge case
    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    result = {}
    items = list(filtered_df.items_id.unique().astype(str))

    # Initialize dicts
    items_pos = defaultdict(str)

    for _, row in filtered_df.iterrows():
        items_pos[str(row["items_id"])] = f"Item {row['items_position']}:"

    # Drop the items where there is no item completion requirement
    items_todrop = []
    for item in items:
        temp_df = filtered_df[filtered_df.items_id.astype(str) == item]
        if all(temp_df.item_cp_req_type.isna()):
            items_todrop.append(item)
        else:
            continue

    filtered_df = filtered_df[~filtered_df.items_id.astype(str).isin(items_todrop)]

    for item in items:
        result[items_pos.get(item)] = round(
            get_item_completion_percentage(filtered_df, item) * 100, 2
        )

    df_mod = pd.DataFrame(list(result.items()), columns=["Items", "Percentage"])

    # Create the bar plot using Plotly
    fig_4 = go.Figure()

    fig_4.add_trace(go.Bar(y=df_mod["Items"], x=df_mod["Percentage"], orientation="h"))

    fig_4.update_layout(
        title=f"Percentage of completion of items in {module_dict.get(module_selected)}",
        xaxis_title="Percentage Completion",
        yaxis_title="Items",
        xaxis_range=[0, 100],
        showlegend=False,
        yaxis=dict(categoryorder="category descending"),
    )

    # Convert the figure to a JSON serializable format
    fig_4_json = fig_4.to_dict()

    # Create the folder to save the image if not exists
    download_path = f"results/{course_dict.get(course_selected)}/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if n_clicks and active_tab == "view-items":
        image_name = f"Percentage of completion of items in {module_dict.get(module_selected)}.png"
        pio.write_image(fig_4, "".join([download_path, image_name]))

    return fig_4_json, None


# Table Callback
@app.callback(
    Output("table-1", "data"),
    Output("table-1", "columns"),
    [
        Input("student-specific-data", "data"),
    ],
)
def update_student_table(filtered_data):
    """
    Returns a datatable with details of module, items, item types and item status

    Parameters:
        filtered_data (json): filtered data
    """

    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    filtered_df = filtered_df[
        ["module_name", "items_title", "items_type", "item_cp_req_completed"]
    ]
    filtered_df["item_cp_req_completed"] = filtered_df["item_cp_req_completed"].map(
        {1: "✅", 0: "❌", np.nan: "🔘"}
    )

    # Define custom column headings
    custom_column_names = {
        "module_name": "Module Name",
        "items_title": "Item Title",
        "items_type": "Item Type",
        "item_cp_req_completed": "Item Status",
    }

    column_name = [
        {
            "name": custom_column_names[col],
            "id": col,
            "selectable": True,
            "deletable": False,
        }
        for col in filtered_df.columns
    ]

    return filtered_df.to_dict("records"), column_name


# -----------------------------------------------------------------
# Layout

tools = dbc.Container(
    [
        dbc.Row(
            [html.H3("Dashboard Tools", className="text-center")], justify="center"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Select course"),
                        dcc.Dropdown(
                            id="course-dropdown",
                            placeholder="Select Course",
                            clearable=True,
                            options=course_options,  # list of dropdown
                            value=course_options[0]["value"],  # default value
                            style={"width": "100%", "fontsize": "1px"},
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        html.H5("Save Plots"),
                        dbc.Button(
                            "Download",
                            id="export-button",
                            color="primary",
                            className="mr-2",
                        ),
                    ],
                    width=1,
                ),
            ],
            justify="center",
            align="center",
        ),
    ],
    className="bg-light bg-gradient",
    style={
        "backgroundColor": "#F4F4F4",
        "padding": "10px 10px",
        "border-radius": "16px",
        "margin-bottom": "1rem",
        "border": "1px solid lightgray",
        "box-shadow": "1px 1px 5px 5px rgba(0, 0, 0.1, 0.5)",
    },
)

module_sidebar = dbc.Container(
    [
        html.H6("Select Modules "),
        dbc.Checklist(id="module-checkboxes"),
        html.Br(),
        html.Hr(),
        html.Br(),
        html.H6(
            "Select Module State",
        ),
        dcc.RadioItems(
            id="status-radio",
            options=[
                {
                    "label": " " + "All",
                    "value": "All",
                },
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
        html.Br(),
        html.Hr(),
        html.Br(),
        html.H6(
            "Select Students",
        ),
        dcc.Dropdown(
            id="student-dropdown-modules-tab",
            placeholder="Select Students",
            clearable=True,
            options=[],
            value="All",
            style={
                "width": "100%",
            },
        ),
        html.Br(),
        html.Hr(),
        html.Br(),
        html.H6(
            "Select Timeline",
        ),
        dcc.DatePickerRange(
            id="date-slider",
            min_date_allowed=min(pd.to_datetime(data["completed_at"])).date(),
            max_date_allowed=max(pd.to_datetime(data["completed_at"])).date(),
            start_date=min(pd.to_datetime(data["completed_at"])).date(),
            end_date=max(pd.to_datetime(data["completed_at"])).date(),
            clearable=True,
        ),
    ],
    style={
        "backgroundColor": "#F4F4F4",
        "padding": "10px 10px",
        "border-radius": "16px",
        "margin-bottom": "1rem",
        "border": "5px solid lightgray",
        "box-shadow": "0px 0px 0px 0px rgba(0, 0, 0.1, 0.5)",
    },
)

items_sidebar = dbc.Container(
    [
        html.H6(
            "Select One Module",
        ),
        dcc.Dropdown(
            id="module-dropdown",
            options=[],
            value="",
            style={
                "width": "100%",
                "fontsize": "1px",
            },
            clearable=True,
            placeholder="Select One Module",
        ),
        html.Br(),
        html.H6("Select Items "),
        dbc.Checklist(
            id="item-checkboxes",
        ),
    ],
    style={
        "backgroundColor": "#F4F4F4",
        "padding": "10px 10px",
        "border-radius": "16px",
        "margin-bottom": "1rem",
        "border": "5px solid lightgray",
        "box-shadow": "0px 0px 0px 0px rgba(0, 0, 0.1, 0.5)",
    },
)

student_sidebar = dbc.Container(
    [
        html.H6(
            "Select Students",
        ),
        dcc.Dropdown(
            id="student-dropdown-students-tab",
            options=[],
            value="All",
            style={
                "width": "100%",
                "fontsize": "1px",
            },
            clearable=True,
            placeholder="Select Students",
        ),
        html.Br(),
        html.Hr(),
        html.Br(),
        html.H6(
            "Item Status Legend",
        ),
        html.Label(
            "✅: Completed",
        ),
        html.Br(),
        html.Label(
            "❌: Incomplete",
        ),
        html.Br(),
        html.Label(
            "🔘: Not Started",
        ),
    ],
    style={
        "backgroundColor": "#F4F4F4",
        "padding": "10px 10px",
        "border-radius": "16px",
        "margin-bottom": "1rem",
        "border": "5px solid lightgray",
        "box-shadow": "0px 0px 0px 0px rgba(0, 0, 0.1, 0.5)",
    },
)

pop = dbc.Popover(
    [
        dbc.PopoverHeader("Tip", style=text_style),
        dbc.PopoverBody(
            "If needed, you can filter the columns. Type in the respective column cell that says 'filter data...'",
            style={"font-size": "16px"},
        ),
    ],
    body=True,
    target="table-1",
    trigger="hover",
    placement="auto",
    style={
        "width": "800px",
        "height": "150px",
        "border-radius": "10px",
        "padding": "5px",
        "overflow": "hidden",
        "background-color": "lightblue",
    },
)

app.layout = dbc.Container(
    fluid=True,
    children=[
        html.Div(
            children=[
                html.H1(
                    "Module Progress Dashboard",
                    style=heading_style,
                    className="bg-primary bg-opacity-75 text-white border rounded-pill text-center",
                ),
            ],
            style={"padding": "5px"},
        ),
        dbc.Row(
            [
                tools,
            ],
            className="m-3",  # Add spacing between rows
        ),
        dbc.Row(
            [
                dcc.Store(id="course-specific-data"),
                dcc.Store(id="module-specific-data"),
                dcc.Store(id="student-specific-data"),
                dcc.Tabs(
                    id="tabs",
                    value="view-modules",
                    children=[
                        dcc.Tab(
                            id="tab-1",
                            label="View Modules",
                            value="view-modules",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [module_sidebar],
                                            width=3,
                                            className="m-3",
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Row(
                                                    [
                                                        dcc.Graph(
                                                            id="plot1",
                                                            style={
                                                                "width": "100%",
                                                                "height": "300px",
                                                            },
                                                            className="shadow p-3 mb-5 bg-white rounded",
                                                        ),
                                                    ],
                                                ),
                                                dbc.Row(
                                                    [
                                                        dcc.Graph(
                                                            id="plot3",
                                                            style={
                                                                "width": "100%",
                                                                "height": "300px",
                                                            },
                                                            className="shadow p-3 mb-5 bg-white rounded",
                                                        ),
                                                    ],
                                                    className="m-3",
                                                ),
                                                dbc.Row(
                                                    [
                                                        dcc.Graph(
                                                            id="plot2",
                                                            style={
                                                                "width": "100%",
                                                                "height": "300px",
                                                            },
                                                            className="shadow p-3 mb-5 bg-white rounded",
                                                        ),
                                                    ],
                                                    className="m-3",
                                                ),
                                            ],
                                            width=7,
                                            className="m-3 border rounded shadow p-3 mb-5 bg-white rounded",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dcc.Tab(
                            id="tab-2",
                            label="View Items",
                            value="view-items",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                items_sidebar,
                                            ],
                                            width=3,
                                            className="m-3",
                                        ),
                                        dbc.Col(
                                            [
                                                dcc.Graph(
                                                    id="plot4",
                                                    style={
                                                        "width": "100%",
                                                        "height": "500px",
                                                    },
                                                    className="shadow p-3 mb-5 bg-white rounded",
                                                ),
                                            ],
                                            width=7,
                                            className="m-3",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dcc.Tab(
                            id="tab-3",
                            label="View Students",
                            value="view-students",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                student_sidebar,
                                            ],
                                            width=3,
                                        ),
                                        dbc.Col(
                                            [
                                                dash_table.DataTable(
                                                    id="table-1",
                                                    editable=False,
                                                    filter_action="native",
                                                    sort_action="native",
                                                    sort_mode="multi",
                                                    row_deletable=False,
                                                    selected_columns=[],
                                                    selected_rows=[],
                                                    # page_action="native",
                                                    # page_current=0,
                                                    # page_size=15, Optional to paginate the table
                                                    style_table={
                                                        "height": "600px",
                                                        "overflowY": "auto",
                                                        "border": "2px solid gray",
                                                        "border-radius": "10px",
                                                    },
                                                    style_cell={
                                                        "textAlign": "center",
                                                        "border": "1px solid gray",
                                                    },
                                                    style_header={
                                                        "backgroundColor": "lightgrey",
                                                        "fontWeight": "bold",
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            "if": {"row_index": "odd"},
                                                            "backgroundColor": "rgb(248, 248, 248)",
                                                        }
                                                    ],
                                                ),
                                                pop,
                                            ],
                                        ),
                                    ],
                                    className="m-3",
                                ),
                            ],
                        ),
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.P(
                                    "Attributions: Alison Myers, Ranjit Sundaramurthi",
                                    style={
                                        "font-size": "16px",
                                        "font-weight": "normal",
                                        "padding": "5px",
                                    },
                                    className="bg-secondary bg-gradient text-white text-center border rounded-pill",
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                html.P(
                                    "Learning Analytics: UBC Sauder School of Business",
                                    style={
                                        "font-size": "16px",
                                        "font-weight": "normal",
                                        "padding": "5px",
                                    },
                                    className="bg-secondary bg-gradient text-white text-center border rounded-pill",
                                )
                            ],
                        ),
                    ],
                    className="mb-3",  # Add spacing between rows
                ),
            ],
            className="mt-3",
        ),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)

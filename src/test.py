# imports
from dash import dash, html, dcc, Input, Output
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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

import kaleido
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
    module_num, module_dict, item_num, item_dict, student_dict = (
        defaultdict(str) for _ in range(5)
    )

    for _, row in df.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    # map the module id to a module number for labeling
    for i, k in enumerate(module_dict.keys()):
        module_num[k] = f"Module {i+1}:"

    for i, k in enumerate(item_dict.keys()):
        item_num[k] = f"Item {i+1}:"

    return module_num, module_dict, item_num, item_dict, student_dict


def get_sub_dicts(df):
    """
    df is data after being by course and selected modules.
    Creates and returns the dictionaries mapping ids to names,
    module name, item name and student name, in that order specifically
    """
    # Initialize dicts

    module_dict, item_num, item_dict, student_dict = (
        defaultdict(str) for _ in range(4)
    )

    for _, row in df.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        item_dict[str(row["items_id"])] = row["items_title"]
        student_dict[str(row["student_id"])] = row["student_name"]

    for i, k in enumerate(item_dict.keys()):
        item_num[k] = f"Item:{i+1}"

    return module_dict, item_num, item_dict, student_dict


def get_item_completion_percentage(df, item):
    """
    Returns the marked complete percentage of item in df
    df is dataframe after removal of items that do not have a specific completion requirement
    """
    # df is the filtered_data after selections
    df_item = df[df.items_id.astype(str) == item]

    # Ensure that df_item is not null
    if df_item.shape[0] == 0:
        return 0

    total_item_students = df_item.student_id.unique().size


    percentage = (
        df_item[df_item.item_cp_req_completed == 1.0].student_id.unique().size
        / total_item_students
    )
    return percentage


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

# # Make the mapping of any id to the corresponding names
# course_dict = defaultdict(str)
# for _, row in data.iterrows():
#     course_dict[str(row["course_id"])] = row["course_name"]


############################
# All accessible vairables #
############################

module_status = ["completed", "started", "unlocked", "locked"]

# Make the mapping of any id to the corresponding names
global course_dict
global module_dict
global item_dict
# global student_dict

course_dict, module_dict, item_dict = (defaultdict(str) for _ in range(3))

for _, row in data.iterrows():
    course_dict[str(row["course_id"])] = row["course_name"]
    module_dict[str(row["module_id"])] = row["module_name"]
    item_dict[str(row["items_id"])] = row["items_title"]
#    student_dict[str(row["student_id"])] = row["student_name"]

# Create nested defaultdicts with sets
nested_dict = defaultdict(lambda: defaultdict(dict))

# Create a dictionary to store the order of modules for each course
course_module_order = defaultdict(list)

# Iterate through the DataFrame to populate the nested dictionary and module order
for _, row in data.iterrows():
    course_id = str(row["course_id"])
    module_id = str(row["module_id"])
    items_id = str(row["items_id"])
    items_position = row["items_position"]

    nested_dict[course_id][module_id][items_id] = items_position

    # Store the order of modules for each course
    if module_id not in course_module_order[course_id]:
        course_module_order[course_id].append(module_id)

# Convert the nested defaultdict to a regular dictionary (if needed)
nested_dict = dict(nested_dict)


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
# Update module checklist
@app.callback(
    Output("module-checkboxes", "options"),
    Output("module-checkboxes", "value"),
    Input("course-dropdown", "value"),
)
def update_module_checklist(val):
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



    # Add the 'All' option at the beginning (Reconsider later)
    # module_options.insert(0, {"label": "All", "value": "All"})

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
    # Edge case, if no value selected in course-dropdown
    if selected_course is None or selected_module is None:
        item_options = [
            {
                "label": "Either Course or Module not selected",
                "value": "No Course selected",
            }
        ]
        def_value = item_options
        return item_options, def_value

    # filter by the course selected
    subset_data = data.copy()

    selected_course = remove_special_characters(course_dict[selected_course])

    subset_data = subset_data[
        (subset_data.course_name == selected_course)
        & (subset_data.module_id.astype(str) == selected_module)
    ]

    # Create dictionaries accordingly to selected_course
    # module_dict, item_num, item_dict, student_dict = get_sub_dicts(subset_data) # Imoprovement: get_sub_dicts can be only for gettin the item_num and item_dict

    # Initialize dicts
    items_pos = (defaultdict(str))
    items_id_name = (defaultdict(str))

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


    # define a global color map for the modules
    global item_colors
    item_colors = {items_pos[item_id]: color_palette_3[i]
        for item_id, i in zip(items_pos.keys(), np.arange(len(items_pos.keys())))}


    # Add the 'All' option at the beginning (Reconsider later)
    # item_options.insert(0, {"label": "All", "value": "All"})

    # default value, selects all the items in the checklist
    def_value = [item_options[i]["value"] for i in range(len(item_options))]
    return item_options, def_value


# Update module-dropdown options
@app.callback(
    Output("module-dropdown", "options"),
    Output("module-dropdown", "value"),
    Input("course-dropdown", "value"),
)
def update_module_dropdown(val):
    # Edge case, if no value selected in course-dropdown
    if val is None:
        module_options = [{"label": "No Course selected", "value": 0}]
        return module_options

    # filter by the course selected
    subset_data = data.copy()

    selected_course = remove_special_characters(course_dict[val])

    subset_data = subset_data[subset_data.course_name == selected_course]

    # Create dictionaries accordingly to selected_course
    # module_num, module_dict, item_num, item_dict, student_dict = get_dicts(subset_data)
    
    # Initialize dicts
    module_dict= (defaultdict(str))

    for _, row in subset_data.iterrows():
        module_dict[str(row["module_id"])] = re.sub(
            r"^Module\s+\d+:\s+", "", row["module_name"]
        )
        
    if val != None:
        module_options = [
            {"label": module_name, "value": module_id}
            for module_id, module_name in module_dict.items()
        ]

    # Commented out since All is not need for a single module dropdown selection
    # module_options.insert(0, {"label": "All", "value": "All"})

    return module_options, module_options[0]["value"]


# Update student-dropdown options
@app.callback(
    Output("student-dropdown", "options"),
    Input("course-dropdown", "value"),
)
def update_student_dropdown1(val):
    # Edge case, if no value selected in course-dropdown
    if val is None:
        student_options = [{"label": "No Course selected", "value": 0}]
        return student_options

    # filter by the course selected
    subset_data = data.copy()

    selected_course = remove_special_characters(course_dict[val])

    subset_data = subset_data[subset_data.course_name == selected_course]

    # Create dictionaries accordingly to selected_course
    # module_num, module_dict, item_num, item_dict, student_dict = get_dicts(subset_data)
    
    # Initialize dicts
    global student_dict
    student_dict= (defaultdict(str))

    for _, row in subset_data.iterrows():
        student_dict[str(row["student_id"])] = row["student_name"]   
    
    if val != None:
        student_options = [
            {"label": student_name, "value": student_id}
            for student_id, student_name in student_dict.items()
        ]

    # Add 'All' in student_dict
    student_dict['All'] = 'All'
        
    # Add the 'All' option at beginning of the list
    student_options.insert(0, {"label": "All", "value": "All"})

    return student_options


# filter the data based on user selections
@app.callback(
    Output("student-specific-data", "data"),
    [
        Input("course-dropdown", "value"),
        Input("student-dropdown", "value"),
    ],
)
def update_student_filtered_data(selected_course, selected_students):
    # Filter the DataFrame based on user selections
    if (
        selected_students == "All"
    ):  # don't need to filter by students, all are considered
        filtered_df = data[
            (data["course_id"].astype(str) == selected_course)
        ]
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
        Input("student-dropdown", "value"),
        Input("module-checkboxes", "value"),
    ],
)
def update_course_filtered_data(selected_course, selected_students, selected_modules):
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





# filter the data based on user selections
@app.callback(
    Output("module-specific-data", "data"),
    [
        Input("course-dropdown", "value"),
        Input("module-dropdown", "value"),
        Input("student-dropdown", "value"),
        Input("item-checkboxes", "value"),
    ],
)
def update_module_filtered_data(
    selected_course, selected_module, selected_students, selected_items
):
    # Filter the DataFrame based on user selections
    if (
        selected_students == "All"
    ):  # don't need to filter by students, all are considered
        filtered_df = data[
            (data["course_id"].astype(str) == selected_course)
            & (data["module_id"].astype(str) == selected_module)
            & (data["items_id"].astype(str).isin(selected_items))
        ]
    else:
        filtered_df = data[
            (data["course_id"].astype(str) == selected_course)
            & (data["module_id"].astype(str) == selected_module)
            & (data["student_id"].astype(str) == (selected_students))
            & (data["items_id"].astype(str).isin(selected_items))
        ]


    # Convert the filtered DataFrame to JSON serializable format
    filtered_data = filtered_df.to_json(date_format="iso", orient="split")

    return filtered_data


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


# Plot 3
@app.callback(
    Output("plot3", "figure"),
    [
        Input("course-specific-data", "data"),
        Input("date-slider", "start_date"),
        Input("date-slider", "end_date"),
        Input('course-dropdown', 'value'), 
        Input('student-dropdown', 'value'),
        Input("export-button", "n_clicks"),
        State('tabs', 'value')],
    prevent_initial_call=True,
)
def update_timeline(filtered_data, start_date, end_date, course_selected, student_selected, n_clicks, active_tab):
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
    # module_dict, item_num, item_dict, student_dict = get_sub_dicts(filtered_df)

    # Initialize dicts
    module_dict= (defaultdict(str))

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
        title=f"Module completion timeline for {course_dict.get(course_selected)} by {student_dict.get(student_selected)}",
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

    # Create the folder to save the image if not exists
    download_path = '../results/'
    if not os.path.exists(download_path):
        os.makedirs(download_path)    
    
    if n_clicks and active_tab == 'view-modules':
        image_name = f"Module completion timeline for {course_dict.get(course_selected)} by {student_dict.get(student_selected)}.png"
        pio.write_image(fig_1, "".join([download_path, image_name]))


    return fig_1_json


# Plot 2 Box plot - inactivated
# @app.callback(
#     Output("plot2", "figure"),
#     [Input("course-specific-data", "data"), Input("date-picker", "date")],
# )
# def update_box_plot(filtered_data, date_selected):
#     """
#     Returns a box plot of the completion duration of selected modules in the selected course
#     """
#     if isinstance(date_selected, str):
#         date_selected = datetime.datetime.strptime(date_selected, "%Y-%m-%d")

#     assert isinstance(date_selected, datetime.datetime)

#     if filtered_data is not None:
#         # Convert the filtered data back to DataFrame
#         filtered_df = pd.read_json(filtered_data, orient="split")

#     # Create dictionaries accordingly to selected_course
#     # module_num, module_dict, item_num, item_dict, student_dict = get_dicts(filtered_df)

#     # filter the data by state = "completed"
#     filtered_df = filtered_df[filtered_df.state == "completed"]

#     # Improvement: accept course start data as input
#     course_start_date = date_selected
#     course_start_time = datetime.time(0, 30)
#     course_combined_datetime = course_start_date.combine(
#         course_start_date, course_start_time
#     )

#     # compute the duration
#     # subset_data["duration"] = round(
#     #     (subset_data["completed_at"] - course_combined_datetime)
#     #     / np.timedelta64(1, "D"),
#     #     0,
#     # )
    
#     filtered_df = filtered_df.assign(duration = round((filtered_df["completed_at"] - course_combined_datetime)/ np.timedelta64(1, "D"),0,))
    
#     # Next we want to keep only one unique row per student, thereby there are no repetition for the same student
#     filtered_df = filtered_df[
#         ["module_id", "module_name", "state", "duration", "student_id"]
#     ].drop_duplicates()
#     filtered_df["module"] = filtered_df["module_id"].apply(
#         lambda x: module_num.get(str(x))
#     )
    

#     # Plot
#     # Create the box plot using Plotly Express
#     fig_2 = px.box(
#         filtered_df,
#         y="module",
#         x="duration",
#         points="all",
#         title="Boxplot of module completion duration (days)",
#         hover_data=["duration"],
#     )
#     fig_2.update_traces(boxpoints="all", boxmean=True, hoveron="points")

#     # Sort the y-axis in descending order
#     fig_2.update_yaxes(categoryorder="category descending")

#     # Customize the hover template
#     hover_template = "<b>%{y}</b><br>Duration: %{x} days<br><extra></extra>"  # The <extra></extra> tag removes the "trace 0" label

#     fig_2.update_traces(
#         hovertemplate=hover_template,
#         boxpoints="all",  # Show all points when hovering
#         #jitter=0.0,  # Adjust the jitter for better point visibility
#     )
    
#     fig_2_json = fig_2.to_dict()

#     return fig_2_json



# Plot 2 Bar Chart
@app.callback(
    Output("plot2", "figure"),
    [Input("course-specific-data", "data"), Input('course-dropdown', 'value'), Input('student-dropdown', 'value'), Input("export-button", "n_clicks")],
    State('tabs', 'value'),
    prevent_initial_call=True,
)
def update_barchart_duration(filtered_data, course_selected, student_selected, n_clicks, active_tab): #, date_selected):
    """
    Returns a barchart of the mean completion duration of selected modules in the selected course
    """
    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")


    # filter the data by state = "completed"
    filtered_df = filtered_df[filtered_df.state == "completed"]

    # Ensure that the course has a unique start date
    assert filtered_df['course_start_date'].unique().size == 1, 'More than one course start date found for this course'
    
    course_start_date = filtered_df['course_start_date'].unique()[0]
    
    if isinstance(course_start_date, str):
        course_start_date = datetime.datetime.strptime(course_start_date, "%d-%m-%Y %H:%M")

    assert isinstance(course_start_date, datetime.datetime)
    
    # Convert 'completed_at' column to datetime
    filtered_df['completed_at'] = pd.to_datetime(filtered_df['completed_at'], format = 'mixed')
    
    filtered_df = filtered_df.assign(duration = (filtered_df["completed_at"] - course_start_date).map(lambda x: x.days))
    
    # Next we want to keep only one unique row per student, thereby there are no repetition for the same student
    filtered_df = filtered_df[
        ["module_id", "module_name", "state", "duration", "student_id"]
    ].drop_duplicates()
    filtered_df["module"] = filtered_df["module_id"].apply(
        lambda x: module_num.get(str(x))
    )
    
    # Plot
    # Calculate the mean duration for each module
    mean_duration_df = filtered_df.groupby('module')['duration'].mean().reset_index()
    
    # sort the modules by the label
    sorted_modules = sorted(mean_duration_df['module'])
        
    # Create the bar chart using Plotly Express
    fig_2 = px.bar(mean_duration_df, x='duration', y='module', orientation='h', title=f'Days to complete module for course {course_dict.get(course_selected)} by {student_dict.get(student_selected)}',
                 labels={'duration': 'Mean Duration (Days)', 'module': 'Module'}, category_orders={"module": sorted_modules})

    # Customize the hover template
    hover_template = "<b>%{y}</b><br>" + \
                     "Mean Duration: %{x:.2f} days<br>" + \
                     "<extra></extra>"  # The <extra></extra> tag removes the "trace 0" label

    fig_2.update_traces(hovertemplate=hover_template)
    
    fig_2_json = fig_2.to_dict()

    # Create the folder to save the image if not exists
    download_path = '../results/'
    if not os.path.exists(download_path):
        os.makedirs(download_path)    
    
    if n_clicks and active_tab == 'view-modules':
        image_name = f'Days to complete module for course {course_dict.get(course_selected)} by {student_dict.get(student_selected)}.png'
        pio.write_image(fig_2, "".join([download_path, image_name]))


    return fig_2_json




# Plot 1 and Caption
@app.callback(
    Output("plot1", "figure"),
    [Input("course-specific-data", "data"), Input("status-radio", "value"), Input('course-dropdown', 'value'), Input('student-dropdown', 'value'), Input("export-button", "n_clicks")],
    State('tabs', 'value'),
    prevent_initial_call=True,
)
def update_module_completion_barplot(filtered_data, value, course_selected, student_selected, n_clicks, active_tab):
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
    # module_dict, item_num, item_dict, student_dict = get_sub_dicts(filtered_df)

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

    # CHECKing: Remove later is not necessary: Filter out any rows where "Module" is None
    # melted_df = melted_df.dropna(subset=["Module"])

    # Define the color mapping
    color_mapping = {
        module_status[len(module_status)-(i+1)]: color_palette_2[i] for i in range(len(module_status))
    }

    # Create a horizontal bar chart using Plotly
    fig_3 = px.bar(
        melted_df,
        y="Module",
        x="Percentage Completion",
        color="Status",
        orientation="h",
        labels={"Percentage Completion": "Percentage Completion (%)"},
        title=f"Percentage of completion of {course_dict.get(course_selected)} for {student_dict.get(student_selected)}",
        category_orders={"Module": sorted(melted_df["Module"].unique())},
        color_discrete_map=color_mapping,  # Set the color mapping
    )

    fig_3.update_layout(
        showlegend=True,  # Show the legend indicating the module status colors
        legend_title="Status",  # Customize the legend title,
        legend_traceorder="reversed",  # Reverse the order of the legend items
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

    # Create the folder to save the image if not exists
    download_path = '../results/'
    if not os.path.exists(download_path):
        os.makedirs(download_path)    
    
    if n_clicks and active_tab == 'view-modules':
        image_name = f"Percentage of completion of {course_dict.get(course_selected)} for {student_dict.get(student_selected)}.png"
        pio.write_image(fig_3, "".join([download_path, image_name]))


    return fig_3_json


# Plot 4
@app.callback(
    Output("plot4", "figure"),
    [Input("module-specific-data", "data"), Input('course-dropdown', 'value'), Input('student-dropdown', 'value'), Input('module-dropdown', 'value'), Input("export-button", "n_clicks")],
    State('tabs', 'value'),
    prevent_initial_call=True,
)
def update_item_completion_barplot(filtered_data, course_selected, student_selected, module_selected, n_clicks, active_tab):
    """
    Plots a barplot of items and the percentage of students the completed them
    """
    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")

    result = {}
    items = list(filtered_df.items_id.unique().astype(str))

    # Create dictionaries accordingly to selected_course and selected module
    # module_dict, item_num, item_dict, student_dict = get_sub_dicts(filtered_df)

    # Initialize dicts
    items_pos = (defaultdict(str))

    for _, row in filtered_df.iterrows():
        items_pos[str(row["items_id"])] = f"Item {row['items_position']}:"   


    
    # drop the items where there is no item completion requirement
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


    # Each row in the filtered_df for a given student is a unique item for that student
    # In the case that all the students are selected in the dropdown,
    # we have to provide the percentage completion of items for all students together
    # there will be duplicate items id, since each item will appear under multiple students
    # thus I am not doing filtering the dataframe with unique item ids.

    # Create the bar plot using Plotly
    fig_4 = go.Figure()

    fig_4.add_trace(go.Bar(y=df_mod["Items"], x=df_mod["Percentage"], orientation="h"))

    fig_4.update_layout(
        title=f"Percentage of completion of items in {module_dict.get(module_selected)} under {course_dict.get(course_selected)} for {student_dict.get(student_selected)}",
        xaxis_title="Percentage Completion",
        yaxis_title="Item",
        xaxis_range=[0, 100],
        showlegend=False,
        yaxis=dict(categoryorder="category descending"),
    )

    # Convert the figure to a JSON serializable format
    fig_4_json = fig_4.to_dict()
    
    # Create the folder to save the image if not exists
    download_path = '../results/'
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    if n_clicks and active_tab == 'view-items':
        image_name = f"Percentage of completion of items in {module_dict.get(module_selected)} under {course_dict.get(course_selected)} for {student_dict.get(student_selected)}.png"
        pio.write_image(fig_4, "".join([download_path, image_name]))

    return fig_4_json



# table callback
# Plot 4
@app.callback(
    Output("table-1", "data"),
    Output("table-1", "columns"),
    [Input("student-specific-data", "data"),],
)
def update_student_table(filtered_data):

    if filtered_data is not None:
        # Convert the filtered data back to DataFrame
        filtered_df = pd.read_json(filtered_data, orient="split")
    
    filtered_df = filtered_df[['module_name', 'items_title', 'items_type', 'item_cp_req_completed']]
    
    filtered_df['item_cp_req_completed'] = filtered_df['item_cp_req_completed'].map({1: 'Completed', 0: 'Incomplete', '': 'Not Required'}).astype('str')
    column_name = [{'name': col, 'id': col} for col in filtered_df.columns]
    
    return filtered_df.to_dict('records'), column_name

    
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
                    "Dashboard filters ",
                    style=text_style,
                )
            ],
        ),
        dbc.Row(
            [
                html.Div(
                    [
                        html.Label(
                            "Select Course",
                            style=text_style,
                        ),
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
                        html.Label(
                            "Select Students",
                            style=text_style,
                        ),
                        dcc.Dropdown(
                            id="student-dropdown",
                            options=[],
                            value="All",
                            style={
                                "width": "250px",
                                "fontsize": "1px",
                            },
                        ),
                    ],
                    style={
                        "width": "35%",
                        "display": "inline-block",
                    },
                ),
                html.Div(
                    [
                        html.Label(
                            "Save current plots",
                            style=text_style,
                        ),
                        html.Br(),
                        dbc.Button(
                            "Download",
                            id="export-button",
                            color="primary",
                            className="mr-2",
                        ),
                    ],
                    style={"width": "30%", "display": "inline-block"},
                ), html.Div(id='save-message')
            ],
            className="mb-3",  # Add spacing between rows
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
                            value='view-modules',
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                # html.Br(),
                                                # html.Label(
                                                #     "Select Course Start Date",
                                                #     style=text_style,
                                                # ),
                                                # dcc.DatePickerSingle(
                                                #     id="date-picker",
                                                #     date="2023-01-01",  # Set the initial date to today's date
                                                #     max_date_allowed=max(
                                                #         pd.to_datetime(
                                                #             data["completed_at"]
                                                #         )
                                                #     ).date(),
                                                #     display_format="YYYY-MM-DD",  # Specify the format in which the date will be displayed
                                                #     style={
                                                #         "marginLeft": "20px"  # Add 20px space to the left of the DatePickerSingle box
                                                #     },
                                                # ),
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
                                                        {
                                                            "label": " " + "All",
                                                            "value": "All",
                                                        },
                                                        *(
                                                            {
                                                                "label": " "
                                                                + f"{module_status[i]}",
                                                                "value": f"{module_status[i]}",
                                                            }
                                                            for i in range(
                                                                len(module_status)
                                                            )
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
                                                        pd.to_datetime(
                                                            data["completed_at"]
                                                        )
                                                    ).date(),
                                                    max_date_allowed=max(
                                                        pd.to_datetime(
                                                            data["completed_at"]
                                                        )
                                                    ).date(),
                                                    start_date=min(
                                                        pd.to_datetime(
                                                            data["completed_at"]
                                                        )
                                                    ).date(),
                                                    end_date=max(
                                                        pd.to_datetime(
                                                            data["completed_at"]
                                                        )
                                                    ).date(),
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
                            ],
                        ),
                        dcc.Tab(
                            id="tab-2",
                            label="View Items",
                            value='view-items',
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Br(),
                                                html.Label(
                                                    "Select One Module",
                                                    style=text_style,
                                                ),
                                                html.Br(),
                                                html.Div(
                                                    [
                                                        dcc.Dropdown(
                                                            id="module-dropdown",
                                                            options=[],
                                                            value="",
                                                            style={
                                                                "width": "250px",
                                                                "fontsize": "1px",
                                                            },
                                                        ),
                                                    ],
                                                    style={
                                                        "width": "35%",
                                                        "display": "inline-block",
                                                    },
                                                ),
                                                html.Br(),
                                                html.Label(
                                                    "Select Items ",
                                                    style=text_style,
                                                ),
                                                dbc.Checklist(
                                                    id="item-checkboxes",
                                                    #    options=[],  # default empty checklist
                                                    #    value="", # default selected value
                                                ),
                                            ],
                                            width=3,
                                        ),
                                        dbc.Col(
                                            [
                                                dcc.Graph(
                                                    id="plot4",
                                                    style={
                                                        "width": "80%",
                                                        "height": "600px",
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
                                ),
                                # dbc.Row(
                                #     [
                                #         dbc.Col(
                                #             [],
                                #             width=3,
                                #         ),
                                #         dbc.Col(
                                #             [
                                #                 dcc.Graph(
                                #                     id="plot6",
                                #                     style={
                                #                         "width": "100%",
                                #                         "height": "300px",
                                #                         "display": "inline-block",
                                #                         "border": "2px solid #ccc",
                                #                         "border-radius": "5px",
                                #                         "padding": "10px",
                                #                     },
                                #                 )
                                #             ],
                                #             width=9,
                                #         ),
                                #     ]
                                # ),
                            ],
                        ),
                        dcc.Tab(
                            id="tab-3",
                            label="View Students",
                            value='view-students',
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                html.Br(),
                                html.Label(
                                    "Student-wise Table",
                                    style=text_style,
                                ),
                                dash_table.DataTable(
                                    id='table-1',
                                    style_table={'height': '600px', 'overflowY': 'auto'},
                                    style_cell={'textAlign': 'center'},
                                    style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                                    style_data_conditional=[{
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 248, 248)'
                                    }],
                                )
                            ],
                        ),
                    ],
                ),
            ],
            className="mb-3",  # Add spacing between rows
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
            ],
            className="mb-3",  # Add spacing between rows
        ),
    ],
    className="mt-3",
)


if __name__ == "__main__":
    app.run_server(debug=True)

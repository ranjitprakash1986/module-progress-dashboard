# Module Progress Dashboard
>
> Authors: Ranjit Sundaramurthi, UBC
> Reviewers: Alison Myers, UBC

## About

An open-source Dashboard to visualize the student progress on courses. The intended stakeholders are administrators/instructors who are interested in tracking the status of students' progress on courses taught through the Canvas platform.

## Objective

The Dashboard enables the users to draw immediate insights into the status at different granular levels. The data source is downloaded using [module-progress](https://github.com/saud-learning-services/module-progress) scripts to interact with the [Canvas LMS REST API](https://canvas.instructure.com/doc/api/index.html). Each general structure of the data is as follows, Each instructor might teach multiple courses. Each course in comprised of several modules which in turn have several items. These items may be of different types - Page, Discussion, Video, Quiz etc. A module is said to be completed for a specific student when he/she has completed the designated required items underneath it. Note that depending on the item type, the requirement may be different and often the item might be completely optional.

The Dashboard provides the users the following insights:

* Percentage of student completion of modules within a course.
* Average completion time (days) for modules within a course.
* Percentage completion progression over time based on user defined time period selection.
* Percentage of student completion of required items within a module.
* Student-wise review of module and items for a selected course.

## Layout

The Dashboard is comprised of two tabs to segment into two distinct sections. The first tab provides the user with Course specific information at the module hierarchy level. The second tab provides the user with Course and Module specific information at the item hierarchy level.

The top of the Dashboard has two overall filters: by Course and by Student. By default, the first Course (alphabetically) and All students are selected.

![Dashboard_tab1](/img/view-modules-tab.PNG)
The sidebar on the left enables the user to single, all or multiple modules that are present within the selected course.

For the selecte modules, the visualization are showcases a lineplot of the student percentage completion over time. It also shows a stacked barplot of the statuses: 'locked', 'unlocked', 'started' and 'completed'. The bottom half presents a datable with student counts. A box plot presenting the time to complete each module is planned to provide insights on modules that might be time consuming/challenging.

Note that when a specific Student is selected in the overall filter, the visualization are dynamically changes to a scatter plot (as student percentage completion is longer a reasonable computation). The box plot is planned to be retained to show completion time as a separate scatter plot as well.

![Dashboard_tab2](/img/view-items-tab.PNG)
The second tab of the Dashboard contains a different sidebar. This sidebar compels the user to select a specific module within the already selected combination of course and student filters. The selection of the module, activates and populates the items checklist. By default 'All' items are selected. The user is allowed to select 'All', single or multiple items.

![Dashboard_tab2](/img/view-students-tab.PNG)
The visualization area showcases a barplot of the count of types of items under the selected module. Specifically for items that are mandatory, the student percentage completion is depicted as a stacked barplot. he bottom half presents a datable with student counts. Since items completion are not tracked by a timestamp in the dataset, average completion time of items cannot be visualized.

As before, when a specific Student is selected in the overall filter, the visualization dynamically changes to a scatter plot (as student percentage completion is longer a reasonable computation).

The bottom of the Dashboard contains attributions, source, assumptions and summary.

## Data-Source

The current data is sourced using the [module-progress](https://github.com/saud-learning-services/module-progress) python scripts. It downloads the necessary fields required for the dashboard from the Canvas LMS API.
(OR)
Alternatively, data could be downloaded using an equivalent javascript on Tampermonkey to enable extraction of the specific fields through the Canvas LMS API.

## Combining with [module-progress](https://github.com/saud-learning-services/module-progress)

This dashboard can be used independent of the [module-progress](https://github.com/saud-learning-services/module-progress) repository as mentioned in the Usage section below.

An option going forward is to combine the two repositories into a singe repository. This can be done by making transferring the `app.py` source code and updating the relative paths for the source data.

## Usage

### Setup and launch Dashboard

* Clone [this](https://github.com/ranjitprakash1986/module-progress-dashboard) Github repository

```bash
git clone https://github.com/ranjitprakash1986/module-progress-dashboard.git
```

* Navigate to the Github repository

```bash
cd module-progress-dashboard
```

* create the environment using the following command.

```bash
conda env create -f environment.yaml
```

* Activate the environment (by default the environment is named, dashboard)

```bash
conda activate module_progress_dashboard
```

* Paste the data you want to visualize in csv format into the `data` folder.
Note that by default, a sample data is present for the demonstration of the visualization. To view the data of your interest, please replace the sample data with the data downloaded by running the [module-progress](https://github.com/saud-learning-services/module-progress).

* Launch the dashboard

```bash
python src/app.py
```

This will launch the dashboard in your default interent browser at the localhost virtual server. This will be displayed on your terminal and will be of the form `http://127.0.0.1.xxxx`. If your internet browser does not launch automatically, open it and copy/paste the displayed location on your terminal in the address bar and press enter.

Now you can interact with the dashboard in the browser to draw insights from your data.

### Saving images

Use the filters on the dashboard to get the specific visualizations you are interested in. Then use the Export button to download the visualizations in the currently active tab to the `results` folder.

## Data Privacy

To adhere to the FIPPA regulations and protect privacy of data

* Do not upload your data to github

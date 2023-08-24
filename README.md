# Module Progress Dashboard
>
> Authors: Ranjit Sundaramurthi, UBC
> Reviewers: Alison Myers, UBC

## About

An open-source Dashboard to visualize the student progress on courses. The intended stakeholders are administrators/instructors who are interested in tracking the status of students' progress on courses taught through the Canvas platform. The Dashboard is designed to visualize the insights one course at a time.

## Objective

The Dashboard enables the users to draw immediate insights into the course progression status at different granular levels. The data source is downloaded using [module-progress](https://github.com/saud-learning-services/module-progress) scripts to interact with the [Canvas LMS REST API](https://canvas.instructure.com/doc/api/index.html). The general structure of the data is as follows. Each instructor might teach multiple courses. Each course in comprised of several modules which in turn have several items. These items may be of different types - Page, Discussion, Video, Quiz etc. A module is said to be completed for a specific student when he/she has completed the designated required items underneath it. Note that depending on the item type, the requirement may be different and often an item might be completely optional.

The Dashboard provides the users the following insights:

* Percentage of student completion of modules within a course.
* Average completion time (days) for modules within a course.
* Percentage completion progression over time based on user defined time period selection.
* Percentage of student completion of required items within a module.
* Student-wise review of module and items for a selected course.

## Layout

The Dashboard has 'tools' at the top which are applicable to the entire application. One of the  tools is a dropdown to enable the user to select the specific course for which the visualizations is intended. The other tool is a button to download the currently displayed plots onto the users local results folder. More information on saving the plots can be seen a separate section below.  

Below the tools are three Tabs that provide the user flexibility to view the data at different hierarchy levels. The first tab displays the course specific information at the module hierarchy level. The second tab displays the course and module specific information at the item hierarchy level. The second tab displays the course and student specific information in a table.

### View Modules Tab
![Dashboard_tab1](/img/layout/view-modules-tab.jpg)
The sidebar on the left enables the user to select single, all or multiple modules that are present within the selected course. The user can also filter the status of the module using the radio buttons provided below. The user can also select "all" or specific students from a dropdown. The default is set to "All" for these filters. Finally, a timeline selection enables the user to specify the time period for the lineplot visualization. This is set of the minimum and maximum completion dates for any module within the selected course. 

For the selected filters, the visualization shows a stacked barplot of the statuses: 'locked', 'unlocked', 'started' and 'completed'. This plot conveys the percentage of students in each status of a module. Below that is a lineplot of the percentage of students completion of each module over time. The last plot shows the average duration of time (days) by the students to complete a module. Please note the duration is shown only for the 'completed' status of the modules.

![Dashboard_tab2](/img/layout/view-items-tab.jpg)
The second tab of the Dashboard contains a different sidebar. This sidebar allows the user to select a specific module within the already selected course. The selection of the module, activates and populates the items checklist. By default 'All' items are selected. The user is allowed to select 'All', single or multiple items.

For the selected filters the visualization shows a horizontal barplot of the percentage of student who completed the mandatory requirements within the selected module. Please note that the percentage is computed only for the mandatory items. The optional items are eliminated from consideration. 

![Dashboard_tab2](/img/layout/view-students-tab.jpg)
The third tab of the Dashboard contains a different sidebar. This sidebar allows the user to select a specific student within the already selected course.

The visualization area showcases a dashtable with the selected students' details. The table provide information at the Item level and displays the status of each item for the specific student. Underneath each column header, there is a cell wherein the user can filter and search for a specific module, item title and item type. Currently there is no filtering available for the item status.

The bottom of the Dashboard contains attributions.

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

Use the filters on the dashboard to get the specific visualizations you are interested in. Then use the Export button to download the visualizations in the currently active tab to the `results` folder. The results folder will automatically place the images into the respective course folder, depending on the course selected on the dashboard.

## Data Privacy

To adhere to the FIPPA regulations and protect privacy of data

* Do not upload your data to github

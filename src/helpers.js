const axios = require('axios');
const fs = require('fs');
const path = require('path');

function createDictFromObject(theobj, list_of_attributes) {
    function getAttributeIfAvailable(theobj, attrname) {
        if (theobj.hasOwnProperty(attrname)) {
            return { [attrname]: theobj[attrname] };
        } else {
            return { [attrname]: null };
        }
    }

    const mydict = {};
    list_of_attributes.forEach(i => {
        mydict = { ...mydict, ...getAttributeIfAvailable(theobj, i) };
    });
    return mydict;
}

async function getModules(course) {
    console.log("Getting Module Information ...");
    try {
        const response = await axios.get(`https://canvas.api/courses/${course.id}/modules`);
        const modules = response.data;
        const attrs = [
            "id",
            "name",
            "position",
            "unlock_at",
            "require_sequential_progress",
            "another_item",
            "publish_final_grade",
            "prerequisite_module_ids",
            "published",
            "items_count",
            "items_url",
            "items",
            "course_id"
        ];

        const modulesDict = modules.map(m => createDictFromObject(m, attrs));
        const modulesDataFrame = modulesDict.map(m => ({
            module_id: m.id,
            module_name: m.name,
            module_position: m.position
        }));

        return modulesDataFrame;
    } catch (error) {
        throw new Error(`Unable to get modules for course: ${course.name}`);
    }
}

function getItems(modules_df, cname) {
    console.log("Getting item information ...");
    try {
        const expanded_items = listToDataFrame(
            modules_df.map(m => ({
                module_id: m.module_id,
                module_name: m.module_name,
                course_id: m.course_id,
                items: m.items
            })),
            "items"
        );

        let items_df = dictToColumns(expanded_items, "items", "items_");

        items_df = dictToColumns(
            items_df,
            "items_completion_requirement",
            "items_completion_req_"
        );

        return items_df;
    } catch (error) {
        throw new Error(
            `Unable to expand module items for "${cname}." Please ensure all modules have items`
        );
    }
}

// Helper functions need to be defined here...

const axios = require('axios');
const fs = require('fs');
const path = require('path');

function getStudentModuleStatus(course) {
    console.log("Getting Module Status for students ...");
    const students_df = getStudents(course);
    const enrollments_df = getEnrollments(course);

    console.log(`Getting student module info for ${course.name}`);
    const student_module_status = [];

    const num_rows = students_df.length;
    for (let i = 0; i < num_rows; i++) {
        const row = students_df[i];
        const sid = row.id;
        const student_data = getStudentModules(course, sid);
        const attrs = [
            "id",
            "name",
            "position",
            "unlock_at",
            "require_sequential_progress",
            "publish_final_grade",
            "prerequisite_module_ids",
            "state",
            "completed_at",
            "items_count",
            "items_url",
            "items",
            "course_id"
        ];

        const student_rows_dict = student_data.map(m => createDictFromObject(m, attrs));
        const student_rows = student_rows_dict.map(m => {
            return {
                ...m,
                student_id: sid.toString(),
                sis_user_id: row.sis_user_id,
                student_name: row.name,
                sortable_student_name: row.sortable_name
            };
        });
        student_module_status.push(...student_rows);
    }

    const student_module_status_with_enrollment_date = student_module_status.map(row => {
        const enrollment = enrollments_df.find(enrollment => enrollment.user_id === row.student_id);
        return {
            ...row,
            enrollment_date: enrollment ? enrollment.created_at : null
        };
    });

    return student_module_status_with_enrollment_date;
}

// Helper functions need to be defined here...

const axios = require('axios');
const fs = require('fs');
const path = require('path');

function getStudentItemsStatus(course, module_status) {
    try {
        const expanded_items = listToDataFrame(module_status, "items");
    } catch (error) {
        throw new Error("Course has no items completed by students");
    }

    const expanded_items_cols = dictToColumns(expanded_items, "items", "items_");
    const student_items_status = dictToColumns(
        expanded_items_cols,
        "items_completion_requirement",
        "item_cp_req_"
    ).map(row => {
        return {
            ...row,
            course_id: course.id,
            course_name: course.name
        };
    });

    const items_status_list = student_items_status.map(row => row.completed_at);
    const cleaned = items_status_list.map(__cleanDatetimeValue);
    student_items_status.forEach((row, index) => {
        row.completed_at = cleaned[index];
    });

    const datesSet = new Set(student_items_status.map(row => row.completed_at));
    const dates = Array.from(datesSet).filter(date => date !== null);

    console.log("Max Date:");
    console.log(new Date(Math.max(...dates)).toISOString());

    return student_items_status.map(row => {
        return {
            completed_at: row.completed_at,
            course_id: row.course_id,
            module_id: row.module_id,
            items_count: row.items_count,
            module_name: row.module_name,
            module_position: row.module_position,
            state: row.state,
            unlock_at: row.unlock_at,
            student_id: row.student_id,
            student_name: row.student_name,
            items_id: row.items_id,
            items_title: row.items_title,
            items_position: row.items_position,
            items_indent: row.items_indent,
            items_type: row.items_type,
            items_module_id: row.items_module_id,
            item_cp_req_type: row.item_cp_req_type,
            item_cp_req_completed: row.item_cp_req_completed,
            course_name: row.course_name
        };
    });
}

// Helper functions need to be defined here...
const fs = require('fs');
const path = require('path');

function cleanDatetimeValue(datetimeString) {
    if (datetimeString === null) {
        return datetimeString;
    }

    if (typeof datetimeString === 'string') {
        let x = datetimeString.replace("T", " ");
        return x.replace("Z", "");
    }

    throw new TypeError("Expected datetime_string to be of type string (or null)");
}

function writeDataDirectory(dataframes, cid) {
    const coursePath = makeOutputDir(cid);
    for (const [name, dataframe] of Object.entries(dataframes)) {
        const filePath = path.join(coursePath, `${name}.csv`);
        fs.writeFileSync(filePath, dataframe.toCSV(), 'utf8');
    }
}

function clearDataDirectory() {
    const root = path.dirname(__filename).slice(0, -4);
    const dataPath = path.join(root, 'data');

    fs.readdirSync(dataPath).forEach(subdir => {
        const subdirPath = path.join(dataPath, subdir);
        if (
            subdir !== "Tableau" &&
            subdir !== ".gitkeep" &&
            subdir !== ".DS_Store"
        ) {
            fs.rmdirSync(subdirPath, { recursive: true });
        }
    });
}

// Helper functions need to be defined here...


const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function writeTableauDirectory(listOfDfs) {
    const tableauPath = makeOutputDir("Tableau");
    const union = listOfDfs.reduce((result, df) => result.concat(df), []);
    const moduleDataOutputPath = path.join(tableauPath, "module_data.csv");
    fs.writeFileSync(moduleDataOutputPath, union.toCSV(), 'utf8');

    const root = path.dirname(__filename).slice(0, -4);

    // Copy the course_entitlements.csv into the Tableau folder
    const src = path.join(root, "course_entitlements.csv");
    const dst = path.join(root, "data", "Tableau", "course_entitlements.csv");
    fs.copyFileSync(src, dst);

    const currentDt = new Date();
    const dirName = currentDt.toISOString().replace(/:/g, "-");
    const archiveDst = path.join(root, "archive", dirName);
    const archivePath = path.join(root, "archive", dirName + ".zip");

    spawnSync('zip', ['-r', archivePath, dirName], { cwd: path.dirname(archiveDst) });

    outputStatusTable(tableauPath);
}

function outputStatusTable(tableauPath) {
    const currentDt = new Date();
    const cols = ["Course Id", "Course Name", "Status", "Message", "Data Updated On"];
    const data = [];

    for (const [cid, info] of Object.entries(settings.status)) {
        const row = [cid, info.cname, info.status, info.message, currentDt.toISOString()];
        data.push(row);
    }

    const statusLogPath = path.join(settings.ROOT_DIR, "status_log", `${currentDt.toISOString()}.csv`);
    fs.writeFileSync(statusLogPath, data.map(row => row.join(',')).join('\n'), 'utf8');

    const statusPath = path.join(tableauPath, "status.csv");
    fs.writeFileSync(statusPath, data.map(row => row.join(',')).join('\n'), 'utf8');
}

function logFailure(cid, msg) {
    settings.status[cid].status = "Failed";
    settings.status[cid].message = msg;
}


const axios = require('axios'); // You may need an HTTP library like Axios to make API requests
const settings = require('./settings'); // You need to import your settings module

function logSuccess(cid) {
    settings.status[cid].status = "Success";
    settings.status[cid].message = "Course folder has been created in data directory";
}

function getStudents(course) {
    const students = course.getUsers({
        include: ["test_student", "email"],
        enrollment_type: ["student"],
        per_page: 50
    });

    const attrs = [
        "id",
        "name",
        "created_at",
        "sortable_name",
        "short_name",
        "sis_user_id",
        "integration_id",
        "login_id",
        "pronouns"
    ];

    const studentsData = students.map(s => createDictFromObject(s, attrs));
    const studentsDF = createDataFrame(studentsData);
    return studentsDF;
}

function getEnrollments(course) {
    const enrollments = course.getEnrollments({
        enrollment_type: ["student"],
        per_page: 50
    });

    const attrs = [
        "created_at",
        "user_id"
    ];

    const enrollmentData = enrollments.map(e => createDictFromObject(e, attrs));
    const enrollmentsDF = createDataFrame(enrollmentData);
    enrollmentsDF['user_id'] = enrollmentsDF['user_id'].map(String);
    return enrollmentsDF;
}

// Helper function to create a dictionary from object attributes
function createDictFromObject(obj, attributes) {
    const result = {};
    for (const attr of attributes) {
        if (obj.hasOwnProperty(attr)) {
            result[attr] = obj[attr];
        } else {
            result[attr] = null;
        }
    }
    return result;
}

// You need to implement the createDataFrame function using a suitable library
// For example, if you're using Node.js, you might use a library like 'pandas-js'
// or 'dataframe-js' to create dataframes from arrays of objects.

// Example usage of axios for API requests
async function makeApiRequest(url, params) {
    try {
        const response = await axios.get(url, { params });
        return response.data;
    } catch (error) {
        console.error("API request failed:", error);
        return null;
    }
}

// Usage
const course = /* Initialize your course object */;
const studentsDF = getStudents(course);
const enrollmentsDF = getEnrollments(course);



const fs = require('fs');
const path = require('path');

function makeOutputDir(name) {
    const root = path.dirname(path.resolve(__filename)) + '/../';
    const directoryPath = path.join(root, 'data', name);

    if (!fs.existsSync(directoryPath)) {
        fs.mkdirSync(directoryPath, { recursive: true });
    }

    return directoryPath;
}

// Usage
const dirName = 'yourDirectoryName';
const outputDir = makeOutputDir(dirName);
console.log('Output directory:', outputDir);


function dictToColumns(dataframe, colToExpand, expandName) {
    dataframe[colToExpand] = dataframe[colToExpand].map(allDictToStr);
    const originalDF = dataframe.drop([colToExpand], axis = 1);
    const extendedDF = dataframe[colToExpand].map((entry) =>
        entry.reduce((acc, val, index) => {
            acc[expandName + index] = val;
            return acc;
        }, {})
    );
    const extendedDFColumns = extendedDF.map((entry) =>
        Object.keys(entry).filter((key) => key.startsWith(expandName))
    );
    const newColumns = Array.from(new Set(extendedDFColumns.flat()));
    const newDF = new DataFrame();

    for (const col of originalDF.columns) {
        newDF.addColumn(col, originalDF.getColumn(col));
    }

    for (const newCol of newColumns) {
        newDF.addColumn(newCol, extendedDF.map((entry) => entry[newCol] || null));
    }

    return newDF;
}

function listToDataFrame(dataframe, colToExpand) {
    const series = dataframe.apply((row) => row[colToExpand].map((item) => [item]), 1);
    const seriesName = colToExpand;
    const newDF = dataframe.drop([colToExpand], axis = 1);

    for (let rowIndex = 0; rowIndex < series.length; rowIndex++) {
        for (let itemIndex = 0; itemIndex < series[rowIndex].length; itemIndex++) {
            newDF.loc[rowIndex, seriesName + itemIndex] = series[rowIndex][itemIndex];
        }
    }

    return newDF;
}

function allDictToStr(d) {
    if (typeof d === 'object' && d !== null) {
        const newDict = {};

        for (const [key, value] of Object.entries(d)) {
            newDict[key] = String(value);
        }

        return newDict;
    } else if (d === null) {
        return null;
    } else {
        try {
            const parsed = JSON.parse(d);

            if (typeof parsed === 'object') {
                const newDict = {};

                for (const [key, value] of Object.entries(parsed)) {
                    newDict[key] = String(value);
                }

                return newDict;
            }
        } catch (e) { }

        return d;
    }
}

// Usage
const colToExpand = 'items';
const expandName = 'items_';
const newDataFrame = dictToColumns(dataframe, colToExpand, expandName);

const colToExpandList = 'columnWithList';
const newDataFrameList = listToDataFrame(dataframe, colToExpandList);

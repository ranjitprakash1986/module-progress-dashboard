const os = require('os');
const dotenv = require('dotenv');
const pd = require('pandas-js');
const Canvas = require('canvasapi');
const { InvalidAccessToken, ResourceDoesNotExist, Unauthorized } = require('canvasapi/exceptions');
const { pick } = require('pick');
const { table } = require('table');
const { init } = require('colorama');
init();

const settings = require('./settings');
const canvasHelpers = require('./canvas_helpers');
const logFailure = canvasHelpers.logFailure;

function getUserSettings() {
    console.log('\n');
    const base_url = 'https://canvas.ubc.ca';

    const token = loadToken(base_url);

    const canvas = new Canvas(base_url, token);
    const auth_header = { Authorization: 'Bearer ' + token };
    const course_ids = loadIds();
    const courses = [];
    const valid_cids = [];

    for (const cid of course_ids) {
        settings.status[cid] = {
            cname: null,
            status: 'Not executed',
            message: 'Has not been run yet',
        };

        try {
            const course = canvas.getCourse(cid);
            courses.push(course);
            valid_cids.push(cid);
        } catch (e) {
            if (e instanceof InvalidAccessToken) {
                shutDown('Invalid Access Token: Please check that the token provided is correct and still active');
            } else if (e instanceof Unauthorized) {
                logFailure(cid, 'User not authorized to get course data');
            } else if (e instanceof TypeError) {
                logFailure(cid, 'Invalid type on course id: "' + cid + '"');
            } else if (e instanceof ResourceDoesNotExist) {
                logFailure(cid, 'Not Found Error: Please ensure correct course id');
            }
        }
    }

    if (courses.length === 0) {
        shutDown('Error: course_entitlements.csv must contain at least one valid course code');
    }

    const course_names = makeSelectedCoursesString(courses);
    const options = ['Yes, run for all courses', 'Nevermind, end process'];
    const title = `You have chosen to get Module Process: \n\n For: ${course_names} \n\n From: ${base_url}`;
    const continue_confirm = pick(options, title);

    if (continue_confirm[1] === 0) {
        console.log(`Getting Module Progress: \n For: ${course_names} \n From: ${base_url}`);
        console.log('------------------------------\n');
        console.log('Starting...');
        console.log('Getting module dataframe');

        return {
            canvas: canvas,
            base_url: base_url,
            token: token,
            header: auth_header,
            course_ids: valid_cids,
        };
    }

    console.log('Exiting user setup...');
    process.exit();
}

function renderStatusTable() {
    const R = '\033[0;31;40m'; // RED
    const G = '\033[0;32;40m'; // GREEN
    const N = '\033[0m'; // Reset

    const rows = [['Course Id', 'Course Name', 'Status', 'Message']];
    for (const cid in settings.status) {
        const info = settings.status[cid];
        const col = info.status === 'Success' ? G : R;
        rows.push([cid, info.cname, col + info.status + N, info.message]);
    }

    const config = {
        columns: {
            2: {
                width: 15,
            },
        },
    };

    console.log(table(rows, config));
}

function loadToken(url) {
    try {
        const token = readToken(url);
        return token;
    } catch (e) {
        if (e instanceof InvalidAccessToken) {
            shutDown('Ivalid Access Token: No value set for token in .env file. Please provide a valid token');
        } else if (e instanceof RuntimeError) {
            console.log('Runtime Error: Could not load token!');
            console.log(
                'Ensure .env file is in root directory with token filled in for variable corresponding to given instance'
            );
            shutDown(
                'Possible variable keys are: CANVAS_API_TOKEN, CANVAS_API_TOKEN_TEST, CANVAS_API_TOKEN_SANDBOX'
            );
        }
    }
}

function loadIds() {
    try {
        const cids = [];
        const entitlementsPath = settings.ROOT_DIR + '/course_entitlements.csv';
        const dataframe = pd.readCSV(entitlementsPath);

        for (const row of dataframe.toDict()) {
            const course_id = row['course_id'];

            if (!cids.includes(course_id)) {
                cids.push(course_id);
            }
        }

        return cids;
    } catch (e) {
        if (e instanceof FileNotFoundError) {
            shutDown('File Not Found: There must be a file named course_entitlements.csv in ROOT directory.');
        } else if (e instanceof KeyError) {
            shutDown('Key Error: Please ensure there is a column titled "course_id" present in course_entitlements.csv');
        }
    }
}

function makeSelectedCoursesString(courses) {
    const indent = '    ';
    let selected = '\n' + indent + courses[0].name;
    courses.shift();

    if (courses.length > 0) {
        for (const course of courses) {
            selected += ', ' + '\n' + indent + course.name;
        }
    }

    return selected;
}

function readToken(url) {
    dotenv.loadDotenv(dotenv.findDotenv('.env'));

    let token = null;

    if (url === 'https://canvas.ubc.ca') {
        token = process.env.CANVAS_API_TOKEN;
    }

    if (token === '') {
        throw new InvalidAccessToken('No token value.');
    }

    if (token === null) {
        throw new RuntimeError();
    }

    return token;
}

function shutDown(msg) {
    console.log(msg);
    console.log('Shutting down...');
    process.exit();
}

// Usage
const userSettings = getUserSettings();
const canvas = userSettings.canvas;
const base_url = userSettings.base_url;
const token = userSettings.token;
const header = userSettings.header;
const course_ids = userSettings.course_ids;

renderStatusTable();

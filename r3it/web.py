import config
import base64
import copy
import csv
import json
import time
import flask_login
# import flask_wtf
# from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
import os, hashlib, random, logging, uuid, cachelib
import uuid
import logging
from flask_sessionstore import Session
from flask_session_captcha import FlaskSessionCaptcha

from random import choice as pick
from flask import Flask, redirect, request, send_from_directory, render_template, flash, url_for
import interconnection

# Global static variables.
r3itDir = os.path.dirname(os.path.abspath(__file__))
statuses = (
    'Application Submitted', # Attn: Member services, upon submission.
    'Engineering Review', # Attn: Engineering, if above size threshold
    'Customer Options Meeting Required', # Attn: Member Services, if engineering says so
    'Customer Options Meeting Proposed', # Attn: Consumer, when proposed by member services.
    'Customer Options Meeting Scheduled', # Attn: ???, 
    'Interconnection Agreement Proffered', # Attn: Customer
    'Interconnection Agreement Executed', # Attn: Customer
    'Permission to Operate Proffered', # Attn: Customer
    'Commissioning Test Needed', # Attn: Engineering, Customer
    'Commissioned', 
    'Out of Service'
)
engineerActionItems = (
    'Engineering Review', 'Commissioning Test Needed'
)
customerActionItems = (
    'Customer Options Meeting Proposed', 
    'Interconnection Agreement Proffered', 
    'Interconnection Agreement Executed',
    'Permission to Operate Proffered',
    'Commissioning Test Needed'
)
msActionItems = (
    'Application Submitted',
    'Customer Options Meeting Required'
)

# Instantiate app
app = Flask(__name__)
app.secret_key = config.COOKIE_KEY
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 5
app.config['CAPTCHA_WIDTH'] = 160
app.config['CAPTCHA_HEIGHT'] = 60
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
captcha = FlaskSessionCaptcha(app)


# Inject global template variables.
@app.context_processor
def inject_config():
    return dict(logo=config.logo, sizeThreshold=config.sizeThreshold, utilityName=config.utilityName)

# Initiate authentication system.
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'

def pwHash(username, password): return str(base64.b64encode(hashlib.pbkdf2_hmac('sha256', b'{password}', b'{username}', 100000)))

class User(flask_login.UserMixin):
    def __init__(self, email):
        self.id = email
        if self.id in config.engineers:
            self.type = 'engineer'
        elif self.id in config.memberServices:
            self.type = 'memberServices'
        else: 
            self.type = 'customer'

class Anon(flask_login.AnonymousUserMixin):
    def __init__(self):
        self.id = 'anonymous'
        self.type = 'anonymous'

## class docUpload(FlaskForm):
##     doc = FileField(validators=[FileRequired()])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['txt', 'pdf', 'doc', 'docx']

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    notification = request.args.get('notification', None)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect('/upload?notification=No%20file%20part%2E')
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return redirect('/upload?notification=No%20file%20selected%2E')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
        try:
            os.makedirs(os.path.join(app.root_path, "data", flask_login.current_user.id, "uploads"))
        except OSError:
            pass
        file.save(os.path.join(app.root_path, "data", flask_login.current_user.id, "uploads", filename))
        return redirect(url_for('upload_file') + '?notification=Upload%20successful%2E')
    return render_template('upload.html', notification=notification)

@login_manager.user_loader
def load_user(email):
    (_, users, _) = next(os.walk(os.path.join(app.root_path, 'data', 'Users')), (None, None, []))
    if email in users:
        return User(email)
    else:
        return Anon()

@app.route('/')
def index():
    data = []
    priorities = []
    notification = request.args.get('notification', None)
    if flask_login.current_user.is_anonymous():
        pass
    elif flask_login.current_user.type == 'engineer':
        for id, value in json.load(open('data/queue.json')).items():
            data.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
            if value['Status'] in engineerActionItems:
                priorities.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
    elif flask_login.current_user.type == 'memberServices':
        for id, value in json.load(open('data/queue.json')).items():
            data.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
            if value['Status'] in msActionItems:
                priorities.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
    elif flask_login.current_user.type == 'customer':
        for id, value in json.load(open('data/queue.json')).items():
            if value["Email (Customer)"] == flask_login.current_user.get_id():
                data.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
            if value['Status'] in customerActionItems:
                priorities.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
    if data:
        return render_template('index.html', data=data, priorities=priorities, notification=notification)
    else:
        return render_template('index.html', notification=notification)

@app.route('/login', methods=['GET', 'POST'])
def login():
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("login.html", notification=notification)
    if request.method == "POST":
        email, passwordAttempt = request.form['username'], pwHash(request.form['username'],request.form['password'])
        try: 
            with open(os.path.join(app.root_path, 'data', 'Users', email, 'user.json'), 'r') as userJson:
                users = json.load(userJson)
        except:
            users = {}
        password = users.get(email, {}).get('password')
        if email in users and password == passwordAttempt:
            flask_login.login_user(load_user(email))
            return redirect('/')
        else:
            return redirect('/login?notification=Username%20or%20password%20does%20not%20match%20our%20records%2E')

@app.route('/register', methods=['GET', 'POST'])
def register():
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("register.html", notification=notification)
    if request.method == "POST":
        email, password = request.form['username'], pwHash(request.form['username'],request.form['password'])
        user = {email : {'password' : password}}
        try:
            os.makedirs(os.path.join(app.root_path, "data", "Users", email))
        except OSError:
            pass
        if captcha.validate():
            with open(os.path.join(app.root_path, 'data', 'Users', email, 'user.json'), 'w') as userFile:
                json.dump(user, userFile)
            return redirect('/login?notification=Registration%20successful%2E')
        else:
            return redirect('/register?notification=CAPTCHA%20error%2E')

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')

@app.route('/report/<id>', methods=['GET','POST'])
@flask_login.login_required
def report(id):
    if request.method == "POST": 
        pass
    else:
        with open('data/queue.json') as queue:
            report_data = json.load(queue)[id]
        report_data['id'] = id
        with open('data/sample/allOutputData.json') as data:
            sample_data = json.load(data)
        return render_template('report.html', data=report_data, sample_data=sample_data)

def listIC():
    icList = []
    (_, users, _) = next(os.walk(os.path.join(app.root_path, 'data', 'Users')), (None, None, []))
    for user in users:
        (_, applications, _) = next(os.walk(os.path.join(app.root_path, 'data', 'Users', user, "applications")), (None, None, []))
        if applications: 
            icList.extend(applications)
    return icList

def absQueuePosition(requestTime, region = 0):
    return len(listIC())

# def headPosition(region = 0):


@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_queue():

    interconnection_request = {}
    for key, value in request.form.items():
        interconnection_request[key] = value
    interconnection_request['Time of Request'] = time.asctime(time.localtime(time.time()))
    queue_position = str(absQueuePosition(interconnection_request['Time of Request']))
    interconnection_request['Position'] = queue_position
    interconnection_request['Status'] = interconnection.submitApplication(interconnection_request)
    try:
        os.makedirs(os.path.join(app.root_path, 'data','Users',flask_login.current_user.id, "applications", interconnection_request['Time of Request']))
    except OSError:
        pass
    with open(os.path.join(app.root_path, 'data','Users',flask_login.current_user.id, "applications", interconnection_request['Time of Request'], 'application.json'), 'w') as queue:
        json.dump(interconnection_request, queue)
    # interconnection.processQueue()
    return redirect('/?notification=Application%20submitted%2E')

@app.route('/send-file/<path:fullPath>')
@flask_login.login_required
def send_file(fullPath):
    path_pieces = fullPath.split('/')
    return send_from_directory('/'.join(path_pieces[0:-1]), path_pieces[-1])

@app.route('/application')
@flask_login.login_required
def application():
    firstNames = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Charles', 'Mary', 'Patricia', 'Linda', 'Barbara', 'Elizabeth', 'Jennifer', 'Maria', 'Susan', 'Margaret']
    lastNames = ['Smith', 'Jones', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    trees = ['Oak', 'Birch', 'Cypress', 'Maple', 'Pine', 'Hickory', 'Ash', 'Aspen', 'Elder Berry']
    suffixes = ['Ave.', 'Ln.', 'St.', 'Way', 'Blvd']
    zips = range(54601, 54650)
    phases = ['One', 'Three']
    sizes = range(1,20)
    voltages = ['110', '220', '600']
    firstname, lastname = pick(firstNames), pick(lastNames)
    default = {
        'label' : '{} {}\'s Solar Project'.format(firstname, lastname),
        'name' : '{} {}'.format(firstname, lastname),
        'address' : "{} {} {}".format(str(pick(range(9999))), pick(trees), pick(suffixes)),
        'zip' : '{}'.format(pick(zips)),
        'city': 'LaCrosse',
        'state' : 'WI',
        'phone' : '({}{}) {}{} - {}'.format(pick(range(2,9)), pick(range(10,99)), pick(range(2,9)), pick(range(10,99)), pick(range(1000,9999))),
        'size' : '{}'.format(pick(sizes)),
        'voltage' : '{}'.format(pick(voltages)),
        'email' : str(flask_login.current_user.id)
    }
    return render_template('application.html', default = default)

@app.route('/update-status/<id>/<status>')
@flask_login.login_required
def update_status(id, status):
    with open('data/queue.json') as queue:
        data = json.load(queue)
    status = interconnection.compute_status(data[id])
    if status not in statuses:
        return 'Status invalid; no update made.'
    data[id]['Status'] = status
    with open('data/queue.json', 'w') as queue:
        json.dump(data, queue)
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run(debug=True)
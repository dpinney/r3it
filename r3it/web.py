import config
import base64
import copy
import csv
import json
from datetime import datetime
import flask_login
from werkzeug.utils import secure_filename
import os, hashlib, random, logging, uuid, cachelib
import uuid
import logging
from flask_sessionstore import Session
from flask_session_captcha import FlaskSessionCaptcha
from random import choice as pick
from flask import Flask, redirect, request, send_from_directory, render_template, flash, url_for
from multiprocessing import Process
# import interconnection

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

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'

@app.route('/register', methods=['GET', 'POST'])
def register():
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("register.html", notification=notification)
    if request.method == "POST":
        email, password = request.form['email'], request.form['password']
        userDict = {email : {'password' : passwordHash(email, password)}}
        try:
            os.makedirs(os.path.join(app.root_path, "data", "Users", email))
        except:
            return redirect('/register?notification=Account%20already%20exists%2E')
        if captcha.validate():
            with userAccountFile(email, 'w') as userFile:
                json.dump(userDict, userFile)
            return redirect('/login?notification=Registration%20successful%2E')
        else:
            return redirect('/register?notification=CAPTCHA%20error%2E')

@login_manager.user_loader
def load_user(email):
    if email in users():
        return User(email)
    else:
        return Anon()

def authorized(ic):
    '''Is the user authorized to see this application?'''
    authed = flask_login.current_user.is_authenticated()
    employee = authed and not currentUser() == 'customer'
    applicant = authed and currentUser() == ic.get('Email (Customer)')
    return employee or applicant

@app.route('/logout')
def logout():
    try:
        flask_login.logout_user()
    except:
        pass
    return redirect('/')

@app.route('/')
def index():
    notification = request.args.get('notification', None)
    data = [
            [str(key+1), # queue position
            ic.get('Time of Request'),
            ic.get('Address (Facility)'),
            ic.get('Status')] for key, ic in enumerate(listIC()) if authorized(ic)
        ]
    priorities = [row for row in data if row[3] in config.actionItems.get(flask_login.current_user.type)]
    return render_template('index.html', data=data, priorities=priorities, notification=notification)

def passwordHash(username, password):
    return str(base64.b64encode(hashlib.pbkdf2_hmac('sha256', b'{password}', b'{username}', 100000)))

@app.route('/login', methods=['GET', 'POST'])
def login():
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("login.html", notification=notification)
    if request.method == "POST":
        email, passwordAttempt = request.form['email'], request.form['password']
        passwordAttemptHash = passwordHash(email, passwordAttempt)
        passwordHash = userAccountDict(email).get(email, {}).get('password')
        passwordsMatch = passwordHash == passwordAttemptHash

        if passwordsMatch:
            flask_login.login_user(load_user(email))
            return redirect('/')
        else:
            return redirect('/login?notification=Username%20or%20password%20does%20not%20match%20our%20records%2E')

@app.route('/report/<id>')
@flask_login.login_required
def report(id):
    report_data = listIC()[int(id)-1]
    with open(app.root_path + '/../sample/allOutputData.json') as data:
        sample_data = json.load(data)
    return render_template('report.html', data=report_data, sample_data=sample_data)

def users():
    '''Returns list of users'''
    (_, users, _) = next(os.walk(os.path.join(app.root_path, 'data', 'Users')), (None, [], None))
    return users

def currentUser():
    try:
        currentUser = flask_login.current_user.get_id()
    except:
        currentUser = 'anonymous'
    return currentUser

def userHomeDir(user=currentUser()):
    '''Takes user email, returns path of the user's home directory'''
    return os.path.join(app.root_path, 'data', 'Users', user)

def userAccountFile(user=currentUser(), rw='r'):
    '''Returns user account file object.'''
    return open(os.path.join(userHomeDir(user), 'user.json'), rw)

def userAccountDict(user=currentUser()):
    '''Return user account information'''
    with userAccountFile(user, 'r') as userFile:
        return json.load(userFile)

def userAppsList(user=currentUser()):
    '''Returns IDs of applications belonging to a user'''
    (_, applications, _) = next(os.walk(os.path.join(userHomeDir(user), "applications")), (None, [], None))
    return applications

def allAppIDs():
    '''Returns list of all application IDs'''
    return (apps for apps in userAppsList(user) for user in users())

def appExists(appID='-1'):
    '''Returns true when an appID corresponds to an application'''
    return appID in allAppIDs()

def listIC():
    icList = []
    # Restrict customers from seeing all interconnection applications
    for user in users():
        for application in userAppsList(user):
            with open(os.path.join(app.root_path, 'data', 'Users', user, "applications", application, 'application.json')) as appJSON:
                icList.append(json.load(appJSON))
    icList.sort(key=lambda x: float(x.get('Time of Request')))
    return icList

@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_queue():
    interconnection_request = {}
    for key, item in request.form.items():
        interconnection_request[key] = item
    interconnection_request['Timestamp'] = str(datetime.timestamp(datetime.now()))
#   TODO: Re-add interconnection.py when OMF is fixed.
#   interconnection_request['Status'] = interconnection.submitApplication(interconnection_request)
    interconnection_request['Status'] = 'Submitted'
    try:
        os.makedirs(os.path.join(app.root_path, 'data','Users',currentUser(), "applications", interconnection_request['Time of Request']))
    except OSError:
        pass
    with open(os.path.join(app.root_path, 'data','Users',currentUser(), "applications", interconnection_request['Time of Request'], 'application.json'), 'w') as queue:
        json.dump(interconnection_request, queue)

    # run analysis on the queue as a separate process
#   TODO: Re-add interconnection.py when OMF is fixed.
#    p = Process(target=interconnection.processQueue)
#    p.start()

    return redirect('/?notification=Application%20submitted%2E')

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
        'email' : currentUser()
    }
    return render_template('application.html', default = default)

#TODO: Fix update status
@app.route('/update-status/<id>/<status>')
@flask_login.login_required
def update_status(position, status):
    data = listIC()
#    status = interconnection.compute_status(data[position])
    if status not in config.statuses:
        return 'Status invalid; no update made.'
    data[id]['Status'] = status
#    with open('data/queue.json', 'w') as queue:
#        json.dump(data, queue)
    return redirect(request.referrer)

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
            os.makedirs(os.path.join(app.root_path, "data", currentUser(), "uploads"))
        except OSError:
            pass
        file.save(os.path.join(app.root_path, "data", currentUser(), "uploads", filename))
        return redirect(url_for('upload_file') + '?notification=Upload%20successful%2E')
    return render_template('upload.html', notification=notification)

if __name__ == '__main__':
    app.run(debug=True)

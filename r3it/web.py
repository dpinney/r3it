import config #, interconnection, user, queue
import base64, json, copy, csv, os, hashlib, random, uuid
from datetime import datetime
from multiprocessing import Process
from flask import Flask, redirect, request, render_template, url_for
from werkzeug.utils import secure_filename
import flask_login, flask_sessionstore, flask_session_captcha

# Instantiate app
app = Flask(__name__)
app.secret_key = config.COOKIE_KEY
# Inject global template variables.
@app.context_processor
def inject_config():
    return dict(
        logo          = config.logo,
        sizeThreshold = config.sizeThreshold,
        utilityName   = config.utilityName
        )
# Instantiate CAPTCHA
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 5
app.config['CAPTCHA_WIDTH'] = 160
app.config['CAPTCHA_HEIGHT'] = 60
app.config['SESSION_TYPE'] = 'filesystem'
flask_sessionstore.Session(app)
captcha = flask_session_captcha.FlaskSessionCaptcha(app)

# Instantiate authentication system.
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'

class User(flask_login.UserMixin):
    def __init__(self, email):
        self.id = email
        self.type = userType(email)

@login_manager.user_loader
def load_user(email):
    if email in users():
        return User(email)
    else:
        pass

# User management functions
#def users():
#    '''Returns list of users'''

def currentUserEmail():
    '''Returns the email (account identifier) of the currently logged-in user'''
    try:
        currentUserEmail = flask_login.current_user.get_id()
    except:
        currentUserEmail = 'anon@ymous.com'
    return currentUserEmail

def powerUsers():
    '''Returns dict 'email':[roles] for users with elevated permissions.'''
    emails = [email for email in emails for _, emails in enumerate(config.roles)]
    return {email:userRoles(email) for email in emails}

def userRoles(user=currentUserEmail()):
    '''Returns list of roles assigned to a user, identified by email.'''
    return [role for role, emails in enumerate(config.roles) if user in emails]

def currentUserIs(role):
    '''Checks to see if the current user has the role'''
    return role in userRoles(currentUserEmail())

def userHomeDir(user=currentUserEmail()):
    '''Takes user email, returns path of the user's home directory'''
    return os.path.join(app.root_path, 'data', 'Users', user)

def userAccountFile(user=currentUserEmail(), rw='r'):
    '''Returns user account file object.'''
    return open(os.path.join(userHomeDir(user), 'user.json'), rw)

def userAccountDict(user=currentUserEmail()):
    '''Return user account information'''
    with userAccountFile(user, 'r') as userFile:
        return json.load(userFile)

@app.route('/register', methods=['GET', 'POST'])
def register():
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("register.html", notification=notification)
    if request.method == "POST":
        email, password = request.form['email'], request.form['password']
        userDict = {email : {'password' : passwordHash(email, password)}}
        try:
            os.makedirs(UserHomeDir(email))
        except:
            return redirect('/register?notification=Account%20already%20exists%2E')
        if captcha.validate():
            with userAccountFile(email, 'w') as userFile:
                json.dump(userDict, userFile)
            return redirect('/login?notification=Registration%20successful%2E')
        else:
            return redirect('/register?notification=CAPTCHA%20error%2E')

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''GET for the login page, POST to log in user.'''
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

@app.route('/logout')
def logout():
    try:
        flask_login.logout_user()
    except:
        pass
    return redirect('/')

def authorized(ic):
    '''Is the current user authorized to see this application?'''
#TODO: fix 68
    employee = not currentUserEmail() == 'customer'
    applicant = currentUserEmail() == ic.get('Email (Customer)')
    return employee or applicant

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

@app.route('/report/<id>')
@flask_login.login_required
def report(id):
    '''Given interconnection ID, render detailed report page'''
    report_data = listIC()[int(id)-1]
    with open(app.root_path + '/../sample/allOutputData.json') as data:
        sample_data = json.load(data)
    return render_template('report.html', data=report_data, sample_data=sample_data)


# Queue management functions
def userAppsList(user=currentUserEmail()):
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
    interconnection_request['Time of Request'] = str(datetime.timestamp(datetime.now()))
    interconnection_request['Status'] = 'Application Submitted'
    try:
        os.makedirs(os.path.join(app.root_path, 'data','Users',currentUserEmail(), "applications", interconnection_request['Time of Request']))
    except OSError:
        pass
    with open(os.path.join(app.root_path, 'data','Users',currentUserEmail(), "applications", interconnection_request['Time of Request'], 'application.json'), 'w') as queue:
        json.dump(interconnection_request, queue)
    # run analysis on the queue as a separate process
    # p = Process(target=interconnection.processQueue)
    # p.start()
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
    firstname, lastname = random.choice(firstNames), random.choice(lastNames)
    default = {
        'label' : '{} {}\'s Solar Project'.format(firstname, lastname),
        'name' : '{} {}'.format(firstname, lastname),
        'address' : "{} {} {}".format(str(random.choice(range(9999))), random.choice(trees), random.choice(suffixes)),
        'zip' : '{}'.format(random.choice(zips)),
        'city': 'LaCrosse',
        'state' : 'WI',
        'phone' : '({}{}) {}{} - {}'.format(random.choice(range(2,9)), random.choice(range(10,99)), random.choice(range(2,9)), random.choice(range(10,99)), random.choice(range(1000,9999))),
        'size' : '{}'.format(random.choice(sizes)),
        'voltage' : '{}'.format(random.choice(voltages)),
        'email' : currentUserEmail()
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
            os.makedirs(os.path.join(app.root_path, "data", currentUserEmail(), "uploads"))
        except OSError:
            pass
        file.save(os.path.join(app.root_path, "data", currentUserEmail(), "uploads", filename))
        return redirect(url_for('upload_file') + '?notification=Upload%20successful%2E')
    return render_template('upload.html', notification=notification)

if __name__ == '__main__':
    app.run(debug=True)

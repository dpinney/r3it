import config #, interconnection
from user import *
from queue import *
import base64, json, copy, csv, os, hashlib, random, uuid, glob
import flask_login, flask_sessionstore, flask_session_captcha
from datetime import datetime
from multiprocessing import Process
from flask import Flask, redirect, request, render_template, url_for
from werkzeug.utils import secure_filename

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

@login_manager.user_loader
def load_user(email):
    if email in users():
        return User(email)
    else:
        pass

def currentUser():
    '''Returns the email (account identifier) of the currently logged-in user'''
    try:
        currentUserEmail = flask_login.current_user.get_id()
    except:
        currentUserEmail = 'anon@ymous.com'
    return currentUserEmail

# Account-related routes.
@app.route('/register', methods=['GET', 'POST'])
def register():
    '''Account registration with CAPTCHA verification'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("register.html", notification=notification)
    if request.method == "POST":
        email, password = request.form['email'], request.form['password']
        userDict = {email : {'password' : hashPassword(email, password)}}
        if captcha.validate():
            try: os.makedirs(userHomeDir(email))
            except:
                return redirect('/register?notification=Account%20already%20exists%2E')
            with userAccountFile(email, 'w') as userFile: json.dump(userDict, userFile)
            return redirect('/login?notification=Registration%20successful%2E')
        else:
            return redirect('/register?notification=CAPTCHA%20error%2E')

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''GET for the login page, POST to log in user with flask_login.'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("login.html", notification=notification)
    if request.method == "POST":
        if passwordCorrect(request.form['email'], request.form['password']):
            flask_login.login_user(load_user(request.form['email']))
            return redirect('/')
        else:
            return redirect('/login?notification=Username%20or%20password%20does%20not%20match%20our%20records%2E')

@app.route('/logout')
def logout():
    '''Logs the user out of their account.'''
    try:
        flask_login.logout_user()
    except:
        pass
    return redirect('/')

@app.route('/')
def index():
    '''Landing page; shows interconnection inboxes for logged in users.'''
    notification = request.args.get('notification', None)
    data = [
        [str(key+1), # queue position
        app.get('Time of Request'),
        app.get('Address (Facility)'),
        app.get('Status')] for key, app in enumerate(queue()) \
                                    if authorizedToView(currentUser(), app)
    ]
    priorities = [
        [str(key+1),
        app.get('Time of Request'),
        app.get('Address (Facility)'),
        app.get('Status')] for key, app in enumerate(queue()) \
                                    if requiresUsersAction(currentUser(),app)
    ]
    return render_template('index.html', data=data, \
                                         priorities=priorities, \
                                         notification=notification)
@app.route('/report/<id>')
@flask_login.login_required
def report(id):
    '''Given interconnection ID, render detailed report page'''
#TODO: Reconfigure to user timestamps or uuids instead of queue index.
    report_data = queue()[int(id)-1]
    with open(app.root_path + '/../sample/allOutputData.json') as data:
        sample_data = json.load(data)
    return render_template('report.html', data=report_data, sample_data=sample_data)

@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_queue():
    '''Adds an interconnection application to the queue'''
    app = {key:item for key, item in request.form.items()}
    app['Timestamp'] = str(datetime.timestamp(datetime.now()))
    app['Time of Request'] = str(datetime.now())
    app['Status'] = 'Application Submitted'
    try: os.makedirs(appPath(currentUser(),app['Timestamp']))
    except: pass
    with appFile(currentUser(), app['Timestamp'], 'w') as appFile:
        json.dump(app, appFile)
    # TODO: Figure out the fork-but-not-exec issue (below -> many errors)
    # run analysis on the queue as a separate process
    # p = Process(target=interconnection.processQueue)
    # p.start()
    return redirect('/?notification=Application%20submitted%2E')

@app.route('/application')
@flask_login.login_required
def application():
    '''GET returns form for new interconnection application.'''
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
        'email' : currentUser()
    }
    return render_template('application.html', default = default)

#TODO: Fix update status
@app.route('/update-status/<id>/<status>')
@flask_login.login_required
def update_status(position, status):
    data = queue()
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
#TODO Re-work uploads
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

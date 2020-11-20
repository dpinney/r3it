import config, interconnection, mailer
from user import *
from appQueue import *
import base64, json, copy, csv, os, hashlib, random, uuid, glob
import flask_login, flask_sessionstore, flask_session_captcha
from datetime import datetime
from multiprocessing import Process, Lock
from flask import Flask, redirect, request, render_template, url_for, send_from_directory
from werkzeug.utils import secure_filename

# Instantiate app
app = Flask(__name__)
app.secret_key = config.COOKIE_KEY

# Inject global template variables.
@app.context_processor
def inject_config():
    return dict(
        logo          = config.logo,
        bg            = config.bg,
        sizeThreshold = config.sizeThreshold,
        utilityName   = config.utilityName,
        appAttachments= config.appAttachments
    )

# instantiate queue processing lock, and withdrawal lock
# ensures only one que processing run happens at a time
processQueueLock = Lock()
withdrawLock = Lock()

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
        self.roles = userRoles(email)

@login_manager.user_loader
def load_user(email):
    if email in users(): return User(email)
    else: pass

def currentUser():
    '''Returns the email (account identifier) of the currently logged-in user'''
    try: currentUserEmail = flask_login.current_user.get_id()
    except: currentUserEmail = 'anon@ymous.com'
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

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    '''Account registration with CAPTCHA verification'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("forgot.html", notification=notification)
    if request.method == "POST":
        email = request.form['email']
        try:
            userDict = userAccountDict(email)
        except: return redirect('/forgot?notification=The%20email&20address&20you&20entered&20does&20match&our&records%2E')
        userDict[email]['resetToken'] = random.choice(9999999999)
        with userAccountFile(email, 'w') as userFile: json.dump(userDict, userFile)
        link = 'demo.r3it.ghw.coop/reset/' + email + '/' + userDict[email]['resetToken']
        mailer.sendEmail(email,'R3IT Password Reset',link)
        return redirect('/forgot?notification=Password&20reset&20email&20sent%2E')

@app.route('/newpassword/<email>/<token>', methods=['GET', 'POST'])
def newpassword():
    '''Account registration with CAPTCHA verification'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        if userDict[email]['resetToken'] == token:
            return render_template("newpassword.html", notification=notification)
        else: redirect('/?Not&20a&20valid&20password&20reset&20link.')
    if request.method == "POST":
        email = request.form['email']
        try:
            userDict = userAccountDict(email)
        except: return redirect('/forgot?notification=The%20email&20address&20you&20entered&20does&20match&our&records%2E')
        userDict[email]['resetToken'] = random.choice(9999999999)
        with userAccountFile(email, 'w') as userFile: json.dump(userDict, userFile)
        link = 'demo.r3it.ghw.coop/reset/' + email + '/' + userDict[email]['resetToken']
        mailer.sendEmail(email,'R3IT Password Reset',link)
        return redirect('/forgot?notification=Password&20reset&20email&20sent%2E')


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
        app.get('ID'),
        app.get('Address (Facility)'),
        app.get('Status')] for key, app in enumerate(appQueue()) \
                                    if authorizedToView(currentUser(), app)
    ]
    priorities = [
        [str(key+1),
        app.get('Time of Request'),
        app.get('ID'),
        app.get('Address (Facility)'),
        app.get('Status')] for key, app in enumerate(appQueue()) \
                                    if requiresUsersAction(currentUser(), app)
    ]
    return render_template('index.html', data=data, \
                                         priorities=priorities, \
                                         notification=notification)

@app.route('/report/<id>', methods=['GET', 'POST'])
@flask_login.login_required
def report(id):
    '''Given interconnection ID, render detailed report page'''
    report_data = appDict(id)
    try:
        with open(os.path.join(appDir(id),GRIDLABD_DIR,OUTPUT_FILENAME)) as data:
            eng_data = json.load(data)
    except: eng_data = []
    next_statuses = allowedStatusChanges.get(report_data.get('Status'))
    if next_statuses:
        updates = [update for update, role in next_statuses.items() \
                            if role in userRoles(currentUser(), report_data)]
    else: updates = []
    return render_template('report.html', data=report_data, eng_data=eng_data, updates=updates, files=allAppUploads(id))

@app.route('/upload/<id>/<doc>', methods=['GET','POST'])
@flask_login.login_required
def upload(id, doc):
    if request.method == 'POST': # File uploads
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect('/report/' + id + '?notification=No%20file%20part%2E')
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return redirect('/report/' + id + '?notification=No%20file%20selected%2E')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
        try:
            os.makedirs(os.path.join(app.root_path, "data", 'applications', id, "uploads", doc))
        except OSError:
            pass
        file.save(os.path.join(app.root_path, "data", 'applications', id, 'uploads', doc, filename))
        return redirect(url_for('index') + '?notification=Upload%20successful%2E')
    else: return redirect(request.referrer)

@app.route('/download/<id>/<doc>/<path:filename>')
@flask_login.login_required
def download(id, doc, filename):
    if authorizedToView(currentUser(), appDict(id)) and doc in appAttachments:
        return send_from_directory(os.path.join(appDir(id),'uploads',doc), filename)
    else:
        return redirect('/')

@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_appQueue():
    '''Adds an interconnection application to the queue'''
    app = {key:item for key, item in request.form.items()}
    app['ID'] = str(int(datetime.timestamp(datetime.now()) * 10**7) + random.choice(range(999)))
    app['Time of Request'] = str(datetime.now())
    app['Status'] = 'Application Submitted'
    try: os.makedirs(appDir(app['ID']))
    except: pass
    with appFile(app['ID'], 'w') as appfile:
        json.dump(app, appfile)
    # TODO: Figure out the fork-but-not-exec issue (below -> many errors)
    # run analysis on the queue as a separate process
    p = Process(target=interconnection.processQueue, args=(processQueueLock,))
    p.start()
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
        'email' : currentUser(),
        'meterID' : '{}'.format(random.choice(interconnection.getMeterNameList( \
            os.path.join(config.STATIC_DIR,config.GRIDLABD_DIR,config.omdFilename))))
    }
    return render_template('application.html', default = default)

@app.route('/update-status/<id>/<status>')
@flask_login.login_required
def update_status(id, status):
    data = appDict(id)
    if status not in config.statuses: return 'Status invalid; no update made.'
    data['Status'] = status
    with appFile(id, 'w') as file:
        json.dump(data, file)
    mailer.sendEmail(data.get('Email (Contact)', ''), 'The status of your interconnection request has changed.')
    if status == 'Withdrawn':
        p = Process(target=interconnection.withdraw, args=(withdrawLock, processQueueLock, id))
        p.start()
    return redirect(request.referrer)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['txt', 'pdf', 'doc', 'docx']

if __name__ == '__main__':
    app.run(debug=True, host= '0.0.0.0')

from datetime import datetime
import base64, json, copy, csv, os, hashlib, random, uuid, glob, stripe
import flask_login, flask_session, flask_session_captcha
from flask import Flask, redirect, request, render_template, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from multiprocessing import Process, Lock
from urllib.parse import urlencode
from logger import log
import config, mailer
from subprocess import Popen
if config.enableAutomaticScreening:
    import interconnection
else:
    from interconnection import calcCapacityUsed, calcCapacityByUser, processQueue, withdraw
    from appQueue import *

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
        states        = config.states,
        inverters     = config.inverters,
        appAttachments= config.appAttachments
    )

# instantiate queue processing lock, and withdrawal lock
# ensures only one que processing run happens at a time
processQueueLock = Lock()
withdrawLock = Lock()

# Instantiate CAPTCHA TODO: make work with flask 2.0 -> werkzeug > .16
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 5
app.config['CAPTCHA_WIDTH'] = 160
app.config['CAPTCHA_HEIGHT'] = 60
app.config['SESSION_TYPE'] = 'filesystem'
flask_session.Session(app)
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
        log('Registering new user with email, ' + email)
        userDict = {email : {'password' : hashPassword(email, password)}}
        if captcha.validate():
            try: os.makedirs(userHomeDir(email))
            except:
                log('Registration for ' + email + ' failed; Account already exists')
                return redirect(f"/register?{urlencode({'notification': 'Error: Account already exists.'})}")
            with userAccountFile(email, 'w') as userFile: json.dump(userDict, userFile)
            log('Registration successful for ' + email)
            return redirect(f"/login?{urlencode({'notification': 'Success: Registration completed.'})}")
        else:
            log('Registration for ' + email + ' failed; CAPTCHA error')
            return redirect(f"/register?{urlencode({'notification': 'Error: Invalid CAPTCHA.'})}")

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    '''Sends email to user with a password reset link'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("forgot.html", notification=notification)
    if request.method == "POST":
        email = request.form['email']
        try:
            userDict = userAccountDict(email)
        except: 
            log('Password reset requested for ' + email + '; account not found')
            return redirect(f"/forgot?{urlencode({'notification': 'Error: Account not found.'})}")
        userDict[email]['resetToken'] = str(random.randint(100000,1000000))
        with userAccountFile(email, 'w') as userFile: json.dump(userDict, userFile)
        link = 'demo.r3it.ghw.io/newpassword/' + email + '/' + userDict[email]['resetToken']
        mailer.sendEmail(email,'R3IT Password Reset Link','Use the following link to reset your password: ' + link)
        log('Password reset link sent to ' + email)
        return redirect(f"/forgot?{urlencode({'notification': 'Success: Password reset email sent.'})}")

@app.route('/newpassword/<email>/<token>', methods=['GET', 'POST'])
def newpassword(email, token):
    '''create new password for account'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        try:
            userDict = userAccountDict(email)
        except: return redirect(f"/forgot?{urlencode({'notification': 'Error: Invalid password reset link.'})}")
        if userDict[email].get('resetToken','') == token:
            return render_template("newpassword.html", email=email, token=token, notification=notification)
        else: return redirect(f"/forgot?{urlencode({'notification': 'Error:  Invalid password reset link.'})}")
    
    if request.method == "POST":
        password = request.form['password']
        userDict = {email : {'password' : hashPassword(email, password)}}
        with userAccountFile(email, 'w') as userFile: json.dump(userDict, userFile)
        mailer.sendEmail(email,'R3IT Password Reset successfully','Your R3IT password has been reset successfully.')
        log('Password reset successfully for ' + email)
        return redirect(f"/login?{urlencode({'notification': 'Success: Password successfully updated.'})}")

@app.route('/sendDelegationEmail/<id>')
@flask_login.login_required
def sendDelegationEmail(id, notification=''):
    mailer.sendEmail(appDict(id)['Email (Member)'], 
    	'Approve interconnection application', 
    	'Click this link to approve ' + 
    	appDict(id)['Email (Contractor)'] + 
    	' to administer an interconnection application for ' + 
    	appDict(id)['Address (Service)'] + ': ' + 
    	config.DOMAIN + '/delegate/' + id + '/' + 
    	hashPassword('delegation', id)) 
    return redirect(f"""/report/{id}?{urlencode(
        {'notification': f'Success: {notification} Delegation email sent.'})}""") # Does notification insert really need to be there?

@app.route('/delegate/<id>/<token>')
def delegate(id, token):
    '''Delegate account permissions'''
    notification = request.args.get('notification', None)
    if appDict(id)['Status'] == 'Delegation Required':
        if hashPassword('delegation', id) == token:
            update_status(id, 'Application Submitted')
            return redirect(f"/?{urlencode({'notification': 'Success: Account permission delegated.'})}")
        else: return redirect(f"/?{urlencode({'notification': 'Error: Delegation failed.'})}")
    else: return redirect(f"/?{urlencode({'notification': 'Info: Delegation already completed.'})}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''GET for the login page, POST to log in user with flask_login.'''
    notification = request.args.get('notification', None)
    if request.method == "GET":
        return render_template("login.html", notification=notification)
    if request.method == "POST":
        log('User login attempt')
        if passwordCorrect(request.form['email'], request.form['password']):
            flask_login.login_user(load_user(request.form['email']))
            log('User ' + request.form['email'] + ' logged in successfully')
            return redirect('/')
        else:
            log('User login failed; incorrect username or password')
            return redirect(f"/login?{urlencode({'notification': 'Error: Invalid username or password.'})}")

@app.route('/logout')
def logout():
    '''Logs the user out of their account.'''

    log('User logging out')
    try:
        flask_login.logout_user()
    except:
        pass
    log('User logged out')
    return redirect('/')

@app.route('/')
def index():
    '''Landing page; shows interconnection inboxes for logged in users.'''
    notification = request.args.get('notification', None)
    data = [
        [str(key+1), # queue position
        app.get('Time of Request'),
        app.get('ID'),
        app.get('Address (Service)'),
        app.get('Status')] for key, app in enumerate(appQueue()) \
                                    if authorizedToView(currentUser(), app)
    ]
    priorities = [
        [str(key+1),
        app.get('Time of Request'),
        app.get('ID'),
        app.get('Address (Service)'),
        app.get('Status')] for key, app in enumerate(appQueue()) \
                                    if requiresUsersAction(currentUser(), app)
    ]

    netMeteringUsed = {}
    netMeteringUsed['used'] = calcCapacityUsed()
    netMeteringUsed['available'] = config.netMeteringCapacity
    netMeteringUsed['percent'] = 100 * \
    	netMeteringUsed['used'] / netMeteringUsed['available']
    netMeteringUsed['currentUser'] = calcCapacityByUser(currentUser())
    netMeteringUsed['otherUsers'] = netMeteringUsed['used'] - netMeteringUsed['currentUser']
    netMeteringUsed['currentUserPercent'] = 100 * \
    	netMeteringUsed['currentUser'] / netMeteringUsed['available']
    netMeteringUsed['otherUsersPercent'] = 100 * \
    	netMeteringUsed['otherUsers'] / netMeteringUsed['available']
    return render_template('index.html', data=data, \
                                         priorities=priorities, \
                                         notification=notification, \
                                         netMeteringUsed=netMeteringUsed)

@app.route('/report/<id>', methods=['GET', 'POST'])
@flask_login.login_required
def report(id):

    '''Given interconnection ID, render detailed report page'''
    
    notification = request.args.get('notification', None)
    report_data = appDict(id)
    
    try: edits = appEditsDict(id)
    except: edits = {}

    try:
        with open(os.path.join(appDir(id),GRIDLABD_DIR,OUTPUT_FILENAME)) as data:
            eng_data = json.load(data)
    except: eng_data = []
    
    next_statuses = allowedStatusChanges.get(report_data.get('Status'))
    if next_statuses:
        updates = [update for update, role in next_statuses.items() \
                            if role in userRoles(currentUser(), report_data)]
    else: updates = []

    return render_template('report.html', data=report_data, edits=edits, 
        eng_data=eng_data, updates=updates, files=allAppUploads(id), 
        notification=notification)

@app.route('/upload/<id>/<doc>', methods=['GET','POST'])
@flask_login.login_required
def upload(id, doc):
  
    if request.method == 'POST': # File uploads
        log('Uploading file')

        # check if the post request has the file part
        if 'file' not in request.files:
            log('Document ' + doc + 'Upload for application ' + id + ' failed; no file part')
            return redirect(f"/report/{id}?{urlencode({'notification': 'Error: No file recieved.'})}")
        file = request.files['file']
  
        # if user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            log('Document ' + doc + 'Upload for application ' + id + ' failed; no file selected')
            return redirect(f"/report/{id}?{urlencode({'notification': 'Error: No file selected.'})}")
  
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
        else: return redirect(f"/report/{id}?{urlencode({'notification': 'Error: File type not supported.'})}")

        try:
            os.makedirs(os.path.join(app.root_path, "data", 'applications', id, "uploads", doc))
        except OSError:
            pass
  
        file.save(os.path.join(app.root_path, "data", 'applications', id, 'uploads', doc, filename))
        log('Document ' + doc + 'Upload for application ' + id + ' successful; document saved')
        return redirect(f"/report/{id}?{urlencode({'notification': 'Success: File upload successful.'})}")
  
    else: return redirect(request.referrer)

@app.route('/download/<id>/<doc>/<path:filename>')
@flask_login.login_required
def download(id, doc, filename):
    log('Attempting to download document ' + doc + ' for application ' + id)
    if authorizedToView(currentUser(), appDict(id)) and doc in appAttachments:
        log('Download initiated')
        return send_from_directory(os.path.join(appDir(id),'uploads',doc), filename)
    else:
        log('Download not initiated; user not authorized to view document')
        return redirect('/')

@app.route('/.well-known/acme-challenge/<path:filename>')
def cert_renewal(filename):
    log('Attempting to renew TLS certificate')
    return send_from_directory(os.path.join(app.root_path,'.well-known','acme-challenge'), filename)
    
@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_appQueue():

    '''Adds an interconnection application to the queue'''
    
    app = {key:item for key, item in request.form.items()}
    app['Time of Request'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    app['Status'] = 'Payment Required'
    app['ID'] = str(int(datetime.timestamp(datetime.now()) * 10**7) + 
        random.choice(range(999)))
    
    try: os.makedirs(appDir(app['ID']))
    except: pass
    
    with appFile(app['ID'], 'w') as appfile:
        json.dump(app, appfile)
    
    log('Application ' + app['ID'] + 'submitted')
    
    link = 'demo.r3it.ghw.io/report/' + app['ID']
    mailer.mailEngineers('New R3IT application', 
        'New application with ID ' + app['ID'] + 
        ' submitted. Use the following link for details: ' + link)    
    mailer.sendEmail(app.get('Email (Member)', ''), 
        "R3IT application submitted",
        "Your application with ID " + app['ID'] + 
        ' submitted. Use the following link for details: ' + link)    

    # TODO: Figure out the fork-but-not-exec issue (below -> many errors)
    # run analysis on the queue as a separate process
    if config.enableAutomaticScreening == True:
        p = Process(target=interconnection.processQueue, 
            args=(processQueueLock,))
        p.start()
    
    return redirect(f"""/payment/{app['ID']}?{urlencode(
        {'notification': f'''Success: Application submitted. 
        Please click 'checkout' to complete payment.'''})}""")

@app.route('/application')
@flask_login.login_required
def application():
    
    '''GET returns form for new interconnection application.'''
    
    default = config.appFormDefaults
    if config.useMockApplications:
        default = getMockAppFormInputs()
    default['Email (Member)'] = currentUser()


    log('New application started')
    return render_template('application.html', 
        formAction='/add-to-queue', default = default)

@app.route('/edit/<id>')
@flask_login.login_required
def edit(id):
    '''GET returns form for editing interconnection application.'''
    data = appDict(id)
    log('New application edits started')
    return render_template('application.html', 
        default = data, formAction='/updateApp/'+id)

@app.route('/updateApp/<id>', methods=['GET', 'POST'])
@flask_login.login_required
def updateApp(id):

    # get original and edited apps
    app = appDict(id)
    appEdits = {key:item for key, item in request.form.items()}

    # compare original and edited apps and 
    # track values that are unchanged
    unchanged = []
    for key in appEdits.keys():
        if key in app.keys():
            originalVal = app[key]
            editedVal = appEdits[key]
            if originalVal == editedVal:
                unchanged.append(key)

    # only keep the values that are different as edits
    for key in unchanged:
        del appEdits[key]

    # save differences into edits.json
    with appEditsFile(app['ID'], 'w') as editsfile:
        json.dump(appEdits, editsfile, indent=4)

    # save and update the statuses of the app
    app['Previous Status'] = app['Status']
    app['Status'] = 'Engineering Review'
    with appFile(app['ID'], 'w') as appfile:
        json.dump(app, appfile, indent=4)

    # log event
    log('Application ' + app['ID'] + 'edited')

    # mail engineers the edits
    link = 'demo.r3it.ghw.io/report/' + app['ID']
    mailer.mailEngineers('R3IT application edited', 
        'Application with ID ' + app['ID'] + 
        ' has been edited. Use the following link for details: ' + link)    
    mailer.sendEmail(app.get('Email (Member)', ''), 
        "R3IT application edited",
        "Your edits to the application with ID " + app['ID'] + ' ' +
        'have been submitted.')

    # redirect to the report but with the edits displayed 
    return redirect(f"""/report/{id}?{urlencode(
        {'notification': '''Success: Application edits submitted. 
        Awaiting engineer approval.'''})}""")

@app.route('/reviewEdits/<id>/<decision>')
@flask_login.login_required
def reviewEdits(id, decision):

    if userHasUtilityRole(currentUser()):

        app = appDict(id)

        if decision == 'accept':

            # update application info
            edits = appEditsDict(id)
            for key in edits.keys():
                app[key] = edits[key]

            # delete edits file
            os.remove(appEditsPath(id))

            # log event
            log('Edits accepted for application ' + id)

            # return to report with 'approved' message
            notification = 'Success: Application edits accepted.'

        if decision == 'reject':

            # delete edits file
            os.remove(appEditsPath(id))

            # log event
            log('Edits rejected for application ' + id)

            # return to report with 'reject' message
            notification = 'Rejected: Application edits rejected.'

        #return app to previous status
        app['Status'] = app['Previous Status']
        del(app['Previous Status'])

        # save appliction info
        with appFile(app['ID'], 'w') as appfile:
            json.dump(app, appfile, indent=4)
    

    else: notification = 'Current user is not authorized to approve edits.'

    return redirect(f"/report/{id}?{urlencode({'notification': notification})}")
    
@app.route('/update-status/<id>/<status>')
@flask_login.login_required
def update_status(id, status):

    notification = interconnection.updateStatus(id, status)
    if status == 'Withdrawn':
        p = Process( target=interconnection.withdraw, 
            args=(withdrawLock, processQueueLock, id) )
        p.start()
    else: notification = 'Unauthorized attempt to update application status. Status not updated'
    return redirect(f"/?{urlencode({'notification': notification})}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['txt', 'pdf', 'doc', 'docx', 'jpg', 'png', 'gif', 'bmp', 'heic']

stripe.api_key = STRIPE_PRIVATE_KEY

@flask_login.login_required
@app.route('/payment/<id>')
def payment(id):
    if userOwnsApp(currentUser(), appDict(id)):
        notification = request.args.get('notification', None)
    else: notification = \
        'Current user is not authorized to make a payment on this application. ' + \
            'Please log in with the Member email provided in the application.'
    return render_template('payment.html', id=id, notification=notification)

@flask_login.login_required
@app.route('/success/<id>/<token>')
def success(id, token):
    
    if token != hashPassword(id, COOKIE_KEY) : 
        return redirect(f"/?{urlencode({'notification': 'Error: Payment failed.'})}")

    if appDict(id).get('Installation Type', '') ==  'Self-install':
        update_status(id, 'Application Submitted')
        notification = 'Success: Application submitted.'
        return redirect(f"/report/{id}?{urlencode({'notification': notification})}")
    
    else: 
    	update_status(id, 'Delegation Required')
    	notification = 'Success: Application submitted. Delegation still required.'
    	return sendDelegationEmail(id, notification=notification)
    

@app.route('/create-checkout-session/<id>', methods=['POST'])
def create_checkout_session(id):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 5000,
                        'product_data': {
                            'name': 'Interconnection Application Fee',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f"https://{DOMAIN}/success/{id}/{hashPassword(id, COOKIE_KEY)}",
            cancel_url=f"https://{DOMAIN}/?{urlencode({'notification': 'Error: Payment failed.'})}",
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 4

@app.route('/save-notes/<id>', methods=['POST'])
def save_notes(id):
    
    app = appDict(id)
    oldNotes = app.get('Notes', '')
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    newNote = request.form['notesText'].strip()
    newEntry = f"{now} {currentUser()}: \n{newNote}"
    notes = f"{oldNotes}\n\n{newEntry}" if oldNotes else newEntry

    if newNote != '':
        app['Notes'] = notes
        with appFile(app['ID'], 'w') as appfile:
            json.dump(app, appfile)

    return redirect(f"/report/{id}")

if __name__ == '__main__':
    # app.run(debug=True, host= '0.0.0.0')
    appProc = Popen(['gunicorn', '-w', '2', '-b', '0.0.0.0:5000', '--preload', 'web:app','--worker-class=sync', '--access-logfile', './data/r3it.access.log', '--error-logfile', './data/r3it.error.log', '--capture-output'])
    print('r3it started on port 5000; console output going to data/r3it.acces.log and data/r3it.error.log')
    appProc.wait()
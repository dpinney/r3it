import pytest, os, json, shutil
from r3it import web
from r3it.config import USERS_DIR, APPLICATIONS_DIR
from r3it.user import hashPassword, userAccountFile
from r3it.appQueue import appFile

fakeEmail, fakePassword = 'a@email.com', 'password'

@pytest.fixture
def client():
    web.app.config['TESTING'] = True
    with web.app.test_client() as client:
        yield client

# -----------------------------------------------------------------------

def checkResponseStatusOnGet(client, route, code):
    response = client.get(route)
    assert(response.status_code == code)

def createFakeUser():
    if not os.path.isdir(USERS_DIR): os.makedirs(USERS_DIR)
    userDict = {fakeEmail : {'password' : hashPassword(fakeEmail, fakePassword)}}
    os.makedirs(os.path.join(USERS_DIR,fakeEmail))
    with userAccountFile(fakeEmail, 'w') as userFile: 
        json.dump(userDict, userFile)

def deleteFakeUser():
    shutil.rmtree(os.path.join(USERS_DIR,fakeEmail))

# ------------------------------------------------------------------------

def test_index(client):
    checkResponseStatusOnGet(client, '/', 200)

def test_register(client):
    checkResponseStatusOnGet(client, '/register', 200)

def test_forgot(client):
    checkResponseStatusOnGet(client, '/forgot', 200)

def test_login(client):
    checkResponseStatusOnGet(client, '/login', 200)

def test_logoutBeforeLogin(client):
    checkResponseStatusOnGet(client, '/logout', 302)

def test_logoutAfterLogin(client):
    createFakeUser()
    fakeForm = {'email':fakeEmail,'password':fakePassword}
    client.post('/login', data={'form':fakeForm})
    checkResponseStatusOnGet(client, '/logout', 302)
    deleteFakeUser()
    
def test_application(client):
    checkResponseStatusOnGet(client, '/application', 302)


'''
@app.route('/newpassword/<email>/<token>', methods=['GET', 'POST'])
def newpassword(email, token):

@app.route('/sendDelegationEmail/<id>')
@flask_login.login_required
def sendDelegationEmail(id, notification=''):

@app.route('/delegate/<id>/<token>')
def delegate(id, token):

@app.route('/report/<id>', methods=['GET', 'POST'])
@flask_login.login_required
def report(id):

@app.route('/upload/<id>/<doc>', methods=['GET','POST'])
@flask_login.login_required
def upload(id, doc):  

@app.route('/download/<id>/<doc>/<path:filename>')
@flask_login.login_required
def download(id, doc, filename):

@app.route('/.well-known/acme-challenge/<path:filename>')
def cert_renewal(filename):
    
@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_appQueue():

@app.route('/edit/<id>')
@flask_login.login_required
def edit(id):

@app.route('/updateApp/<id>', methods=['GET', 'POST'])
@flask_login.login_required
def updateApp(id):

@app.route('/reviewEdits/<id>/<decision>')
@flask_login.login_required
def reviewEdits(id, decision):

@app.route('/update-status/<id>/<status>')
@flask_login.login_required
def update_status(id, status):

@flask_login.login_required
@app.route('/payment/<id>')
def payment(id):

@flask_login.login_required
@app.route('/success/<id>/<token>')
def success(id, token):
    
@app.route('/create-checkout-session/<id>', methods=['POST'])
def create_checkout_session(id):

@app.route('/save-notes/<id>', methods=['POST'])
def save_notes(id):
'''
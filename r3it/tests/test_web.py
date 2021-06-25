import pytest, os, shutil, glob, io
from r3it import web
from r3it.appQueue import appEditsDict, appDict
from .testHelpers import *

# -----------------------------------------------------------------------

@pytest.fixture
def client():
    web.app.config['TESTING'] = True
    with web.app.test_client() as client:
        yield client

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
    checkResponseStatusOnGet(client, '/logout', 200)

def test_logoutAfterLogin(client):
    createFakeUser()
    loginFakeUser(client,fakeEmail)
    checkResponseStatusOnGet(client, '/logout', 200)
    deleteFakeUser()
    
def test_applicationAfterLogin(client):
    createFakeUser()
    loginFakeUser(client,fakeEmail)
    checkResponseStatusOnGet(client, '/application', 200)
    deleteFakeUser()

def test_newPasswordGetValidToken(client):
    createFakeUser()
    token = createFakePasswordResetToken()    
    checkResponseStatusOnGet(client,'/newpassword/'+fakeEmail+'/'+token, 200)
    deleteFakeUser()

def test_newPasswordGetInvalidToken(client):
    checkResponseStatusOnGet(client, '/newpassword/'+fakeEmail+'/123456', 200)

def test_newPasswordPost(client):
    createFakeUser()
    token = createFakePasswordResetToken()    
    newPassword = 'newPassword'
    fakeForm = {'password':newPassword}
    client.post('/newpassword/'+fakeEmail+'/'+token, data=fakeForm, follow_redirects=True)
    # print(request.path, request.args)
    userDict = userAccountDict(fakeEmail)
    deleteFakeUser()
    assert(userDict[fakeEmail]['password'] == hashPassword(fakeEmail, newPassword))

def test_reportNotLoggedIn(client):
    checkResponseStatusOnGet(client,'/report/'+fakeApp['ID'], 200)
    # print(request.path, request.args)

def test_reportLoggedIn(client):
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    checkResponseStatusOnGet(client,'/report/'+fakeApp['ID'], 200)
    # print(request.path, request.args)
    deleteFakeApp()
    deleteFakeUser()

def test_add_to_appQueue(client):
    createFakeUser()
    loginFakeUser(client,fakeEmail)

    oldApps = glob.glob(os.path.join(APPLICATIONS_DIR,'*'))
    client.post('/add-to-queue', data=fakeApp, follow_redirects=True)
    # print(request.path, request.args)
    allApps = glob.glob(os.path.join(APPLICATIONS_DIR,'*'))
    newApps = list( set(allApps)-set(oldApps) )
    newAppID = os.path.split(newApps[0])[1]
    app = appDict(newAppID)
    assert(app['placeholder']=='data')
    shutil.rmtree(newApps[0])
    deleteFakeUser()

def test_editNotLoggedIn(client):
    checkResponseStatusOnGet(client,'/edit/'+fakeApp['ID'], 200)
    # print(request.path, request.args)

def test_editLoggedIn(client):
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    checkResponseStatusOnGet(client,'/edit/'+fakeApp['ID'], 200)
    # print(request.path, request.args)
    deleteFakeApp()
    deleteFakeUser()

def test_editLoggedIn(client):
    
    createFakeUser()
    loginFakeUser(client,fakeEmail)    
    createFakeApp()

    client.post('/updateApp/'+fakeApp['ID'], data=editedFakeApp, follow_redirects=True)
    # print(request.path, request.args)
    
    app, edits = appDict(fakeApp['ID']), appEditsDict(fakeApp['ID'])
    assert( (edits['placeholder'], app['Previous Status'], app['Status']) == 
        ('newData',fakeApp['Status'],'Engineering Review')
    )
    
    deleteFakeApp()
    deleteFakeUser()

def test_reviewEditsAccept(client):

    createFakeUser(fakePriviledgedEmail)
    loginFakeUser(client,fakePriviledgedEmail)
    createFakeApp()

    client.post('/updateApp/'+fakeApp['ID'], data=editedFakeApp, follow_redirects=True)
    client.get('/reviewEdits/'+fakeApp['ID']+'/accept', follow_redirects=True)
    # print(request.path, request.args)

    app = appDict(fakeApp['ID'])
    assert( (app['placeholder'], app['Status'], app.get('Previous Status')) == 
        (editedFakeApp['placeholder'], fakeApp['Status'], None) 
    )

    deleteFakeUser(fakePriviledgedEmail)
    deleteFakeApp()

def test_reviewEditsReject(client):

    createFakeUser(fakePriviledgedEmail)
    loginFakeUser(client,fakePriviledgedEmail)
    createFakeApp()

    client.post('/updateApp/'+fakeApp['ID'], data=editedFakeApp, follow_redirects=True)
    client.get('/reviewEdits/'+fakeApp['ID']+'/reject', follow_redirects=True)
    # print(request.path, request.args)

    app = appDict(fakeApp['ID'])
    assert( (app['placeholder'], app['Status'], app.get('Previous Status')) == 
        (fakeApp['placeholder'], fakeApp['Status'], None) 
    )

    deleteFakeUser(fakePriviledgedEmail)
    deleteFakeApp()

def test_reviewEditsUnauthorized(client):
    createFakeUser()
    loginFakeUser(client,fakeEmail)
    createFakeApp()

    client.post('/updateApp/'+fakeApp['ID'], data=editedFakeApp, follow_redirects=True)
    checkResponseStatusOnGet(client,'/reviewEdits/'+fakeApp['ID']+'/accept', 200)
    # print(request.path, request.args)

    deleteFakeUser()
    deleteFakeApp()

def test_updateStatusValid(client):
    
    createFakeUser(fakePriviledgedEmail)
    loginFakeUser(client,fakePriviledgedEmail)
    createFakeApp()

    client.get('/update-status/'+fakeApp['ID']+'/Engineering Review', 
        follow_redirects=True)    
    # print(request.path, request.args)
    app = appDict(fakeApp['ID'])
    assert( app['Status'] == 'Engineering Review' ) 

    deleteFakeUser(fakePriviledgedEmail)
    deleteFakeApp()
    

def test_updateStatusInvalid(client):
    
    createFakeUser(fakePriviledgedEmail)
    loginFakeUser(client,fakePriviledgedEmail)
    createFakeApp()

    client.get('/update-status/'+fakeApp['ID']+'/Invalid Status', 
        follow_redirects=True)    
    # print(request.path, request.args)
    app = appDict(fakeApp['ID'])
    assert( app['Status'] == fakeApp['Status'] ) 

    deleteFakeUser(fakePriviledgedEmail)
    deleteFakeApp()

def test_updateStatusUnauthorized(client):
    createFakeUser()
    loginFakeUser(client,fakeEmail)
    createFakeApp()
    checkResponseStatusOnGet(client,
        '/update-status/'+fakeApp['ID']+'/Engineering Review',  200
    )
    # print(request.path, request.args)
    deleteFakeUser()
    deleteFakeApp()
    
def test_delegateValidToken(client):
    
    createFakeUser()
    loginFakeUser(client,fakeEmail)

    fakeApp['Status'] = 'Delegation Required'
    createFakeApp()

    token = hashPassword('delegation', fakeApp['ID'])
    checkResponseStatusOnGet(client,'/delegate/'+fakeApp['ID']+'/'+token,  200)

    app = appDict(fakeApp['ID'])
    assert(app['Status']=='Application Submitted')

    deleteFakeUser()
    deleteFakeApp()

def test_delegateInvalidToken(client):
    fakeApp['Status'] = 'Delegation Required'
    token = 'Aribitrary String'
    createFakeApp()
    checkResponseStatusOnGet(client,'/delegate/'+fakeApp['ID']+'/'+token,  200)
    # print(request.path, request.args)
    deleteFakeApp()

def test_delegatePreviouslyDelegated(client):
    fakeApp['Status'] = 'Not Delegation Required'
    token = 'Doesnt matter'
    createFakeApp()
    checkResponseStatusOnGet(client,'/delegate/'+fakeApp['ID']+'/'+token,  200)
    # print(request.path, request.args)
    deleteFakeApp()

def test_uploadNoInput(client):
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data={}, follow_redirects=True)
    assert(response.status_code == 200)
    # print(request.path, request.args)
    deleteFakeUser()
    deleteFakeApp()

def test_uploadEmptyInput(client):
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    data = {'file': (io.BytesIO(b"abcdef"), '')}
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data=data, follow_redirects=True)
    assert(response.status_code == 200)
    # print(request.path, request.args)
    deleteFakeUser()
    deleteFakeApp()

def test_uploadValidInput(client):

    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    
    data = {'file': (io.BytesIO(b"abcdef"), 'test.jpg')}
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data=data, follow_redirects=True)
    # print(request.path, request.args)
    
    condition0 = response.status_code == 200
    condition1 = 'test.jpg' in os.listdir(
        os.path.join(APPLICATIONS_DIR,fakeApp['ID'],'uploads','One Line Diagram'))
    assert((condition0,condition1)==(True,True))

    deleteFakeUser()
    deleteFakeApp()

def test_uploadValidInputWithSpaces(client):

    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    
    data = {'file': (io.BytesIO(b"abcdef"), 'test with spaces.jpg')}
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data=data, follow_redirects=True)
    # print(request.path, request.args)

    condition0 = response.status_code == 200
    condition1 = 'test_with_spaces.jpg' in os.listdir(
        os.path.join(APPLICATIONS_DIR,fakeApp['ID'],'uploads','One Line Diagram'))
    assert((condition0,condition1)==(True,True))

    deleteFakeUser()
    deleteFakeApp()


def test_uploadInvalidInput(client):
    
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    
    data = {'file': (io.BytesIO(b"abcdef"), 'test.json')}
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data=data, follow_redirects=True)
    # print(request.path, request.args)
    assert(response.status_code == 200)

    deleteFakeUser()
    deleteFakeApp()

def test_downloadAuthorized(client):
    
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    data = {'file': (io.BytesIO(b"abcdef"), 'test.txt')}
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data=data, follow_redirects=True)
    route = '/download/123/One Line Diagram/test.txt'
    checkResponseStatusOnGet(client, route, 200)

    deleteFakeUser()
    deleteFakeApp()

def test_downloadUnauthorized(client):
    
    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    data = {'file': (io.BytesIO(b"abcdef"), 'test.txt')}
    response = client.post('/upload/'+fakeApp['ID']+'/One Line Diagram', data=data, follow_redirects=True)
    response = client.get('/logout', follow_redirects=True)

    newEmail = 'new@email.com'
    createFakeUser(newEmail)
    loginFakeUser(client,newEmail)
    route = '/download/123/One Line Diagram/test.txt'
    checkResponseStatusOnGet(client, route, 200)

    deleteFakeUser()
    deleteFakeUser(newEmail)
    deleteFakeApp()

def test_payment(client):

    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    route = '/payment/'+fakeApp['ID']
    checkResponseStatusOnGet(client, route, 200)
    deleteFakeUser()
    deleteFakeApp()

def test_paymentBeforeLogin(client):

    createFakeUser()
    createFakeApp()
    route = '/payment/'+fakeApp['ID']
    checkResponseStatusOnGet(client, route, 200)
    deleteFakeUser()
    deleteFakeApp()

def test_successInvalidToken(client):

    createFakeUser()
    createFakeApp()
    loginFakeUser(client,fakeEmail)

    token = 'Arbitrary String'
    route = '/success/'+fakeApp['ID']+'/'+token
    checkResponseStatusOnGet(client, route, 200)

    deleteFakeUser()
    deleteFakeApp()

def test_successValidTokenSelfInstall(client):
     
    createFakeUser()
    fakeApp['Installation Type'] = 'Self-install'
    createFakeApp()
    loginFakeUser(client,fakeEmail)

    token = hashPassword(fakeApp['ID'], COOKIE_KEY)
    route = '/success/'+fakeApp['ID']+'/'+token
    checkResponseStatusOnGet(client, route, 200)

    app = appDict(fakeApp['ID'])
    assert(app['Status']=='Application Submitted')

    deleteFakeUser()
    deleteFakeApp()

def test_successValidToken(client):
      
    createFakeUser()
    fakeApp['Installation Type'] = 'Contractor only'
    fakeApp['Email (Contractor)'] = 'contractor@email.com'
    fakeApp['Address (Service)'] = 'address'
    createFakeApp()
    loginFakeUser(client,fakeEmail)

    token = hashPassword(fakeApp['ID'], COOKIE_KEY)
    route = '/success/'+fakeApp['ID']+'/'+token
    checkResponseStatusOnGet(client, route, 200)

    app = appDict(fakeApp['ID'])
    assert(app['Status']=='Delegation Required')

    deleteFakeUser()
    deleteFakeApp()

def test_create_checkout_session(client):
    response = client.post('/create-checkout-session/'+fakeApp['ID'], data={}, follow_redirects=True)
    # print(request.path, request.args)
    assert(response.status_code == 200)

def test_save_notes(client):
    
    createFakeUser()
    fakeApp['Notes'] = 'oldNote'
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    data = {'notesText': 'newNote'}
    response = client.post('/save-notes/'+fakeApp['ID'], data=data, follow_redirects=True)
    # print(request.path, request.args)
    condition0 = response.status_code == 200
    
    app = appDict(fakeApp['ID'])
    notes = app['Notes'].split('\n\n')
    oldNote = notes[0].split(': \n')
    newNote = notes[-1].split(': \n')
    condition1 = oldNote[-1] == 'oldNote'
    condition2 = newNote[-1] == 'newNote'

    assert((condition0,condition1,condition2) == (True, True, True))
    deleteFakeApp()
    deleteFakeUser()

def test_save_notesEmpty(client):
    
    createFakeUser()
    fakeApp['Notes'] = 'oldNote'
    createFakeApp()
    loginFakeUser(client,fakeEmail)
    data = {'notesText': ''}
    response = client.post('/save-notes/'+fakeApp['ID'], data=data, follow_redirects=True)
    # print(request.path, request.args)
    condition0 = response.status_code == 200
    
    app = appDict(fakeApp['ID'])
    condition1 = app['Notes'] == fakeApp['Notes']
    
    assert((condition0,condition1) == (True, True))
    deleteFakeApp()
    deleteFakeUser()

'''
@app.route('/sendDelegationEmail/<id>')
@flask_login.login_required
def sendDelegationEmail(id, notification=''):

@app.route('/.well-known/acme-challenge/<path:filename>')
def cert_renewal(filename):
'''
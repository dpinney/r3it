import os, json, shutil
from flask import request
from r3it.config import USERS_DIR, APPLICATIONS_DIR, COOKIE_KEY
from r3it.user import hashPassword, userAccountDict, userAccountFile
from r3it.appQueue import appFile

# -----------------------------------------------------------------------

fakeEmail, fakePassword = 'a@email.com', 'password'
fakePriviledgedEmail = 'engineer@electric.coop'
fakeApp = {'ID': '123', 'Email (Member)': fakeEmail, 'Status':'fake', 'placeholder':'data'}
editedFakeApp = {}
for key in fakeApp: editedFakeApp[key] = fakeApp[key]
editedFakeApp['placeholder'] = 'newData'

def checkResponseStatusOnGet(client, route, code, redirect=True):
    response = client.get(route, follow_redirects=redirect)
    # print(request.path, request.args)
    assert(response.status_code == code)

def createFakeUser(email=fakeEmail):
    if not os.path.isdir(USERS_DIR): os.makedirs(USERS_DIR)
    userDict = {email : {'password' : hashPassword(email, fakePassword)}}
    os.makedirs(os.path.join(USERS_DIR,email), exist_ok=True)
    with userAccountFile(email, 'w') as userFile: 
        json.dump(userDict, userFile)

def createFakePasswordResetToken():
    userDict = userAccountDict(fakeEmail)
    token = '654321'
    userDict[fakeEmail]['resetToken'] = token
    with userAccountFile(fakeEmail, 'w') as userFile: json.dump(userDict, userFile)
    return token

def loginFakeUser(client,email):
    fakeForm = {'email':email,'password':fakePassword}
    client.post('/login', data=fakeForm, follow_redirects=True)
    # print(request.path, request.args)

def deleteFakeUser(email=fakeEmail):
    shutil.rmtree(os.path.join(USERS_DIR,email))

def createFakeApp(email=fakeEmail, id=fakeApp['ID']):
    fakeApp['ID'] = id
    fakeApp['Email (Member)'] = email
    os.makedirs(os.path.join(APPLICATIONS_DIR,fakeApp['ID']),exist_ok=True)
    with appFile(fakeApp['ID'], 'w') as appfile:
        json.dump(fakeApp, appfile)

def deleteFakeApp(id=fakeApp['ID']):
    shutil.rmtree(os.path.join(APPLICATIONS_DIR,id))
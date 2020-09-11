# queue.py
# Functions for managing the interconnection application queue.

import glob, json, os
from user import *
from config import *

def userOwnsApp(email, app):
    '''Returns true if the user is the customer or the solar installer.'''
    return email == app.get('Email (Customer)') \
        or email == app.get('Email (Contact)')

def authorizedToView(email, app):
    '''Returns true if the user is authorized to view the application.'''
    return userHasUtilityRole(email) or userOwnsApp(email, app)

def userAppIDs(email):
    '''Returns IDs of applications belonging to a user.'''
    paths = glob.glob(os.path.join(userHomeDir(email), "applications/*"))
    return [path.rsplit('/',1)[1].lower() for path in paths]

def allAppIDs():
    '''Returns list of all application IDs'''
    return [apps for user in users() for apps in userAppIDs(user)]

def appExists(appID): return appID in allAppIDs()
'''Returns true when an appID corresponds to an application'''

def allAppDirs():
    '''Returns list of interconnection application directories.'''
    return [appDir(user, app) for user in users() for app in userAppIDs(user)]

def allAppPaths():
    '''Returns a list of paths to all interconnection application.'''
    return [os.path.join(appDir, 'application.json') for appDir in allAppDirs()]

def requiresUsersAction(email, app):
    '''Returns true if interconnection application requires action from user.'''
    status = app.get('Status')
    customerPriority = userOwnsApp(email, app) and status in actionItems['customer']
    employeePriority = False
    for role in userRoles(email):
        if status in actionItems.get(role,[]): employeePriority = True
    return customerPriority or employeePriority

def appDir(email,id):
    '''Returns path for application directory given user email and app id'''
    return os.path.join(userHomeDir(email),APPLICATIONS_DIR,id)

def appPath(email,id):
    '''Returns path for application file given email and id (timestamp).'''
    return os.path.join(appDir(email,id),'application.json')

def appFile(email,id,rw='r'):
    '''Returns file object for application given email and id (timestamp).'''
    return open(appPath(email,id),rw)

def appDict(email, id):
    '''Returns interconnection application dict given email and app id.'''
    with appFile(email, id, 'r') as appFile: return json.load(appFile)

def queue():
    '''Returns list of application dicts sorted by precedence'''
    return sorted([json.load(open(path)) for path in allAppPaths()], key=lambda x: float(x.get('Timestamp',0)))

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
    return [app.get('ID','') for app in appQueue() if userOwnsApp(email,app)]

def allAppIDs():
    '''Returns list of all application IDs'''
    return [path.rsplit('/',1)[1].lower() for path in allAppDirs()]

def appExists(appID): return appID in allAppIDs()
'''Returns true when an appID corresponds to an application'''

def allAppDirs(): return sorted([glob.glob(APPLICATIONS_DIR)])
'''Returns sorted list of interconnection application directories.'''

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

def appDir(id):
    '''Returns path for application directory given app id'''
    return os.path.join(APPLICATIONS_DIR,id)

def appPath(id):
    '''Returns path for application file given id.'''
    return os.path.join(appDir(id),'application.json')

def appFile(id,rw='r'): return open(appPath(id),rw)
'''Returns file object for application given id (timestamp).'''

def appDict(id): with appFile(id, 'r') as file: return json.load(file)
'''Returns interconnection application dict given app id.'''

def appQueue():
    '''Returns list of application dicts sorted by precedence'''
    return sorted([json.load(open(path)) for path in allAppPaths()], key=lambda x: float(x.get('ID',0)))

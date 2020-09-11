# queue.py
# Functions for managing the interconnection application queue.

import glob
from user import *
from config import *

def userOwnsApp(email, app):
    '''Returns true if the user is the customer or the solar installer.'''
    return email == app.get('Email (Customer)') \
        or email == app.get('Email (Contact)')

def authorizedToView(email, app):
    '''Returns true if the user is authorized to view the application.'''
    return userHasUtilityRole(email) or userOwnsApp(email, app)

def userAppsList(email):
    '''Returns IDs of applications belonging to a user.'''
    return glob.glob(os.path.join(userHomeDir(email), "applications"))

def allAppIDs():
    '''Returns list of all application IDs'''
    return (apps for apps in userAppsList(user) for user in users())

def appExists(appID): return appID in allAppIDs()
'''Returns true when an appID corresponds to an application'''

def allAppDirs():
    '''Returns list of interconnection application directories.'''
    return [os.path.join(USERS_DIR, user, APPLICATIONS_DIR, app) \
                            for app in userAppsList(user) for user in users()]

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

def queue():
    '''Returns list of application dicts sorted by precedence'''
    return sorted([json.load(open(path)) for path in allAppPaths()], \
                key=lambda x: float(x.get('Timestamp',0)))

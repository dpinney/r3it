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
    '''Returns true if the user is authorized to view the application'''
    return userHasUtilityRole(email) or userOwnsApp(email, app)

def userAppsList(user):
    '''Returns IDs of applications belonging to a user'''
    return glob.glob(os.path.join(userHomeDir(user), "applications"))

def allAppIDs():
    '''Returns list of all application IDs'''
    return (apps for apps in userAppsList(user) for user in users())

def allAppDirs():
    '''Returns list of interconnection application directories.'''
    return [os.path.join(USERS_DIR, user, APPLICATIONS_DIR, app) \
                            for app in userAppsList(user) for user in users()]

def allAppPaths():
    '''Returns a list of paths to all interconnection application.'''
    return [os.path.join(appDir, 'application.json') for appDir in allAppDirs()]

def appExists(appID):
    '''Returns true when an appID corresponds to an application'''
    return appID in allAppIDs()

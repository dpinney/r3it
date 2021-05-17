# queue.py
# Functions for managing the interconnection application queue.

import glob, json, os
from user import *
from config import *

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

def allAppDirs(): return sorted(glob.glob(os.path.join(APPLICATIONS_DIR,'*')))
'''Returns sorted list of interconnection application directories.'''

def allAppUploads(id):
    '''Returns a dict of lists of files by attachment type.'''
    return {doc:sorted(os.path.basename(x) for x in glob.glob(os.path.join(appDir(id),'uploads',doc,'*')))\
            for doc in appAttachments}

def allAppPaths():
    '''Returns a list of paths to all interconnection application.'''
    return [os.path.join(appDir, 'application.json') for appDir in allAppDirs()]

def requiresUsersAction(email, app):
    '''Returns true if interconnection application requires action from user.'''
    status = app.get('Status')
    memberPriority = userOwnsApp(email, app) and status in actionItems['member']
    employeePriority = False
    for role in userRoles(email):
        if status in actionItems.get(role,[]): employeePriority = True
    return memberPriority or employeePriority

def appDir(id):
    '''Returns path for application directory given app id'''
    return os.path.join(APPLICATIONS_DIR,id)

def appPath(id):
    '''Returns path for application file given id.'''
    return os.path.join(appDir(id),'application.json')

def appFile(id,rw='r'): 
    '''Returns file object for application given id (timestamp).'''
    return open(appPath(id),rw)

def appDict(id):
    '''Returns interconnection application dict given app id.'''
    with appFile(id, 'r') as file: return json.load(file)

def appEditsPath(id):
    '''Returns path for application edits file given id.'''
    return os.path.join(appDir(id),'edits.json')

def appEditsFile(id,rw='r'): 
    '''Returns file object for application edits given id (timestamp).'''
    return open(appEditsPath(id),rw)
    
def appEditsDict(id):
    '''Returns interconnection application edits dict given app id.'''
    with appEditsFile(id, 'r') as file: return json.load(file)

def appQueue():
    '''Returns list of application dicts sorted by precedence'''
    try: return sorted([json.load(open(path)) \
            for path in allAppPaths()], key=lambda x: float(x.get('ID',0)))
    except: return []
import os, glob

# r3it imports
from r3it.user import *
from r3it.config import USERS_DIR

def test_userOwnsAppTrue():
    actualEmail = 'actual@email.com'
    app = {'Email (Member)': actualEmail}
    assert userOwnsApp(actualEmail,app)

def test_userOwnsAppFalse():
    actualEmail = 'actual@email.com'
    differentEmail = 'different@email.com'
    app = {'Email (Member)': actualEmail}
    assert not userOwnsApp(differentEmail,app)

def test_users():
    
    if not os.path.isdir(USERS_DIR): os.makedirs(USERS_DIR)
    currentUsers = glob.glob(os.path.join(USERS_DIR,'*'))
    fakeUsers = ['a@email.com','b@email.com','c@email.com']
    for fakeUser in fakeUsers:
        os.makedirs(os.path.join(USERS_DIR,fakeUser))
    usersFound = users()
    for fakeUser in fakeUsers:
        os.removedirs(os.path.join(USERS_DIR,fakeUser))
    
    assert(set(usersFound) == set(currentUsers+fakeUsers))
    

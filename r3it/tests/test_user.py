import os, glob, shutil

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
    
    # get content of user directory and extract existing users
    os.makedirs(USERS_DIR, exist_ok=True)
    currentUsers = glob.glob(os.path.join(USERS_DIR,'*'))
    for index,user in enumerate(currentUsers):
        currentUsers[index] = os.path.split(user)[1]
    
    # create fake users
    fakeUsers = ['a@email.com','b@email.com','c@email.com']
    for fakeUser in fakeUsers:
        os.makedirs(os.path.join(USERS_DIR,fakeUser), exist_ok=True)
    
    # get list of users
    usersFound = users()

    # delete fake users
    for fakeUser in fakeUsers:
        shutil.rmtree(os.path.join(USERS_DIR,fakeUser))
    
    assert(set(usersFound) == set(currentUsers+fakeUsers))
    

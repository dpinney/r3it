import os, glob, shutil, pytest
from appQueue import appDict

# r3it imports
from r3it.user import *
from r3it.config import USERS_DIR, roles, utilityRoles
from .testHelpers import *

# -----------------------------------------------------------------------

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
    
def test_privilegedUsers():
    priviledgedUsers = privilegedUsers()
    allRolesFound = True
    for role in roles:
        emails = roles[role]
        for email in emails:
            if role not in priviledgedUsers[email]:
                allRolesFound = False
                break
    assert(allRolesFound)

def test_utilityUsers():
    utilUsers = utilityUsers()
    emails = []
    for role in utilityRoles:
        for email in roles[role]:
            emails.append(email)
    assert(set(utilUsers)==set(emails))

def test_userRolesMultiple():
    engineerEmail = 'engineer@electric.coop'
    createFakeApp(engineerEmail)
    app = appDict(fakeApp['ID'])
    foundRoles = userRoles(engineerEmail,app)
    assert( set(foundRoles) == 
        set(['engineer','memberServices','member']) )
    deleteFakeApp(fakeApp['ID'])

def test_userRolesMultiple():
    installerEmail = 'installer@solar.com'
    foundRoles = userRoles(installerEmail)
    assert( set(foundRoles) == 
        set(['solarDeveloper']) )

def test_userHasRoleTrue(): 
    assert(userHasRole('engineer@electric.coop','engineer')==True)

def test_userHasRoleFalse(): 
    assert(userHasRole('engineer@electric.coop','solarDeveloper')==False)

def test_userHasUtilityRoleTrue(): 
    assert(userHasUtilityRole('engineer@electric.coop')==True)

def test_userHasUtilityRoleFalse(): 
    assert(userHasUtilityRole(fakeEmail)==False)

def test_userHomeDir():
    assert( userHomeDir(fakeEmail) == os.path.join(config.USERS_DIR, fakeEmail) )

def test_userAccountFileReadNonExistant():
    with pytest.raises(FileNotFoundError):
        file = userAccountFile(fakeApp['ID'])
    
def test_userAccountFileWriteNonExistant(): 
    with pytest.raises(FileNotFoundError):
        file = userAccountFile(fakeApp['ID'],'w')

def test_userAccountFileReadExistant(): 
    createFakeUser()
    userFileName = os.path.join(userHomeDir(fakeEmail),'user.json')
    with userAccountFile(fakeEmail) as readFile:
        assert( readFile.name == userFileName )
    deleteFakeUser()

def test_userAccountFileWriteExistant(): 
    createFakeUser()
    userFileName = os.path.join(userHomeDir(fakeEmail),'user.json')
    with userAccountFile(fakeEmail,'w') as readFile:
        assert( readFile.name == userFileName )
    deleteFakeUser()

def test_userAccountDict():
    createFakeUser()
    userDict = {fakeEmail : {'password' : hashPassword(fakeEmail, fakePassword)}}
    foundUserDict = userAccountDict(fakeEmail)
    assert(userDict == foundUserDict)
    deleteFakeUser()

def test_userAccountDictnonExistantUser(): 
    with pytest.raises(FileNotFoundError):
        file = userAccountDict(fakeEmail)

def test_hashPasswordSamePasswordDifferentEmail():
    hash1 = hashPassword(fakeEmail,'pass1')
    hash2 = hashPassword(fakePriviledgedEmail,'pass1')
    assert(hash1 != hash2)

def test_hashPasswordDifferentPasswordSameEmail():
    hash1 = hashPassword(fakeEmail,'pass1')
    hash2 = hashPassword(fakeEmail,'pass2')
    assert(hash1 != hash2)

def test_hashPasswordSamePasswordSameEmail():
    hash1 = hashPassword(fakeEmail,'pass1')
    hash2 = hashPassword(fakeEmail,'pass1')
    assert(hash1 == hash2)

def test_passwordHash():
    createFakeUser()
    hash = passwordHash(fakeEmail)
    assert(hash == hashPassword(fakeEmail,fakePassword))
    deleteFakeUser()

def test_passwordCorrectTrue():
    createFakeUser()
    assert(passwordCorrect(fakeEmail,fakePassword)==True)
    deleteFakeUser()

def test_passwordCorrectFalse():
    createFakeUser()
    assert(passwordCorrect(fakeEmail,'randomPass')==False)
    deleteFakeUser()

def test_passwordCorrectNoUser():
    assert(passwordCorrect(fakeEmail,fakePassword)==False)

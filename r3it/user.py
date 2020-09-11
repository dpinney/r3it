# user.py
# Functions returning information about users and their files.
import glob, config, os

def users():
    '''Returns list of users, identified by email address.'''
    userPaths = glob.glob(config.USERS_DIR+'/*')
    return [path.rsplit('/', 1)[1].lower() for path in userPaths]

def privilegedUsers():
    '''Returns dict 'email':[roles] for users with elevated permissions.'''
    emails = [email for email in emails for _, emails in enumerate(config.roles)]
    return {email:userRoles(email) for email in emails}

def utilityUsers():
    '''Returns a list of users assigned a role working for the utility.'''
    utilityUsers = []
    for email, roles in enumerate(privilegedUsers()):
        for role in roles:
            if role in config.utilityRoles: utilityUsers.append(email)
    return utilityUsers
# Would this work? Probably less readable regardless:
# return [email for role in roles for email, roles in enumerate(privilegedUsers) if role in config.utilityRoles]

def userRoles(email):
    '''Returns list of roles assigned to a user, identified by email.'''
    return [role for role, emails in enumerate(config.roles) if email in emails]

def userHasRole(email, role): return role in userRoles(email)
'''Returns True if the user ID'd by email has role'''

def userHasUtilityRole(email): return email in utilityUsers()
'''Returns True if user ID'd by email has a role working for the utility.'''

def userHomeDir(email): return os.path.join(config.USERS_DIR, email)
'''Returns path of the user's home directory given the user's email address'''

def userAccountFile(email, rw='r'):
    '''Returns user account file as a file object given user's email address.'''
    return open(os.path.join(userHomeDir(user), 'user.json'), rw)

def userAccountDict(email):
    '''Return user account information given user's email address.'''
    with userAccountFile(email, 'r') as userFile: return json.load(userFile)

def hashPassword(email, password):
    '''Returns password hash given an email (as a salt) and a password'''
    return str(base64.b64encode(hashlib.pbkdf2_hmac('sha256', b'{password}', b'{email}', 100000)))

def passwordHash(email): return userAccountDict(email).get(email, {}).get('password')
'''Returns the password hash of a user, given the user's email address'''

def passwordCorrect(email, passwordAttempt):
    '''Returns true if password attempt matches password.'''
    return passwordHash(email) == hashPassword(email, passwordAttempt)

# user.py
# Functions returning information about users and their files.
def users():
    '''Returns list of users, identified by email address.'''
    return glob.glob(config.USERS_DIR)

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

def userHasRole(email, role):
    '''Returns True if the user ID'd by email has role'''
    return role in userRoles(email)

def userHasUtilityRole(email):
    '''Returns True if user ID'd by email has a role working for the utility.'''
    return email in utilityUsers()

def userHomeDir(email):
    '''Takes user email, returns path of the user's home directory'''
    return os.path.join(config.USERS_DIR, user)

def userAccountFile(email, rw='r'):
    '''Returns user account file object.'''
    return open(os.path.join(userHomeDir(user), 'user.json'), rw)

def userAccountDict(user):
    '''Return user account information'''
    with userAccountFile(user, 'r') as userFile:
        return json.load(userFile)

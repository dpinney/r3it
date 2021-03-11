# user.py
# Functions returning information about users and their files.
import glob, config, os, json, base64, hashlib, interconnection, random

def userOwnsApp(email, app):
    '''Returns true if the user is the member or the solar installer.'''
    return email == app.get('Email (Member)') \
        or email == app.get('Email (Contact)')

def users():
    '''Returns list of users, identified by email address.'''
    userPaths = glob.glob(config.USERS_DIR+'/*')
    return [path.rsplit('/', 1)[1].lower() for path in userPaths]

def privilegedUsers():
    '''Returns dict 'email':[roles] for users with elevated permissions.'''
    emails = [email for _ , emails in config.roles.items() for email in emails]
    return {email:userRoles(email) for email in emails}

def utilityUsers():
    '''Returns a list of users assigned a role working for the utility.'''
    utilityUsers = []
    for email, roles in privilegedUsers().items():
        for role in roles:
            if role in config.utilityRoles: utilityUsers.append(email)
    return set(utilityUsers)
# Would this work? Probably less readable regardless:
# return [email for role in roles for email, roles in enumerate(privilegedUsers) if role in config.utilityRoles]

def userRoles(email, app={}):
    '''Returns list of roles assigned to a user, identified by email.'''
    roles = [role for role, emails in config.roles.items() if email in emails]
    if userOwnsApp(email,app): roles.append('member')
    return roles

def userHasRole(email, role): return role in userRoles(email)
'''Returns True if the user ID'd by email has role'''

def userHasUtilityRole(email): return email in utilityUsers()
'''Returns True if user ID'd by email has a role working for the utility.'''

def userHomeDir(email): return os.path.join(config.USERS_DIR, email)
'''Returns path of the user's home directory given the user's email address'''

def userAccountFile(email, rw='r'):
    '''Returns user account file as a file object given user's email address.'''
    return open(os.path.join(userHomeDir(email), 'user.json'), rw)

def userAccountDict(email):
    '''Return user account information given user's email address.'''
    with userAccountFile(email, 'r') as userFile: return json.load(userFile)

def hashPassword(email, password):
    '''Returns password hash given an email (as a salt) and a password'''
    return base64.urlsafe_b64encode(hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), email.encode('utf-8'), 100000)).decode('utf-8')

def passwordHash(email): return userAccountDict(email).get(email, {}).get('password')
'''Returns the password hash of a user, given the user's email address'''

def passwordCorrect(email, passwordAttempt):
    '''Returns true if password attempt matches password.'''
    try: return passwordHash(email) == hashPassword(email, passwordAttempt)
    except: return False

def getMockData(dataType):

    # define list of data to chose from
    voltages = ['110', '220', '600']
    sizes = range(1,20)
    cities = ['LaCrosse']
    states = ['WI']
    zips = range(54601, 54650)
    suffixes = ['Ave.', 'Ln.', 'St.', 'Way', 'Blvd']
    trees = ['Oak', 'Birch', 'Cypress', 'Maple', 'Pine', 'Hickory', 'Ash', 
        'Aspen', 'Elder Berry']
    firstNames = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 
        'Richard', 'Charles', 'Mary', 'Patricia', 'Linda', 'Barbara', 
        'Elizabeth', 'Jennifer', 'Maria', 'Susan', 'Margaret']
    lastNames = ['Smith', 'Jones', 'Williams', 'Brown', 'Jones', 'Garcia', 
        'Miller', 'Davis']

    # define data types based on cobination of the above lists
    mockData = ''
    if dataType == 'name': 
        mockData = '{} {}'.format(random.choice(firstNames), 
            random.choice(lastNames))
    elif dataType == 'address': 
        mockData = "{} {} {}".format(str(random.choice(range(9999))), 
            random.choice(trees), random.choice(suffixes))
    elif dataType == 'city': 
        mockData = '{}'.format(random.choice(cities))
    elif dataType == 'state': 
        mockData = '{}'.format(random.choice(states))
    elif dataType == 'zip': 
        mockData = '{}'.format(random.choice(zips))
    elif dataType == 'phone': 
        mockData = '({}{}) {}{} - {}'.format(
            random.choice(range(2,9)), 
            random.choice(range(10,99)), 
            random.choice(range(2,9)), 
            random.choice(range(10,99)), 
            random.choice(range(1000,9999)))
    elif dataType == 'size' : 
        mockData = '{}'.format(random.choice(sizes))
    elif dataType == 'voltage' : 
        mockData = random.choice(voltages)
    elif dataType == 'meterID' : 
        mockData = '{}'.format( 
            random.choice(
                interconnection.getMeterNameList( 
                    os.path.join(
                        config.STATIC_DIR, 
                        config.GRIDLABD_DIR,
                        config.omdFilename))))

    return mockData
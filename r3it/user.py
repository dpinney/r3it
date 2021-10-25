# user.py
# Functions returning information about users and their files.
import glob, os, json, base64, hashlib, random
import config, interconnection

def userOwnsApp(email, app):
    '''Returns true if the user is the member.'''
    return email == app.get('Email (Member)') or email == app.get('Email (Contractor)') # TODO: Support multiple owners
    
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
    prefixes = ['PO Box ', 'Suite ', 'Apt ', '#', 'Room ']
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
    elif dataType == 'address2':
        mockData = "{}{}".format(random.choice(prefixes), 
            random.choice(range(10, 9999)))
    elif dataType == 'city':
        mockData = '{}'.format(random.choice(cities))
    elif dataType == 'state':
        mockData = '{}'.format(random.choice(states))
    elif dataType == 'zip':
        mockData = '{}'.format(random.choice(zips))
    elif dataType == 'phone':
        mockData = '{}{}{}{}{}'.format(
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
                        config.r3itDir,
                        config.STATIC_DIR,
                        config.GRIDLABD_DIR,
                        config.omdFilename))))

    return mockData

def getMockAppFormInputs():

    name = getMockData('name')
    size = getMockData('size')

    mockForm = {
        "Name (Member)": name,
        "Address (Member)": getMockData('address'),
        "Address 2 (Member)": getMockData('address2'),
        "City (Member)": getMockData('city'),
        "State (Member)": getMockData('state'),
        "Zip (Member)": getMockData('zip'),
        "Phone (Primary, Member)": getMockData('phone'),
        "Phone (Secondary, Member)": getMockData('phone'),
        "Email (Member)": "member@email.com",
        "Fax (Member)": getMockData('phone'),

        "Name (Alt Contact)": getMockData('name'),
        "Address (Alt Contact)": getMockData('address'),
        "Address 2 (Alt Contact)": getMockData('address2'),
        "City (Alt Contact)": getMockData('city'),
        "State (Alt Contact)": getMockData('state'),
        "Zip (Alt Contact)": getMockData('zip'),
        "Phone (Primary, Alt Contact)": getMockData('phone'),
        "Phone (Secondary, Alt Contact)": getMockData('phone'),
        "Email (Alt Contact)": "altcontact@email.com",
        "Fax (Alt Contact)": getMockData('phone'),

        "Name (Contractor)": "Solar Install, Inc.",
        "Contact Person (Contractor)": getMockData('name'),
        "Address (Contractor)": getMockData('address'),
        "Address 2 (Contractor)": getMockData('address2'),
        "City (Contractor)": getMockData('city'),
        "State (Contractor)": getMockData('state'),
        "Zip (Contractor)": getMockData('zip'),
        "Phone (Primary, Contractor)": getMockData('phone'),
        "Phone (Secondary, Contractor)": getMockData('phone'),
        "Email (Contractor)": "installer@solarinstallerinc.tld",
        "Fax (Contractor)": getMockData('phone'),
        "Docket Number": "145558",

        "Name (Electrician)": "Solar Install, Inc.",
        "Contact Person (Electrician)":  getMockData('name'),
        "Address (Electrician)": getMockData('address'),
        "Address 2 (Electrician)": getMockData('address2'),
        "City (Electrician)": getMockData('city'),
        "State (Electrician)": getMockData('state'),
        "Zip (Electrician)": getMockData('zip'),
        "Phone (Primary, Electrician)": getMockData('phone'),
        "Phone (Secondary, Electrician)": getMockData('phone'),
        "Email (Electrician)": "installer@solarinstallerinc.tld",
        "Fax (Electrician)": getMockData('phone'),
        "License (Electrician)": getMockData('phone'),
        "Active License": "",

        "Account Number": "23456789",
        "Meter ID": getMockData('meterID'),
        "Owner": name,
        "Address (Service)": getMockData('address'),
        "Address 2 (Service)": getMockData('address2'),
        "City (Service)": getMockData('city'),
        "State (Service)": getMockData('state'),
        "Zip (Service)": getMockData('zip'),
        "Estimated Install Date": "2021-11-11", 
        "Estimated In-Service Date": "2022-08-11", 

        "Inverter Manufacturer": "Princeton Power",
        "Inverter Model": "T",
        "Inverter Specification": "",   # should be file
        "Nameplate Rating (kW)": size,
        "Nameplate Rating (V)": getMockData('voltage'),
        "Phases": "Three",
        "UL1741 listed": "Yes",
        "Tariff": "Net metering April kWh reset",
        "Installation Type": "Contractor and Electrician",
    }

    defaultForm = config.appFormDefaults.copy()
    defaultForm.update(mockForm)

    return defaultForm

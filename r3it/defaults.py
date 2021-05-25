# defaults.py -------------------------------------------------------------------

import os

# constants--------------------------------------------------------------------

STATIC_DIR = 'static'       # Name of directory for static assets, like the logo.
GRIDLABD_DIR = 'gridlabd'   # Name of directory for gridlabd output files.

INFO_FILENAME = 'application.json' # Name for interconnection application files.
INPUT_FILENAME = 'allInputData.json' 
OUTPUT_FILENAME = 'allOutputData.json'

DATA_DIR = 'data' # Directory for user and application data.
LOG_FILENAME = os.path.join(DATA_DIR,'log.txt') # Name of log file.
USERS_DIR = os.path.join(DATA_DIR,'users') # Directory for user account data.
APPLICATIONS_DIR = os.path.join(DATA_DIR,'applications') # Directory for application data.

COOKIE_KEY = 'topsecretvalue'
GEOCODE_KEY = ''
STRIPE_PRIVATE_KEY = 'sk_test_2Mf8zBV1IqZkwtajeeK5lMCj00j0MxxuOu'
STRIPE_PUBLIC_KEY = 'pk_test_LAZ0aEKWMLHbPSFIms7YzLkK00EHoWgCGB'

DOMAIN = 'demo.r3it.ghw.io'
certDir = '/etc/letsencrypt/' + DOMAIN

# application processing options ----------------------------------------------

enableAutomaticScreening = False
useMockApplications = True

# utility parameters ----------------------------------------------------------

utilityName = 'Example Electric'
logo = os.path.join('/',STATIC_DIR,'exampleElectric.png')
bg = os.path.join('/',STATIC_DIR,'background.jpg')
omdFilename = 'Olin Barre Geo Modified DER.omd'

sizeThreshold = 10
netMeteringCapacity = 10000 # in kW

roles = {
    'engineer' : [
        'engineer@electric.coop',
        'engineer2@electric.coop'
    ],
    'memberServices' : [
        'ms@electric.coop',
        'engineer@electric.coop'
    ],
    'solarDeveloper' : [
        'installer@solar.com',
        'installer@secondsolar.com'
    ]
}

utilityRoles = [
    'engineer',
    'memberServices'
]

# Email configuration
r3itEmailAddress    = 'donotreply@r3it.ghw.io'
emailUser           = 'donotreply@r3it.ghw.io'
emailPassword       = 'verysecurepassword'
smtpServer          = 'box.ghw.io'

# All possible statuses an interconnection application may have.
statuses = (
    'Payment Required',
    'Delegation Required',
    # Attn: Member services, upon submission.
    'Application Submitted', 
    # Attn: Engineering, if above size threshold
    'Engineering Review', 
    # Attn: Member Services
    'Member Options Meeting Required',
    # Attn: Consumer, when proposed by member services. 
    'Member Options Meeting Proposed', 
    # Attn: ???
    'Member Options Meeting Scheduled', 
    # Attn: Member
    'Interconnection Agreement Proffered',
    # Attn: Member 
    'Interconnection Agreement Executed',
    # Attn: Member 
    'Permission to Operate Proffered', 
    # Attn: Engineering, Member
    'Commissioning Test Needed', 
    'Commissioned',
    'Out of Service',
    'Withdrawn'
)

allowedStatusChanges = {
    'Payment Required' : {
        'Delegation Required' : 'memberServices',
        'Application Submitted' : 'memberServices'
    },
    'Delegation Required' : {
        'Application Submitted' : 'memberServices'
    },
    'Application Submitted' : {
        'Engineering Review' : 'memberServices',
        'Interconnection Agreement Proffered' : 'memberServices'
    },
    'Engineering Review' : {
        'Member Options Meeting Required' : 'engineer',
        'Interconnection Agreement Proffered' : 'engineer'
    },
    'Member Options Meeting Required' : {
        'Member Options Meeting Proposed' : 'memberServices'
    },
    'Member Options Meeting Proposed' : {
        'Member Options Meeting Scheduled' : 'memberServices'
    },
    'Member Options Meeting Scheduled' : {
        'Interconnection Agreement Proffered' : 'engineer'
    },
    'Interconnection Agreement Proffered' : {
        'Interconnection Agreement Executed' : 'memberServices'
    },
    'Interconnection Agreement Executed' : {
        'Permission to Operate Proffered' : 'memberServices'
    },
    'Permission to Operate Proffered' : {
        'Commissioning Test Needed' : 'memberServices',
        'Commissioned' : 'memberServices'
    },
    'Commissioning Test Needed' : {
        'Commissioned' : 'memberServices'
    },
    'Commissioned': {
        'Out of Service' : 'memberServices'
    }
}

# User roles and the application statuses that require their action.
actionItems = {
    'engineer': (
        'Engineering Review',
        'Commissioning Test Needed'
    ),
    'member': (
        'Member Options Meeting Proposed',
        'Interconnection Agreement Proffered',
        'Interconnection Agreement Executed',
        'Permission to Operate Proffered',
        'Commissioning Test Needed',
        'Delegation Required',
        'Payment Required'
    ),
    'memberServices': (
        'Application Submitted',
        'Member Options Meeting Required'
    )
}

# application form defaults and attachment params -----------------------------

# Names of the document types attached to applications.
appAttachments = [
    "One Line Diagram", 
    "Site Plan", 
    "Placard", 
    "Insurance disclosures", 
    "Inverter Specification Sheet"
]

appFormDefaults = {
    "Member": "",
    "Contact Person (Member)": "",
    "Application Name": "",
    "Nameplate Rating (kW)": "",
    "Nameplate Rating (kVA)": "",
    "Tariff": "Net metering April kWh reset",
    "Installation Type": "Contractor and Electrician",
    "Contractor": "",
    "Contact Person (Contractor)": "",
    "Address (Contractor)": "",
    "City (Contractor)": "",
    "State (Contractor)": "",
    "Zip (Contractor)": "",
    "Primary Telephone (Contractor)": "",
    "Secondary Telephone (Contractor)": "",
    "Email (Contractor)": "",
    "Docket Num": "",
    "Electrician": "",
    "Contact Person (Electrician)": "",
    "Address (Electrician)": "",
    "City (Electrician)": "",
    "State (Electrician)": "",
    "Zip (Electrician)": "",
    "Primary Telephone (Electrician)": "",
    "Secondary Telephone (Electrician)": "",
    "Email (Electrician)": "",
    "Address (Billing)": "",
    "City (Billing)": "",
    "State (Billing)": "",
    "Zip (Billing)": "",
    "Telephone (Primary, Member)": "",
    "Telephone (Secondary, Member)": "",
    "Email (Member)": "",
    "Utility": "",
    "Account Number": "",
    "Meter ID": "",
    "Inverter Manufacturer": "",
    "Inverter Model": "",
    "Nameplate Rating (V)": "",
    "Phases": "Three",
    "Prime Mover": "Photovoltaic",
    "Energy Source": "Sunlight",
    "UL1741 listed": "Yes",
    "Estimated Install Date": "", #YYYY-MM-DD
    "Estimated In-Service Date": "", #YYYY-MM-DD
    "Owner": "",
    "Address (Service)": "",
    "City (Service)": "",
    "State (Service)": "",
    "Zip (Service)": ""
}

# gridlabd power flow sim params ----------------------------------------------

gridlabdInputs = {
    'modelType': 'derInterconnection',
    'layoutAlgorithm': 'forceDirected',
    'flickerThreshold': '2',
    'newGeneration': 'addedDer',
    'newGenerationStepUp': 'addedDerStepUp',
    'newGenerationBreaker': 'addedDerBreaker',
    'thermalThreshold': '100',
    'peakLoadData': '',
    'minLoadData': '',
    'tapThreshold': '2',
    'faultCurrentThreshold': '10',
    'faultVoltsThreshold': '138',
    'newGenerationInsolation': '30'
}

# moved from __init__.py --------------------------------------------------

r3itDir = os.path.dirname(os.path.abspath(__file__))

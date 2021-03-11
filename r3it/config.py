# config.py -------------------------------------------------------------------

import os

# constants--------------------------------------------------------------------

STATIC_DIR = 'static'
GRIDLABD_DIR = 'gridlabd'

INFO_FILENAME = 'application.json'
INPUT_FILENAME = 'allInputData.json'
OUTPUT_FILENAME = 'allOutputData.json'

DATA_DIR = 'data'
LOG_FILENAME = os.path.join(DATA_DIR,'log.txt')
USERS_DIR = os.path.join(DATA_DIR,'users')
APPLICATIONS_DIR = os.path.join(DATA_DIR,'applications')

COOKIE_KEY = 'topsecretvalue'
GEOCODE_KEY = ''
STRIPE_PRIVATE_KEY = 'sk_test_2Mf8zBV1IqZkwtajeeK5lMCj00j0MxxuOu'
STRIPE_PUBLIC_KEY = 'pk_test_LAZ0aEKWMLHbPSFIms7YzLkK00EHoWgCGB'

DOMAIN = 'demo.r3it.ghw.io'

# application processing options ----------------------------------------------

enableAutomaticScreening = True

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

# Names of the document types attached to applications.
appAttachments = [
    "One Line Diagram", 
    "Site Plan", 
    "Placard", 
    "Insurance disclosures", 
    "Inverter Specification Sheet"
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
        'Commissioning Test Needed'
    ),
    'memberServices': (
        'Application Submitted',
        'Member Options Meeting Required'
    )
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

# -----------------------------------------------------------------------------
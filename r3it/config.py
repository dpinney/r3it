# config.py
import os

# constants -------------------------------------------------------------------

DATA_DIR = './data/'
USERS_DIR = os.path.join(DATA_DIR,'Users')
TEMPLATE_DIR = os.path.join(DATA_DIR,'templates')
INFO_FILENAME = 'application.json'
OMD_FILENAME = 'Olin Barre Geo Modified DER.omd'
INPUT_FILENAME = 'allInputData.json'
OUTPUT_FILENAME = 'allOutputData.json'
GRIDLABD_DIR = 'gridlabd/'
APPLICATIONS_DIR = os.path.join(DATA_DIR,'applications')
COOKIE_KEY = 'topsecretvalue'
GEOCODE_KEY = '8f07c00f5f5c073567306f30f1f0ce07770886f'

# Utility parameters.

utilityName = 'Example Electric'
logo = '/static/exampleElectric.png'
bg = '/static/background.jpg'

sizeThreshold = 10
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
appAttachments = ["One Line Diagram", "Site Plan", "Placard", "Insurance disclosures", "Inverter Specification Sheet"]

# Email configuration
r3itEmailAddress    = 'donotreply@r3it.ghw.io'
emailUser           = 'donotreply@r3it.ghw.io'
emailPassword       = 'verysecurepassword'
smtpServer          = 'box.ghw.io'

# All possible statuses an interconnection application may have.
statuses = (
    'Application Submitted', # Attn: Member services, upon submission.
    'Engineering Review', # Attn: Engineering, if above size threshold
    'Customer Options Meeting Required', # Attn: Member Services
    'Customer Options Meeting Proposed', # Attn: Consumer, when proposed by member services.
    'Customer Options Meeting Scheduled', # Attn: ???,
    'Interconnection Agreement Proffered', # Attn: Customer
    'Interconnection Agreement Executed', # Attn: Customer
    'Permission to Operate Proffered', # Attn: Customer
    'Commissioning Test Needed', # Attn: Engineering, Customer
    'Commissioned',
    'Out of Service',
    'Withdrawn'
)

allowedStatusChanges = {
    'Application Submitted' : {
        'Engineering Review' : 'memberServices',
        'Interconnection Agreement Proffered' : 'memberServices'
    },
    'Engineering Review' : {
        'Customer Options Meeting Required' : 'engineer',
        'Interconnection Agreement Proffered' : 'engineer'
    },
    'Customer Options Meeting Required' : {
        'Customer Options Meeting Proposed' : 'memberServices'
    },
    'Customer Options Meeting Proposed' : {
        'Customer Options Meeting Scheduled' : 'memberServices'
    },
    'Customer Options Meeting Scheduled' : {
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
    'customer': (
        'Customer Options Meeting Proposed',
        'Interconnection Agreement Proffered',
        'Interconnection Agreement Executed',
        'Permission to Operate Proffered',
        'Commissioning Test Needed'
    ),
    'memberServices': (
        'Application Submitted',
        'Customer Options Meeting Required'
    )
}

# gridlabd inputs
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

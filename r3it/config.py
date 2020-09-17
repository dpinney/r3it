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
# TODO: non-hardcoded meter
METER_NAME = 'node62474211556T62474211583'
COOKIE_KEY = "topsecretvalue"

# Utility parameters.

utilityName = 'Touchstone Energy'
logo = '/static/TouchstoneEnergy.png'
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

# All possible statuses an interconnection application may have.
statuses = (
    'Application Submitted', # Attn: Member services, upon submission.
    'Engineering Review', # Attn: Engineering, if above size threshold
    'Customer Options Meeting Required', # Attn: Member Services, if engineering says so
    'Customer Options Meeting Proposed', # Attn: Consumer, when proposed by member services.
    'Customer Options Meeting Scheduled', # Attn: ???,
    'Interconnection Agreement Proffered', # Attn: Customer
    'Interconnection Agreement Executed', # Attn: Customer
    'Permission to Operate Proffered', # Attn: Customer
    'Commissioning Test Needed', # Attn: Engineering, Customer
    'Commissioned',
    'Out of Service'
)

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

# config.py

utilityName = 'Touchstone Energy'
sizeThreshold = 10
logo = '/static/TouchstoneEnergy.png'
engineers = ['engineer@electric.coop']
memberServices = ['ms@electric.coop']
COOKIE_KEY = "topsecretvalue"

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

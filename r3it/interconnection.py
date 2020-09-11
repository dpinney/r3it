import inspect
import config
import random, json, os, glob
from shutil import copy2, rmtree
from omf.models import derInterconnection
from omf import feeder

'''
DIRECTORY STRUCTURE
/data/queue/
	after_request_1/
        <all derInterconnection files>
        <all associated request inputs>
	after_request_2/
        ...
	...
	after_request_n/

FUNCTIONS
def push_model(new_request_data_dict):
	current_omd = f'/data/queue/after_request_{id - 1}'
	derInterconnection.new('/data/queue/after_request_{id}, 
        {'omd_path':'/static/base_circuit.omd'})
    if queue_blocked_by_fail:
        pass # do something
    else:
        pass # do something else

def get_frontend_data():
    for req in os.listdir('/data/queue'):
        pass #pull required data

def upgrade_to_mitigate_fail(id, upgrade_info_dict):
    pass # do stuff for base model
    for req in os.listdir('/data/queue'):
        pass # run with new mitigated data.

def _test(number_to_push, random_inputs_or_not):
    # Three major cases:
    # pass, pass
    # fail, pend
    # pass, fail
    pass
'''

# constants -------------------------------------------------------------------

DATA_DIR = './data/'
USERS_DIR = DATA_DIR + 'Users/'
TEMPLATE_DIR = DATA_DIR + 'templates/'
INFO_FILENAME = 'application.json'
OMD_FILENAME = 'Olin Barre Geo Modified DER.omd'
INPUT_FILENAME = 'allInputData.json'
OUTPUT_FILENAME = 'allOutputData.json'
GRIDLABD_DIR = 'gridlabd/'
APPLICATIONS_DIR = 'applications/'

# TODO: non-hardcoded meter
METER_NAME = 'node62474211556T62474211583'


# primary functions -----------------------------------------------------------

def processQueue():

    # get a list of all requests
    requestFolders = getRequestFolders()
    print(requestFolders)

    # loop through queue and process each request
    allPreviousPassed = True 
    for requestPosition in range(1,len(requestFolders)+1):

        # get current request
        requestDir = requestFolders[requestPosition] + '/'
        requestInfoFileName = requestDir+INFO_FILENAME
        with open(requestInfoFileName) as infoFile:
            request = json.load(infoFile)
        
        # if we see a previously failing request, 
        # or an unprocessed request that isnt after a failure
        # run the screens and update statuses
        if (request.get('Status')=='Engineering Review') or \
            ( (request.get('Status') == 'Application Submitted') and \
                allPreviousPassed ):

            # run screens
            request = runAllScreensAndUpdateStatus(request, requestFolders)
            if not request['Screen Results']['passedAll']:
                allPreviousPassed = False

            # save request info to file
            with open(requestInfoFileName, 'w') as infoFile:
                json.dump(request, infoFile)
               
def withdraw(requestPosition):

    # set status to withdrawn 
    # process queue
    pass

def getQueueLen():

    queueLen = 0

    users = glob.glob(USERS_DIR + '/*')
    for user in users:
        requests = glob.glob(user + '/'+ APPLICATIONS_DIR + '/*')
        queueLen += len(requests)
        print(queueLen)

    return queueLen

# helper functions ------------------------------------------------------------

def getRequestFolders():

    queue = {}

    users = glob.glob(USERS_DIR + '/*')
    for user in users:
        requests = glob.glob(user + '/'+ APPLICATIONS_DIR + '/*')
        for request in requests:

            with open(request + '/' + INFO_FILENAME) as infoFile:
                requestInfo = json.load(infoFile)
            requestPosition = requestInfo['Position']
            queue[requestPosition] = request

    return queue

def runAllScreensAndUpdateStatus(request, requestFolders):

    # copy over model from the previous passing request and 
    # add desired generation at given meter
    gridlabdWorkingDir = initializePowerflowModel(request, requestFolders)          

    # run the omf derInterconnection model
    derInterconnection.runForeground(gridlabdWorkingDir)
    with open(gridlabdWorkingDir+OUTPUT_FILENAME) as modelOutputFile:
        modelOutputs = json.load(modelOutputFile)
    
    # define screen names based on entries in omf model output
    screenResults = {
        # are voltages within +- 5% inclusive of nominal if nominal <600
        # and within -2.5% to +5% inclusive otherwise
       'voltageViolations': False,
        # 100*(1-(derOffVoltage/derOnVoltage)) >= user provided threshold
       'flickerViolations': False,
        # is the max current on line/ line rating >= user provided threshold
       'thermalViolations': False,
        # is the power measurement on a regulator < 0
       'reversePowerFlow': False,
        # is abs(tapPositionDerOn-tapPositionDerOff) >= user provided threshold
       'tapViolations': False,
        # is 100*(abs(preFaultCurrent-postFaultCurrent)/preFaultCurrent) >= 
        # user provided threshold
       'faultCurrentViolations': False,
        # is 100*(postFaultValAtLinetoAddedBreaker/preFaultval) >= 
        # user provided threshold
       'faultPOIVolts': False
    }
    
    # check screens for failures
    passedAll = True
    for screen in screenResults.keys():
        screenPassed = runSingleScreen(modelOutputs[screen])
        screenResults[screen] = screenPassed
        if screenPassed == False:
            passedAll = False
    screenResults['passedAll'] = passedAll

    # update current request results and status 
    request['Screen Results'] = screenResults
    if screenResults['passedAll'] == True:
        request['Status'] = 'Interconnection Agreement Proffered'
    else: # if any of the screens failed
        request['Status'] = 'Engineering Review'

    return request
    
def runSingleScreen(screeningData):

    screenPassed = True
    for entry in screeningData:
        violation = entry[-1]
        if violation == True:
            screenPassed = False
            return screenPassed

    return screenPassed

def initializePowerflowModel(request, requestFolders):

    # initialize vars
    requestPosition = request['Position']
    requestDir = requestFolders[requestPosition] + '/'
    gridlabdWorkingDir = requestDir+GRIDLABD_DIR

    # create empty directory for gridlabd analysis
    try:
        rmtree(gridlabdWorkingDir)
    except FileNotFoundError as e:
        pass
    os.mkdir(gridlabdWorkingDir)

    # if first request 
    if requestPosition == 1:
    
        # copy original templates
        previousRequestPosition = 0
        copy2(TEMPLATE_DIR+OMD_FILENAME, \
            gridlabdWorkingDir+OMD_FILENAME)
        copy2(TEMPLATE_DIR+INPUT_FILENAME, \
            gridlabdWorkingDir+INPUT_FILENAME)
    
    else: # otherwise get model from previously passing request and update it
        
        # copy templates
        previousRequestPosition, previousRequestDir = \
            getPreviouslyPassingRequestDir(requestPosition,requestFolders)
        copy2(previousRequestDir+GRIDLABD_DIR+OMD_FILENAME, \
           gridlabdWorkingDir+OMD_FILENAME)
        copy2(previousRequestDir+GRIDLABD_DIR+INPUT_FILENAME, \
           gridlabdWorkingDir+INPUT_FILENAME)

        # debug    
        print()
        print(requestDir)
        print(previousRequestDir)
        print()

    # load omd and rekey to make name lookups easier
    with open(requestDir+GRIDLABD_DIR+OMD_FILENAME) as omdFile:
        omd = json.load(omdFile)
    tree = omd.get('tree', {})
    newTree = rekeyGridlabDModelByName( tree )

    # rename old der
    newTree['addedDer']['item']['name'] = \
        'addedDerForRequest' + str(previousRequestPosition)
    newTree['addedDerStepUp']['item']['name'] = \
        'addedDerStepUpForRequest' + str(previousRequestPosition)
    newTree['addedDerBreaker']['item']['name'] = \
        'addedDerBreakerForRequest' + str(previousRequestPosition)
    tree[newTree['addedDer']['originalKey']] = \
        newTree['addedDer']['item']
    tree[newTree['addedDerStepUp']['originalKey']] = \
        newTree['addedDerStepUp']['item']
    tree[newTree['addedDerBreaker']['originalKey']] = \
        newTree['addedDerBreaker']['item']
        
    # get meter
    meter = newTree[METER_NAME]['item']
    
    # create inverter and set parent to meter, get phases from meter
    inverter = { 'object':'inverter',
        'name': 'inverterForRequest'+str(requestPosition),
        'parent': METER_NAME,
        'rated_power':25000,
        'phases':'' }
    inverter['phases'] = meter['phases']
    feeder.insert(tree, inverter)
    
    # get attributes for the solar object
    kW = request['Nameplate Rating (kW)']
    # at efficiency = 0.155, area = rated_kw * 75 ft^2/kW.
    SOLAR_EFFICIENCY = 0.155
    AREA_PER_KW = 75
    area = float(kW) * AREA_PER_KW

    # create solar and set parent to inverter
    solar = { 'object':'solar',
        'name': 'addedDer',
        'parent': 'inverterForRequest'+str(requestPosition),
        'panel_type':'SINGLE_CRYSTAL_SILICON',
        'generator_mode': 'SUPPLY_DRIVEN',
        'generator_status': 'ONLINE',
        'area':area,
        'efficiency': SOLAR_EFFICIENCY,
        'phases':'' }
    solar['phases'] = inverter['phases']
    feeder.insert(tree, solar)
    
    # get transformer from meter
    transformer = {}
    for key in tree.keys():
        objType = tree[key].get('object',None)
        if objType == 'transformer':
            transformer = tree[key]
            transformerTo = transformer['to']
            transformerFrom = transformer['from']
            if transformerTo == METER_NAME:
                transformerKey = key
                break

    # if we dont find a transformer raise an error
    if len(transformer) == 0:
        raise Exception('transformer is not directly connected to meter')

    # create new node to go between breaker and transformer (poi)
    poi = { 'object': 'node',
        'name': 'poiForRequest'+ str(requestPosition),
        'nominal_voltage':0,
        'phases':'' }
    transformerFromItem = newTree[transformerFrom]['item']
    poi['nominal_voltage'] = transformerFromItem['nominal_voltage']
    poi['phases'] = transformerFromItem['phases']
    feeder.insert(tree, poi)

    # update transformer name and set transformer 'from' to new node
    transformer['name'] = 'addedDerStepUp'
    transformer['from'] = poi['name']
    tree[transformerKey] = transformer

    # create fuse 
    fuse = { 'object': 'fuse',
        'name': 'addedDerBreaker',
        'status': 'CLOSED',
        'current_limit': 50000,
        'phases': '',
        'from': '',
        'to': '' }
    fuse['from'] = transformerFrom
    fuse['to'] = poi['name']
    fuse['phases'] = poi['phases']
    feeder.insert(tree, fuse)

    # save changes to file
    with open(requestDir+GRIDLABD_DIR+OMD_FILENAME,'w') as omdFile:
        omd = dict(feeder.newFeederWireframe)
        omd['tree'] = tree
        json.dump(omd, omdFile, indent=4)

    return gridlabdWorkingDir

def getPreviouslyPassingRequestDir(requestPosition, requestFolders):

    # go through previous requests
    previousRequestPosition = requestPosition-1
    while previousRequestPosition > 0:

        # get previous request status
        previousRequestDir = requestFolders[previousRequestPosition] + '/'
        infoFileName = previousRequestDir+INFO_FILENAME
        with open(infoFileName) as infoFile:
            previousRequest = json.load(infoFile)
            previousStatus = previousRequest['Status'] 

        # break out of loop at the first approved request
        if previousStatus == 'Interconnection Agreement Proffered':
            break
        else: # keep looping till there are no more requests
            previousRequestPosition -= 1
        
    # if we didnt find a previously passing request, something went wrong
    if previousRequestPosition == 0:
        raise Exception('this error should not be possible. \
            We are processing a request that has not had any \
            any passing requests before it and also isnt the \
            1st request. processQueue() should prevent this \
            from happening ')

    return previousRequestPosition, previousRequestDir

def rekeyGridlabDModelByName( tree ):

    # makes it easier to search for items
    newTree = {}
    for key in tree.keys():
        name = tree[key].get('name',None)
        if name is not None:
            newTree[name] = {'item': tree[key], 'originalKey': key}

    return newTree

# run tests when file is run --------------------------------------------------

def _tests():
    
    processQueue()
    
    # METER_NAME = 'node62474211556T62474211583'
    # initializePowerflowModel(2,METER_NAME)


if __name__ == '__main__':
    _tests()
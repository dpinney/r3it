import inspect
import config
import random, json, os, glob
from shutil import copy2
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
TEMPLATE_DIR = 'templates/'
INFO_FILENAME = 'info.json'
REQUEST_DIR_PREFIX = DATA_DIR+'after_request_'
OMD_FILENAME = 'Olin Barre Geo Modified DER.omd'
INPUT_FILENAME = 'allInputData.json'
OUTPUT_FILENAME = 'allOutputData.json'
GRIDLABD_DIR = 'gridlabd/'
# primary functions -----------------------------------------------------------

def submitApplication(interconnectionForm):
 
    # create folder for request
<<<<<<< HEAD
    requestDir = REQUEST_DIR_PREFIX+str(interconnectionForm['Position'])+'/'
    os.mkdir( requestDir )
    os.mkdir( requestDir+GRIDLABD_DIR )
=======
    requestDir = DATA_DIR+'after_request_'+str(interconnectionForm['Position'])+'/'
    try: 
        os.mkdir( requestDir )
    except: 
        pass
>>>>>>> 52c1e5a1bc04e37d7f1ce307c6cab4483e26d2ce
    
    # save request info in the corresponding directory 
    interconnectionForm['Status'] = 'Application Submitted'
    with open(requestDir+INFO_FILENAME, 'w') as file:
        json.dump(interconnectionForm, file)

    return 'Application Submitted'

def processQueue():

    # TODO: add withdrawal logic
    # TODO: remove interactions with queue.json once 
    #       front end is no longer dependent on it

    # get a list of all requests
    folderList = glob.glob(REQUEST_DIR_PREFIX+'*')

    # loop through queue and process each request
    aPreviousEntryFailed = False 
    for requestPosition in range(1,len(folderList)+1):

        # get current request
        requestDir = REQUEST_DIR_PREFIX+ str(requestPosition)+'/'
        requestInfoFileName = requestDir+INFO_FILENAME
        with open(requestInfoFileName) as infoFile:
            request = json.load(infoFile)
        
        # if we see a failed request, update previously failed boolean
        if request.get('Status') == 'Engineering Review':
            aPreviousEntryFailed = True

        # if current request has been submitted but not processed
        elif request.get('Status') == 'Application Submitted':
                      
            # dont update the requests that occur after 
            # a previously failed request 
            if not aPreviousEntryFailed:
                
                # # add omd and input data to folder 
                # copy2(DATA_DIR+TEMPLATE_DIR+OMD_FILENAME, \
                #     requestDir+GRIDLABD_DIR+OMD_FILENAME)
                # copy2(DATA_DIR+TEMPLATE_DIR+INPUT_FILENAME, \
                #     requestDir+GRIDLABD_DIR+INPUT_FILENAME)
               
                meterName = 'node62474211556T62474211583'
                initializePowerflowModel(requestPosition,meterName)
                
                #run screens
                screenResults = runAllScreens(request['Position'])
                request['Screens Passed'] = screenResults

                # if all screens pass, update current request status to passed
                if screenResults['passedAll'] == True:
                    request['Status'] = 'Interconnection Agreement Proffered'
                else: # if any of the screens failed
                    request['Status'] = 'Engineering Review'
                    aPreviousEntryFailed = True

        # update request info
        with open(requestInfoFileName, 'w') as infoFile:
            json.dump(request, infoFile)
    
        # temp: update queue remove once frontend no longer needs queue.json
        with open('data/queue.json') as queueFile:
            queue = json.load(queueFile)
        queue[str(requestPosition)] = request
        with open('data/queue.json','w') as queueFile:
            json.dump(queue, queueFile)

def withdraw(requestPosition):

    # set status to withdrawn 
    # process queue
    pass

# helper functions ------------------------------------------------------------

def runAllScreens(requestPosition):

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

    # run the omf derInterconnection model
    workingDir = REQUEST_DIR_PREFIX + requestPosition + '/' + GRIDLABD_DIR
    derInterconnection.runForeground(workingDir)
    with open(workingDir+OUTPUT_FILENAME) as modelOutputFile:
        modelOutputs = json.load(modelOutputFile)
    
    # check screens for failures
    passedAll = True
    for screen in screenResults.keys():
        screenPassed = runScreen(modelOutputs[screen])
        screenResults[screen] = screenPassed
        if screenPassed == False:
            passedAll = False
    screenResults['passedAll'] = passedAll

    # if we had failed any screens we would have already returned
    # therefore if we are here, we passed all screens
    return screenResults
    
def runScreen(screeningData):

    screenPassed = True
    for entry in screeningData:
        violation = entry[-1]
        if violation == True:
            screenPassed = False
            return screenPassed

    return screenPassed

def initializePowerflowModel(requestPosition, meterName):

    def getPreviouslyPassingRequestDir(requestPosition):

        # go through previous requests
        previousRequestPosition = requestPosition-1
        while previousRequestPosition > 0:

            # get previous request status
            previousRequestDir = REQUEST_DIR_PREFIX + \
                str(previousRequestPosition) + '/'
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

    # main intialization logic ------------------------------------------------

    # get directory for current request
    requestDir = REQUEST_DIR_PREFIX + str(requestPosition) + '/'
        
    # if first request 
    if requestPosition == 1:
    
        # copy original templates
        previousRequestPosition = 0
        copy2(DATA_DIR+TEMPLATE_DIR+OMD_FILENAME, \
            requestDir+GRIDLABD_DIR+OMD_FILENAME)
        copy2(DATA_DIR+TEMPLATE_DIR+INPUT_FILENAME, \
            requestDir+GRIDLABD_DIR+INPUT_FILENAME)
    
    else: # otherwise get model from previously passing request and update it
        
        # copy templates
        previousRequestPosition, previousRequestDir = \
            getPreviouslyPassingRequestDir(requestPosition)
        copy2(previousRequestDir+GRIDLABD_DIR+OMD_FILENAME, \
            requestDir+GRIDLABD_DIR+OMD_FILENAME)
        copy2(previousRequestDir+GRIDLABD_DIR+INPUT_FILENAME, \
            requestDir+GRIDLABD_DIR+INPUT_FILENAME)

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
    meter = newTree[meterName]['item']
    
    # create inverter and set parent to meter, get phases from meter
    inverter = { 'object':'inverter',
        'name': 'inverterForRequest'+str(requestPosition),
        'parent': meterName,
        'rated_power':25000,
        'phases':'' }
    inverter['phases'] = meter['phases']
    feeder.insert(tree, inverter)
    
    # get attributes for the solar object
    requestInfoFileName = requestDir+INFO_FILENAME
    with open(requestInfoFileName) as infoFile:
        request = json.load(infoFile)
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
            if transformerTo == meterName:
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

# run tests when file is run --------------------------------------------------

def _tests():
    processQueue()
    # meterName = 'node62474211556T62474211583'
    # initializePowerflowModel(2,meterName)

if __name__ == '__main__':
    _tests()
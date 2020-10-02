import inspect
import config
import random, json, os, glob
from shutil import copy2, rmtree
from omf.models import derInterconnection
from omf import feeder
from appQueue import allAppDirs
from geocodio import GeocodioClient
from math import sqrt

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

# globals ---------------------------------------------------------------------

addedDer = config.gridlabdInputs['newGeneration']
addedDerStepUp = config.gridlabdInputs['newGenerationStepUp']
addedDerBreaker = config.gridlabdInputs['newGenerationBreaker']

# primary functions -----------------------------------------------------------

def processQueue(lock):

    # processQueue is called asynchronously, the lock ensures only one instance
    # is running at a time so files arent being overwritten and breaking things
    acquired = lock.acquire(False)
    if not acquired:
        return

    # get a list of all requests
    requestFolders = allAppDirs()

    # loop through queue and process each request
    allPreviousPassed = True
    for requestPosition in range(len(requestFolders)):
        # get current request
        requestDir = requestFolders[requestPosition] + '/'
        requestInfoFileName = requestDir+config.INFO_FILENAME
        with open(requestInfoFileName) as infoFile:
            request = json.load(infoFile)

        # if we see a previously failing request,
        # or an unprocessed request that isnt after a failure
        # run the screens and update statuses
        if (request.get('previousRequestWithdrawn',False) == True) or \
            (request.get('Status') == 'Engineering Review') or \
            ( (request.get('Status') == 'Application Submitted') and \
                allPreviousPassed ):

            # run screens
            request = \
            runAllScreensAndUpdateStatus(requestPosition, requestFolders)
            if not request['Screen Results']['passedAll']:
                allPreviousPassed = False

            # update withrawn status
            request['previousRequestWithdrawn'] = False

            # save request info to file
            with open(requestInfoFileName, 'w') as infoFile:
                json.dump(request, infoFile)

    # get a list of all requests again to see if 
    # any new requests have been submitted
    rerun = False
    newRequestFolders = allAppDirs()
    for requestDir in newRequestFolders:
        if requestDir not in requestFolders:
            rerun = True
            break

    # release lock so the next iteration of processQueue can run
    lock.release()

    # if there are new reuests process queue again
    if rerun:
        processQueue(lock)

#TODO link to front-end
def withdraw(withdrawLock, processQueueLock, requestPosition):

    withdrawLock.acquire()

    # get a list of all requests
    requestFolders = allAppDirs()
    for currentRequestPosition in range(len(requestFolders)):

        if currentRequestPosition >= requestPosition:

            # get current request
            requestDir = requestFolders[currentRequestPosition] + '/'
            requestInfoFileName = requestDir+config.INFO_FILENAME
            with open(requestInfoFileName) as infoFile:
                request = json.load(infoFile)

            # update withrawn status
            if currentRequestPosition == requestPosition:
                request['Status'] = 'Withdrawn'
            else:
                request['previousRequestWithdrawn'] = True

            # save request info to file
            with open(requestInfoFileName, 'w') as infoFile:
                json.dump(request, infoFile)


    # process queue
    processQueue(processQueueLock)

    withdrawLock.release()

# helper functions ------------------------------------------------------------

def runAllScreensAndUpdateStatus(requestPosition, requestFolders):

    # copy over model from the previous passing request and
    # add desired generation at given meter
    requestDir = requestFolders[requestPosition] + '/'
    gridlabdWorkingDir = \
    initializePowerflowModel(requestPosition, requestFolders)

    # run the omf derInterconnection model
    derInterconnection.runForeground(gridlabdWorkingDir)
    with open(gridlabdWorkingDir+config.OUTPUT_FILENAME) as modelOutputFile:
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
    requestInfoFileName = requestDir+config.INFO_FILENAME
    with open(requestInfoFileName) as infoFile:
        request = json.load(infoFile)
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

def initializePowerflowModel(requestPosition, requestFolders):

    # initialize vars
    requestDir = requestFolders[requestPosition] + '/'
    gridlabdWorkingDir = os.path.join(requestDir,config.GRIDLABD_DIR)
    requestInfoFileName = os.path.join(requestDir,config.INFO_FILENAME)
    with open(requestInfoFileName) as infoFile:
        request = json.load(infoFile)

    # create empty directory for gridlabd analysis
    try:
        rmtree(gridlabdWorkingDir)
    except FileNotFoundError as e:
        pass
    os.mkdir(gridlabdWorkingDir)

    # if first request
    if requestPosition == 0:

        # copy original templates
        previousRequestPosition = -1
        inputFileName = os.path.join(gridlabdWorkingDir,config.INPUT_FILENAME)
        with open(inputFileName,'w') as inputFile:
            json.dump(config.gridlabdInputs, inputFile)
        copy2(os.path.join(config.TEMPLATE_DIR,config.OMD_FILENAME), \
            os.path.join(gridlabdWorkingDir,config.OMD_FILENAME))

    else: # otherwise get model from previously passing request and update it

        # copy templates
        previousRequestPosition, previousRequestDir = \
            getPreviouslyPassingRequestDir(requestPosition,requestFolders)
        copy2(os.path.join(previousRequestDir, \
            config.GRIDLABD_DIR,config.OMD_FILENAME), \
            os.path.join(gridlabdWorkingDir,config.OMD_FILENAME))
        copy2(os.path.join(previousRequestDir,config.GRIDLABD_DIR, \
            config.INPUT_FILENAME), \
            os.path.join(gridlabdWorkingDir,config.INPUT_FILENAME))

    # load omd and rekey to make name lookups easier
    omdFileName = os.path.join(requestDir, \
        config.GRIDLABD_DIR,config.OMD_FILENAME)
    with open(omdFileName) as omdFile:
        omd = json.load(omdFile)
    tree = omd.get('tree', {})
    nameKeyedTree = rekeyGridlabDModelByName( tree )
    
    # rename old der
    if nameKeyedTree.get(addedDer,None) is not None:
        newName = addedDer+'ForRequest' + str(previousRequestPosition)
        tree, nameKeyedTree = renameTreeItem( tree, nameKeyedTree, \
            addedDer, newName)
    if nameKeyedTree.get(addedDerStepUp,None) is not None:
        newName = addedDerStepUp+'ForRequest' + str(previousRequestPosition)
        tree, nameKeyedTree = renameTreeItem( tree, nameKeyedTree, \
            addedDerStepUp, newName)
    if nameKeyedTree.get(addedDerBreaker,None) is not None:
        newName = addedDerBreaker+'ForRequest' + str(previousRequestPosition)
        tree, nameKeyedTree = renameTreeItem( tree, nameKeyedTree, \
            addedDerBreaker, newName)

    # get meter
    meterName = request['Meter ID']
    meter = nameKeyedTree[meterName]['item']

    # create inverter and set parent to meter, get phases from meter
    inverter = { 'object':'inverter',
        'name': 'inverterForRequest'+str(requestPosition),
        'parent': meterName,
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
        'name': addedDer,
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
    
    # else if transformer is the same as a previous run 
    # rename it for current run
    namePrefix = addedDerStepUp+'ForRequest'
    transformerName = transformer.get('name','')
    if transformerName.startswith(namePrefix):
        oldRequestNum = transformerName[len(namePrefix):]
        tree, nameKeyedTree = renameTreeItem( tree, nameKeyedTree, \
            transformerName, addedDerStepUp)
        breakerName = addedDerBreaker+'ForRequest' + oldRequestNum
        tree, nameKeyedTree = renameTreeItem( tree, nameKeyedTree, \
            breakerName, addedDerBreaker)        

    # else if transformer is not the same as a previous run add a breaker
    else:

        # create new node to go between breaker and transformer
        poi = { 'object': 'node',
            'name': 'poiForRequest'+ str(requestPosition),
            'nominal_voltage':0,
            'phases':'' }
        transformerFromItem = nameKeyedTree[transformerFrom]['item']
        poi['nominal_voltage'] = transformerFromItem['nominal_voltage']
        poi['phases'] = transformerFromItem['phases']
        feeder.insert(tree, poi)

        # update transformer name and set transformer 'from' to new node
        transformer['name'] = addedDerStepUp
        transformer['from'] = poi['name']
        tree[transformerKey] = transformer

        # create fuse
        fuse = { 'object': 'fuse',
            'name': addedDerBreaker,
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
    with open(omdFileName,'w') as omdFile:
        omd = dict(feeder.newFeederWireframe)
        omd['tree'] = tree
        json.dump(omd, omdFile, indent=4)

    return gridlabdWorkingDir

def getPreviouslyPassingRequestDir(requestPosition, requestFolders):

    # go through previous requests
    previousRequestPosition = requestPosition-1
    while previousRequestPosition >= 0:

        # get previous request status
        previousRequestDir = requestFolders[previousRequestPosition] + '/'
        infoFileName = previousRequestDir+config.INFO_FILENAME
        with open(infoFileName) as infoFile:
            previousRequest = json.load(infoFile)
            previousStatus = previousRequest['Status']

        # break out of loop at the first approved request
        if previousStatus == 'Interconnection Agreement Proffered':
            break
        else: # keep looping till there are no more requests
            previousRequestPosition -= 1

    # if we didnt find a previously passing request, something went wrong
    if previousRequestPosition == -1:
        raise Exception('this error should not be possible. \
            We are processing a request that has not had any \
            any passing requests before it and also isnt the \
            1st request. processQueue() should prevent this \
            from happening ')

    return previousRequestPosition, previousRequestDir

def rekeyGridlabDModelByName( tree ):

    # makes it easier to search for items
    nameKeyedTree = {}
    for key in tree.keys():
        name = tree[key].get('name',None)
        if name is not None:
            nameKeyedTree[name] = {'item': tree[key], 'originalKey': key}

    return nameKeyedTree

def renameTreeItem( tree, nameKeyedTree, name, newName):

    nameKeyedTree[name]['item']['name'] = newName
    nameKeyedTree[newName] = nameKeyedTree[name]
    del nameKeyedTree[name]
    tree[nameKeyedTree[newName]['originalKey']] = \
    nameKeyedTree[newName]['item']

    return (tree, nameKeyedTree)

def getMeterNameList( omdPath ):

    # load omd
    with open(omdPath) as omdFile:
        omd = json.load(omdFile)
    tree = omd.get('tree', {})

    # loop through omd and keep track of the meters
    meterNameList = []
    for key in tree.keys():
        objectType = tree[key].get('object',None)
        if (objectType == 'meter') or (objectType == 'triplex_meter'):
            name = tree[key].get('name',None)
            if name is not None:
                meterNameList.append(name)

    return meterNameList

def getMeterFromLatLong(latitude, longitude, tree):

    # loop through meter and pick the closest one
    smallestDist = None
    bestMeterName = None
    for key in tree.keys():
        objType = tree[key].get('object',None)
        if ( (objType == 'meter') or (objType == 'triplex_meter') ):
            
            # get this meters latitude and longitude
            objName = tree[key].get('name',None)
            meterLatitude = tree[key].get('latitude',None)
            meterLongitude = tree[key].get('longitude',None)
            
            # calc dist to query address
            if meterLatitude is not None and meterLatitude is not None:
                dist = sqrt( \
                    (latitude-meterLatitude)**2 + \
                    (longitude-meterLongitude)**2 )
                
                # keep track of the min val
                if (smallestDist == None) or (dist < smallestDist):
                    smallestDist = dist
                    bestMeterName = objName

    if bestMeterName is None:
        raise Exception('No match found, please ensure model has meters \
            and that the meters have a defined latitude and longitude')

    return bestMeterName

def getLatLongFromAddress(address):

    client = GeocodioClient( config.GEOCODE_KEY )
    returned = client.geocode(address)
    location = returned['results'][0]['location']
    latitude = location['lat']
    longitude = location['lng']

    return latitude,longitude


# run tests when file is run --------------------------------------------------

def _tests():

    # processQueue()

    # initializePowerflowModel(2,config.METER_NAME)

    # must be run after all pending processQueue requests are processed
    # because these locks are just place holders
    # from multiprocessing import Lock
    # withdrawLock = Lock()
    # queueLock = Lock()
    # withdraw(withdrawLock, queueLock, 1)

    # getMeterNameList(config.TEMPLATE_DIR+config.OMD_FILENAME)

    # numCorrect = 0
    # numAttempts = 100
    # omdFileName = os.path.join(config.TEMPLATE_DIR,config.OMD_FILENAME)
    # for attemptNum in range(numAttempts):
    #     queryMeterName = random.choice(getMeterNameList(omdFileName))
    #     with open(omdFileName) as omdFile:
    #         omd = json.load(omdFile)
    #     tree = omd.get('tree', {})
    #     for key in tree.keys():
    #         objName = tree[key].get('name',None)
    #         if (objName == queryMeterName):
    #             latitude = tree[key]['latitude']
    #             longitude = tree[key]['longitude']
    #             meterName = getMeterFromLatLong(latitude,longitude,tree)
    #             break
    #     if (queryMeterName == meterName):
    #         numCorrect += 1
    # print(100*numCorrect/numAttempts, \
    #     '% of meters identified correctly out of', numAttempts, 'attempts')

    # address = "1109 N Highland St, Arlington VA"
    # lati, longi = getLatLongFromAddress(address)
    # print(lati, longi)

    pass;


if __name__ == '__main__':
    _tests()

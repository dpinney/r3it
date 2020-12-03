import inspect
import config
import random, json, os, glob
from shutil import copy2, rmtree
from omf.models import derInterconnection
from omf import feeder
from appQueue import allAppDirs, appDir, allAppIDs, appDict
from geocodio import GeocodioClient
from math import sqrt

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
        requestDir = requestFolders[requestPosition]
        requestInfoFileName = os.path.join(requestDir,config.INFO_FILENAME)
        with open(requestInfoFileName) as infoFile:
            request = json.load(infoFile)

        if config.enableAutomaticScreening == True:
            # if we see a previously failing request,
            # or an unprocessed request that isnt after a failure
            # run the screens and update statuses
            if ( (request.get('markedForRerunDueToWithdrawal') == True) and \
                (request.get('Status') != 'Withdrawn') ) or \
                (request.get('Status') == 'Engineering Review') or \
                ( (request.get('Status') == 'Application Submitted') and \
                    allPreviousPassed ):

                # run screens
                request = \
                runAllScreensAndUpdateStatus(requestPosition, requestFolders)
                if not request['Screen Results']['passedAll']:
                    allPreviousPassed = False
                request['markedForRerunDueToWithdrawal'] = False

                if config.requireAllAppsToGoThroughEngineer == True:
                    request['Status'] = 'Engineering Review'

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

def withdraw(withdrawLock, processQueueLock, requestID):

    withdrawLock.acquire()

    # get the withdrawn request directory 
    withdrawnRequestPos = None
    withdrawnRequestDir = appDir(requestID)

    # get a list of all requests
    requestFolders = allAppDirs()
    for currentRequestPosition in range(len(requestFolders)):

        # check to see if current request is the withdrawn request
        requestDir = requestFolders[currentRequestPosition]
        if withdrawnRequestDir == requestDir:
            withdrawnRequestPos = currentRequestPosition

        # mark every request after the withdrawn request to be rerun
        if (withdrawnRequestPos is not None) and \
            (currentRequestPosition >= withdrawnRequestPos):

            # get current request info
            requestInfoFileName = os.path.join(requestDir,config.INFO_FILENAME)
            with open(requestInfoFileName) as infoFile:
                request = json.load(infoFile)

            # update withrawn status
            if currentRequestPosition == withdrawnRequestPos:
                request['Status'] = 'Withdrawn'
            else:
                request['markedForRerunDueToWithdrawal'] = True

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
    outputFilename = os.path.join(gridlabdWorkingDir,config.OUTPUT_FILENAME)
    with open(outputFilename) as modelOutputFile:
        modelOutputs = json.load(modelOutputFile)

    # keep track of screen results to present on the front-end
    screenResults = {
        # are voltages within +- 5% inclusive of nominal if nominal <600
        # and within -2.5% to +5% inclusive otherwise
       'Voltage Violations Screen': 'Running...',
        # 100*(1-(derOffVoltage/derOnVoltage)) >= user provided threshold
       'Flicker Violations Screen': 'Running...',
        # is the max current on line/ line rating >= user provided threshold
       'Thermal Violations Screen': 'Running...',
        # is the power measurement on a regulator < 0
       'Reverse Power Flow Screen': 'Running...',
        # is abs(tapPositionDerOn-tapPositionDerOff) >= user provided threshold
       'Tap Change Violations Screen': 'Running...',
        # is 100*(abs(preFaultCurrent-postFaultCurrent)/preFaultCurrent) >=
        # user provided threshold
       'Fault Current Violations Screen': 'Running...',
        # is 100*(postFaultValAtLinetoAddedBreaker/preFaultval) >=
        # user provided threshold
       'POI Fault Voltage Screen': 'Running...'
    }

    # link screen names to entries in omf model output
    screenNamesToGridlabVars = {
        'Voltage Violations Screen': 'voltageViolations',
        'Flicker Violations Screen': 'flickerViolations',
        'Thermal Violations Screen': 'thermalViolations',
        'Reverse Power Flow Screen': 'reversePowerFlow',
        'Tap Change Violations Screen': 'tapViolations',
        'Fault Current Violations Screen': 'faultCurrentViolations',
        'POI Fault Voltage Screen': 'faultPOIVolts'
    }
    # check screens for failures
    passedAll = True
    for screen in screenResults.keys():
        gridlabVarForScreen = screenNamesToGridlabVars[screen]
        screenPassed = runSingleScreen(modelOutputs[gridlabVarForScreen])
        if screenPassed == True:
            screenResults[screen] = 'Passed'
        else:
            screenResults[screen] = 'Failed'
            passedAll = False
    screenResults['passedAll'] = passedAll

    # update current request results and status
    requestInfoFileName = os.path.join(requestDir,config.INFO_FILENAME)
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

    # get model from previously passing request and 
    # copy it into current request
    previousRequestPosition, previousRequestDir = \
        getPreviouslyPassingRequestDir(requestPosition,requestFolders)
    copy2(os.path.join(previousRequestDir, \
        config.GRIDLABD_DIR,config.omdFilename), \
        os.path.join(gridlabdWorkingDir,config.omdFilename))

    # create gridlabd inputs file
    gridlabdInputFile = \
        os.path.join(gridlabdWorkingDir,config.INPUT_FILENAME)
    with open(gridlabdInputFile, 'w') as inputFile:
        json.dump(config.gridlabdInputs, inputFile)

    # load omd and rekey to make name lookups easier
    omdFileName = os.path.join(requestDir, \
        config.GRIDLABD_DIR,config.omdFilename)
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
        previousRequestDir = requestFolders[previousRequestPosition]
        infoFileName = os.path.join(previousRequestDir,config.INFO_FILENAME)
        with open(infoFileName) as infoFile:
            previousRequest = json.load(infoFile)
            previousStatus = previousRequest['Status']

        # break out of loop at the first approved request
        if previousStatus == 'Interconnection Agreement Proffered':
            break
        else: # keep looping till there are no more requests
            previousRequestPosition -= 1

    # if we didnt find a previously passing request, 
    # use the original templates
    if previousRequestPosition == -1:
        print('no previously passing requests; using original omd.')
        previousRequestDir = config.STATIC_DIR
        
    return previousRequestPosition, previousRequestDir

def rekeyGridlabDModelByName(tree):

    # makes it easier to search for items
    nameKeyedTree = {}
    for key in tree.keys():
        name = tree[key].get('name',None)
        if name is not None:
            nameKeyedTree[name] = {'item': tree[key], 'originalKey': key}

    return nameKeyedTree

def renameTreeItem(tree, nameKeyedTree, name, newName):

    nameKeyedTree[name]['item']['name'] = newName
    nameKeyedTree[newName] = nameKeyedTree[name]
    del nameKeyedTree[name]
    tree[nameKeyedTree[newName]['originalKey']] = \
    nameKeyedTree[newName]['item']

    return (tree, nameKeyedTree)

def getMeterNameList(omdPath):

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
    bestMeterLongitude = None
    bestMeterLatitude = None
    for key in tree.keys():
        objType = tree[key].get('object',None)
        if ( (objType == 'meter') or (objType == 'triplex_meter') ):
            
            # get this meters latitude and longitude
            objName = tree[key].get('name',None)
            meterLatitude = tree[key].get('latitude',None)
            meterLongitude = tree[key].get('longitude',None)
            
            # calc dist to query address
            if meterLatitude is not None and meterLongitude is not None:
                dist = sqrt( \
                    (latitude-meterLatitude)**2 + \
                    (longitude-meterLongitude)**2 )
                
                # keep track of the min val
                if (smallestDist == None) or (dist < smallestDist):
                    smallestDist = dist
                    bestMeterName = objName
                    bestMeterLatitude = meterLatitude
                    bestMeterLongitude = meterLongitude

    if bestMeterName is None:
        raise Exception('No match found, please ensure model has meters \
            and that the meters have a defined latitude and longitude')

    return bestMeterName, bestMeterLatitude, bestMeterLongitude

def getLatLongFromAddress(address):

    client = GeocodioClient( config.GEOCODE_KEY )
    returned = client.geocode(address)
    print()
    print(returned)
    location = returned['results'][0]['location']
    latitude = location['lat']
    longitude = location['lng']

    return latitude,longitude

def calcCapacityUsed():

    approvedGeneration = 0

    apps = allAppIDs()
    for app in apps:
        application = appDict(app)
        if application.get('Status') == 'Interconnection Agreement Proffered':
            approvedGeneration += float( application.get( \
                'Nameplate Rating (kW)',0) )

    return approvedGeneration

# run tests when file is run --------------------------------------------------

def _tests():

    # 1 -----------------------------------------------------------------------
    
    # processQueue()

    # 2 -----------------------------------------------------------------------
    
    # initializePowerflowModel(2,config.METER_NAME)

    # 3 -----------------------------------------------------------------------
    
    # must be run after all pending processQueue requests are processed
    # because these locks are just place holders
    # from multiprocessing import Lock
    # withdrawLock = Lock()
    # queueLock = Lock()
    # withdraw(withdrawLock, queueLock, 1)

    # 4 -----------------------------------------------------------------------
    
    # getMeterNameList(os.path.join(config.STATIC_DIR,config.GRIDLABD_DIR,config.omdFilename))

    # 5 -----------------------------------------------------------------------
    
    # address = "1109 N Highland St, Arlington VA"
    # lati, longi = getLatLongFromAddress(address)
    # print(lati, longi)
    
    # 6 -----------------------------------------------------------------------
    
    # # init geocoding client
    # client = GeocodioClient( config.GEOCODE_KEY )
    
    # # get model tree
    # omdFileName = os.path.join(config.STATIC_DIR,config.GRIDLABD_DIR,config.omdFilename)
    # with open(omdFileName) as omdFile:
    #     omd = json.load(omdFile)
    # tree = omd.get('tree', {})
    
    # # get lat long mappings
    # geoFilename = os.path.join('..','test', \
    #     'Olin Barre Real Coordinates Lat Lons.geojson')
    # with open(geoFilename) as geoFile:
    #     coordinates = json.load(geoFile)
    #     coordinates = coordinates['features']

    # # replace all of the gridlab coordinates with the correct ones
    # for key in tree.keys():
    #     objName = tree[key].get('name',None)    
    #     if objName is not None:
    #         for item in coordinates: 
    #             itemName = item['properties']['name']
    #             if ( (objName+'_A') == itemName ) or \
    #             ( (objName+'_B') == itemName ) or \
    #             ( (objName+'_C') == itemName ) :
    #                 longitude = item['geometry']['coordinates'][0]
    #                 latitude = item['geometry']['coordinates'][1]
    #                 tree[key]['latitude'] = latitude
    #                 tree[key]['longitude'] = longitude
        
    # # run through num attempts tests
    # minAcc = None
    # numCorrect = 0
    # numAttempts = 1
    # for attemptNum in range(numAttempts):
        
    #     # select a random meter to test
    #     queryMeterName = random.choice(getMeterNameList(omdFileName))
    #     for key in tree.keys():
    #         objName = tree[key].get('name',None)
    #         if (objName == queryMeterName):
                
    #             # get lat and long
    #             latitude = tree[key].get('latitude',None)
    #             longitude = tree[key].get('longitude',None) 
    #             print('\n'+queryMeterName,latitude,longitude)
                
    #             # get address from lat long
    #             returned = client.reverse((latitude, longitude))
    #             address = returned['results'][0]['formatted_address']
    #             accuracy = returned['results'][0]['accuracy']
    #             if minAcc is None or accuracy<minAcc:
    #                 minAcc = accuracy
                                
    #             # test function to get lat long from address and
    #             # to get meter from lat long
    #             lati, longi = getLatLongFromAddress(address)
    #             print(accuracy,address,lati,longi)
    #             meterName, meterLatitude, meterLongitude = \
    #                 getMeterFromLatLong(lati,longi,tree)
    #             break

    #     print(meterName, meterLatitude, meterLongitude)
    #     if (queryMeterName == meterName):
    #         print('match found correctly')
    #         numCorrect += 1
    
    # print(100*numCorrect/numAttempts, \
    #     '% of meters identified correctly out of', numAttempts, 'attempts', \
    #     'with min accuracy of:', minAcc )


    # -------------------------------------------------------------------------
    pass;
    # -------------------------------------------------------------------------

if __name__ == '__main__':
    _tests()
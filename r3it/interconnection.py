import inspect
import config
import random, json, os, glob
from shutil import copy2
from omf.models import derInterconnection

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
	derInterconnection.new('/data/queue/after_request_{id}, {'omd_path':'/static/base_circuit.omd'})
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

DATA_DIR = './data/'
INFO_FILENAME = 'info.json'
TEMPLATE_DIR = 'templates/'
INPUT_FILE = 'allInputData.json'
OMD_FILE = 'Olin Barre Geo Modified DER.omd'

def submitApplication(interconnectionForm):
 
    # TODO: 
    # populate directory with appropriate model and allInputData.json
    # using placeholder templates for now

    # create folder for request
    requestDir = DATA_DIR+'after_request_'+str(interconnectionForm['Position'])+'/'
    os.mkdir( requestDir )
    
    # save request info in the corresponding directory 
    interconnectionForm['Status'] = 'Application Submitted'
    with open(requestDir+INFO_FILENAME, 'w') as file:
        json.dump(interconnectionForm, file)

    # PLACEHOLDER: copy templates
    copy2(DATA_DIR+TEMPLATE_DIR+OMD_FILE, requestDir+OMD_FILE)
    copy2(DATA_DIR+TEMPLATE_DIR+INPUT_FILE, requestDir+INPUT_FILE)

    return 'Application Submitted'


def processQueue():

    # TODO: add withdrawal logic
    # TODO: add screen results to info.json outputs
    # TODO: remove interactions with queue.json

    # get a list of all requests
    folderList = glob.glob(DATA_DIR+'after_request_*')

    # loop through queue and process each request
    aPreviousEntryFailed = False 
    for requestPosition in range(1,len(folderList)+1):

        # get current request
        requestInfoFileName = DATA_DIR+'after_request_'+\
            str(requestPosition)+'/'+INFO_FILENAME
        with open(requestInfoFileName) as infoFile:
            request = json.load(infoFile)
        
        # if we see a failed request, update previously failed boolean
        if request.get('Status') == 'Engineering Review':
            aPreviousEntryFailed = True

        # if current request has been submitted but not processed
        elif request.get('Status') == 'Application Submitted':
               
            #run screens
            screenResults = runAllScreens(request['Position'])
            request['Screens Passed'] = screenResults

            # if all screens pass, update current request status to passed
            if screenResults['passedAll'] == True:
                request['Status'] = 'Interconnection Agreement Proffered'                    
            else: # if any of the screens failed, update request to Engineering review
                request['Status'] = 'Engineering Review'
                aPreviousEntryFailed = True

            # cluster all requests that occur after 
            # a previously failed request as Engineering review, 
            # the expectation is the engineer will discuss the cost of
            # any grid updates with everyone that benefits from it and 
            # manually update statuses for anyone else
            if aPreviousEntryFailed:
                request['Status'] = 'Engineering Review'

        # update request info
        with open(requestInfoFileName, 'w') as infoFile:
            json.dump(request, infoFile)
    
        # temp: update queue remove once frontend no longer needs queue.json
        with open('data/queue.json') as queueFile:
            queue = json.load(queueFile)
        queue[str(requestPosition)] = request
        with open('data/queue.json','w') as queueFile:
            json.dump(queue, queueFile)

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
    workingDir = './data/after_request_' + requestPosition
    derInterconnection.runForeground(workingDir)
    with open(workingDir+'/allOutputData.json') as modelOutputFile:
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

def _tests():
    processQueue()

if __name__ == '__main__':
    _tests()
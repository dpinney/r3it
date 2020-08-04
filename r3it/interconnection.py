import random
import inspect
import config
from omf.models import derInterconnection

FEEDER_PATH1 = '/static/feeder1.omd'

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

def compute_status(interconnection_form):
    # TODO: do all the computations on an interconnection request.
    # For now, randomize 'Approved' vs. 'Pending'
    if int(interconnection_form['Nameplate Rating (kW)']) <= config.sizeThreshold:
    	return 'Interconnection Agreement Proffered'
    else:
    	return 'Engineering Review'

def _tests():
    print(derInterconnection.runForeground('./data/test'))


if __name__ == '__main__':
    _tests()
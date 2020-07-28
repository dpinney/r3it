import random
import inspect
import config
from omf.models import derInterconnection

FEEDER_PATH1 = '/static/feeder1.omd'

'''
/data/queue/
	after_request_1
	after_request_2
	...
	after_request_n

def build_model(id):
	current_omd = f'/data/queue/after_request_{id - 1}'
	derInterconnection.new('/data/queue/after_request_{id}, {'omd_path':'/static/base_circuit.omd'})

def withdrawal(id):
	pass #todo later: go through and rebuild the queue starting at id - 1.
'''

def compute_status(interconnection_form):
    # TODO: do all the computations on an interconnection request.
    # For now, randomize 'Approved' vs. 'Pending'
    if int(interconnection_form['Nameplate Rating (kW)']) <= config.sizeThreshold:
    	return 'Interconnection Agreement Proffered'
    else:
    	return 'Engineering Review Needed'

def _tests():
    print(derInterconnection.runForeground('./data/test'))


if __name__ == '__main__':
    _tests()
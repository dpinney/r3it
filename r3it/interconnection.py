import random
import inspect

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
    return random.choice(['Approved', 'Pending'])

def _tests():
    print(derInterconnection.runForeground('./data/403f41aa58474ed6a3633ac22a4cd97b'))


if __name__ == '__main__':
    _tests()

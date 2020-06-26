import random
import inspect

from omf.models import derInterconnection


def compute_status(interconnection_form):
    # TODO: do all the computations on an interconnection request.
    # For now, randomize 'Approved' vs. 'Pending'
    return random.choice(['Approved', 'Pending'])


def _tests():
    print(derInterconnection.runForeground('./data/403f41aa58474ed6a3633ac22a4cd97b'))


if __name__ == '__main__':
    _tests()

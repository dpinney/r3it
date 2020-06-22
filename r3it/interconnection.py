import random

def compute_status(interconnection_form):
    # TODO: do all the computations on an interconnection request.
    # For now, randomize 'Approved' vs. 'Pending'
    return random.choice(['Approved', 'Pending'])
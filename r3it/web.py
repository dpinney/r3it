import copy
import csv
import json
import uuid
import time
from random import choice as pick

from flask import Flask, redirect, request, send_from_directory
from jinja2 import Template

import interconnection

app = Flask(__name__)

statuses = ['Approved', 'Pending', 'Customer Options Meeting Proposed', 'Customer Options Meeting Scheduled', 'Interconnection Agreement Profferred', 'Interconnection Agreement Executed', 'Permission to Operate Profferred', 'Permission to Operate Executed', 'In Operation', 'Out of Service']


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/queue')
def queue():
    queue_data = []
    with open('data/queue.json') as queue:
        data = json.load(queue)
        i = 1
        for id, value in data.items():
            datarow = [i, value['Time of Request'],
                       value['Address (Facility)'], value['Status'], id]
            queue_data.append(datarow)
            i = i+1
    template = Template(open('templates/queue.html', 'r').read())
    return template.render(data=queue_data)


@app.route('/login/engineer')
def login_engineer():
    template = Template(open('templates/loginEngineer.html', 'r').read())
    return template.render()


@app.route('/login/customer')
def login_customer():
    template = Template(open('templates/loginCustomer.html', 'r').read())
    return template.render()


@app.route('/overview')
def overview():
    template = Template(open('templates/overview.html', 'r').read())
    return template.render()


@app.route('/report/<id>')
def report(id):
    with open('data/queue.json') as queue:
        report_data = json.load(queue)[id]
    report_data['id'] = id
    template = Template(open('templates/report.html', 'r').read())
    return template.render(data=report_data)


@app.route('/add-to-queue', methods=['GET', 'POST'])
def add_to_queue():
    print(request.form)
    status = interconnection.compute_status(request.form)
    interconnection_request = {}
    for key, value in request.form.items():
        interconnection_request[key] = value
    interconnection_request['Time of Request'] = time.asctime(time.localtime(time.time()))
    interconnection_request['Status'] = status
    with open('data/queue.json') as queue:
        data = json.load(queue)
    data[uuid.uuid4().hex] = interconnection_request
    with open('data/queue.json', 'w') as queue:
        json.dump(data, queue)
    return redirect('/customerLanding')


@app.route('/send-file/<path:fullPath>')
def send_file(fullPath):
    path_pieces = fullPath.split('/')
    return send_from_directory('/'.join(path_pieces[0:-1]), path_pieces[-1])


@app.route('/application')
def application():
    firstNames = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Charles', 'Mary', 'Patricia', 'Linda', 'Barbara', 'Elizabeth', 'Jennifer', 'Maria', 'Susan', 'Margaret']
    lastNames = ['Smith', 'Jones', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    trees = ['Oak', 'Birch', 'Cypress', 'Maple', 'Pine', 'Hickory', 'Ash', 'Aspen', 'Elder Berry']
    suffixes = ['Ave.', 'Ln.', 'St.', 'Way', 'Blvd']
    zips = range(54601, 54650)


    phases = ['One', 'Three']
    sizes = range(1,20)
    voltages = ['110', '220', '600']

    firstname, lastname = pick(firstNames), pick(lastNames)

    default = {
    'label' : '{} {}\'s Solar Project'.format(firstname, lastname),
    'name' : '{} {}'.format(firstname, lastname),
    'address' : "{} {} {}".format(str(pick(range(9999))), pick(trees), pick(suffixes)),
    'zip' : '{}'.format(pick(zips)),
    'city': 'LaCrosse',
    'state' : 'WI',
    'phone' : '({}{}) {}{} - {}'.format(pick(range(2,9)), pick(range(10,99)), pick(range(2,9)), pick(range(10,99)), pick(range(1000,9999))),
    'size' : '{}'.format(pick(sizes)),
    'voltage' : '{}'.format(pick(voltages)),
    'email' : '{}.{}@gmail.com'.format(firstname, lastname)
    }
    
    template = Template(open('templates/application.html', 'r').read())
    return template.render(default = default)


@app.route('/update-status/<id>/<status>')
def update_status(id, status):
    if status not in statuses:
        return 'Status invalid; no update made.'
    with open('data/queue.json') as queue:
        data = json.load(queue)
    data[id]['Status'] = status
    with open('data/queue.json', 'w') as queue:
        json.dump(data, queue)
    print(data[id])
    return redirect(request.referrer)


if __name__ == '__main__':
    app.run(debug=True)

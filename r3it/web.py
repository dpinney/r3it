import copy
import csv
import json
import uuid

from flask import Flask, redirect, request, send_from_directory
from jinja2 import Template

import interconnection

app = Flask(__name__)

statuses = ['Approved', 'Pending', 'Customer Options Meeting Proposed', 'Customer Options Meeting Scheduled', 'Interconnection Agreement Profferred', 'Interconnection Agreement Executed', 'Permission to Operate Profferred', 'Permission to Operate Executed', 'In Operation', 'Out of Service'
            ]


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
            datarow = [i, value['datetime'],
                       value['location'], value['status'], id]
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
    interconnection_request['status'] = status
    with open('data/queue.json') as queue:
        data = json.load(queue)
    data[uuid.uuid4().hex] = interconnection_request
    with open('data/queue.json', 'w') as queue:
        json.dump(data, queue)
    return redirect('/queue')


@app.route('/send-file/<path:fullPath>')
def send_file(fullPath):
    path_pieces = fullPath.split('/')
    return send_from_directory('/'.join(path_pieces[0:-1]), path_pieces[-1])


@app.route('/application')
def application():
    template = Template(open('templates/application.html', 'r').read())
    return template.render()


@app.route('/update-status/<id>/<status>')
def update_status(id, status):
    if status not in statuses:
        return 'Status invalid; no update made.'
    with open('data/queue.json') as queue:
        data = json.load(queue)
    data[id]['status'] = status
    with open('data/queue.json', 'w') as queue:
        json.dump(data, queue)
    print(data[id])
    return redirect(request.referrer)


if __name__ == '__main__':
    app.run(debug=True)

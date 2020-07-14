import copy
import csv
import json
import time
import flask_login
import flask_wtf
import os, hashlib, random
from random import choice as pick

from flask import Flask, redirect, request, send_from_directory, render_template

import interconnection

app = Flask(__name__)
r3itDir = os.path.dirname(os.path.abspath(__file__))

users = {'me@coop.coop': {'password': 'secret', 'type': 'engineer'}, 'me@gmail.com': {'password': 'secret', 'type': 'customer'}}

def cryptoRandomString():
    ''' Generate a cryptographically secure random string for signing/encrypting cookies. '''
    if 'COOKIE_KEY' in globals():
        return COOKIE_KEY
    else:
        return hashlib.md5(str(random.random()).encode('utf-8') + str(time.time()).encode('utf-8')).hexdigest()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'
app.secret_key = cryptoRandomString()

class User(flask_login.UserMixin):
    def __init__(self, email, userType):
        self.id = email
        self.type = userType

class Anon(flask_login.AnonymousUserMixin):
    def __init__(self):
        self.id = 'anonymous'
        self.type = 'anonymous'

@login_manager.user_loader
def load_user(email):
    if email in users:
        return User(email, users.get(email, {}).get('type'))
    else:
        return Anon()

statuses = ['Approved', 'Pending', 'Customer Options Meeting Proposed', 'Customer Options Meeting Scheduled', 'Interconnection Agreement Profferred', 'Interconnection Agreement Executed', 'Permission to Operate Profferred', 'Permission to Operate Executed', 'In Operation', 'Out of Service']

@app.route('/')
def index(): 
    data = []
    if flask_login.current_user.is_anonymous():
        pass
    elif flask_login.current_user.type == 'engineer':
        for id, value in json.load(open('data/queue.json')).items():
            data.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
    elif flask_login.current_user.type == 'customer':
        for id, value in json.load(open('data/queue.json')).items():
            if value["Email (Customer)"] == flask_login.current_user.get_id():
                data.append([id, value['Time of Request'], value['Address (Facility)'], value['Status']])
    return render_template('index.html', data=data)

@app.route('/login')
def login():
    email, passwordAttempt = request.args['username'], request.args['password']
    password = users.get(email, {}).get('password')
    if email in users and password == passwordAttempt:
        print('loading ', email)
        flask_login.login_user(load_user(email))
        return redirect('/')
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')

@app.route('/thankyou')
@flask_login.login_required
def thankyou():
    return render_template('applicationSubmitted.html')

@app.route('/report/<id>')
@flask_login.login_required
def report(id):
    with open('data/queue.json') as queue:
        report_data = json.load(queue)[id]
    report_data['id'] = id
    with open('data/sample/allOutputData.json') as data:
        sample_data = json.load(data)
    return render_template('report.html', data=report_data, sample_data=sample_data)

@app.route('/add-to-queue', methods=['GET', 'POST'])
@flask_login.login_required
def add_to_queue():
    status = interconnection.compute_status(request.form)
    interconnection_request = {}
    for key, value in request.form.items():
        interconnection_request[key] = value
    interconnection_request['Time of Request'] = time.asctime(time.localtime(time.time()))
    interconnection_request['Status'] = status
    with open('data/queue.json') as queue:
        data = json.load(queue)
    data[len(data) + 1] = interconnection_request
    with open('data/queue.json', 'w') as queue:
        json.dump(data, queue)
    return redirect('/thankyou')


@app.route('/send-file/<path:fullPath>')
@flask_login.login_required
def send_file(fullPath):
    path_pieces = fullPath.split('/')
    return send_from_directory('/'.join(path_pieces[0:-1]), path_pieces[-1])


@app.route('/application')
@flask_login.login_required
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
    'email' : str(flask_login.current_user.id)
    }
    
    return render_template('application.html', default = default)


@app.route('/update-status/<id>/<status>')
@flask_login.login_required
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

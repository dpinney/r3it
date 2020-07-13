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

users = {'george@cooperativetactics.com': {'password': 'secret', 'type': 'customer'}}

def cryptoRandomString():
    ''' Generate a cryptographically secure random string for signing/encrypting cookies. '''
    if 'COOKIE_KEY' in globals():
        return COOKIE_KEY
    else:
        return hashlib.md5(str(random.random()).encode('utf-8') + str(time.time()).encode('utf-8')).hexdigest()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
app.secret_key = cryptoRandomString()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def load_user(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return
    user = User()
    user.id = email
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user


@app.route('/login/engineer', methods=['GET', 'POST'])
def login_engineer():
    return render_template('loginEngineer.html')

@app.route('/login/customer', methods=['GET', 'POST'])
def login_customer():
    return render_template('loginCustomer.html')


statuses = ['Approved', 'Pending', 'Customer Options Meeting Proposed', 'Customer Options Meeting Scheduled', 'Interconnection Agreement Profferred', 'Interconnection Agreement Executed', 'Permission to Operate Profferred', 'Permission to Operate Executed', 'In Operation', 'Out of Service']

@app.route('/')
def hello_world(): 
    return render_template('base.html')

@app.route('/queue')
def queue():
    queue_data = []
    with open('data/queue.json') as queue:
        data = json.load(queue)
        for id, value in data.items():
            datarow = [id, value['Time of Request'],
                       value['Address (Facility)'], value['Status']]
            queue_data.append(datarow)
    return render_template('queue.html', data=queue_data)

@app.route('/overview')
def overview():
    return render_template('overview.html')

@app.route('/customerLanding')
def customerLanding():
    queue_data = []
    with open('data/queue.json') as queue:
        data = json.load(queue)
        for id, value in data.items():
            if value["Email (Customer)"] == flask_login.current_user.id:
                datarow = [id, value['Time of Request'],
                       value['Address (Facility)'], value['Status']]
                queue_data.append(datarow)
                
    return render_template('customerLanding.html', data=queue_data)

@app.route('/login')
def login():
    user = load_user(request.args['username'])
    flask_login.login_user(user)
    nextUrl = request.args['next']
    return redirect(nextUrl)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login/{}'.format(users[flask_login.current_user.id]['type']))


@app.route('/thankyou')
def thankyou():
    return render_template('applicationSubmitted.html')

@app.route('/report/<id>')
def report(id):
    with open('data/queue.json') as queue:
        report_data = json.load(queue)[id]
    report_data['id'] = id
    with open('data/sample/allOutputData.json') as data:
        sample_data = json.load(data)
    return render_template('report.html', data=report_data, sample_data=sample_data)


@app.route('/add-to-queue', methods=['GET', 'POST'])
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

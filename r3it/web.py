from flask import Flask, request, redirect, send_from_directory
from jinja2 import Template
import uuid
import csv

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/queue')
def queue():
    data = []
    with open('data/queue.csv') as queue:
        reader = csv.DictReader(queue, delimiter='\t')
        next(reader, None)
        i = 1
        for row in reader:
            datarow = [i, row['datetime'], row['location'], row['status']]
            data.append(datarow)
            i = i+1
    template = Template(open('templates/queue.html', 'r').read())
    return template.render(data=data)


@app.route('/login')
def login():
    template = Template(open('templates/login.html', 'r').read())
    return template.render()


@app.route('/overview')
def overview():
    template = Template(open('templates/overview.html', 'r').read())
    return template.render()


@app.route('/add-to-queue', methods=['GET', 'POST'])
def add_to_queue():
    print(request.form)
    with open('data/queue.csv', 'a') as queue:
        writer = csv.writer(queue, delimiter='\t')
        writer.writerow([str(request.form['datetime']),
                         str(request.form['location']), str(request.form['status'])])
    return redirect('/queue')


@app.route('/send-file/<path:fullPath>')
def send_file(fullPath):
    path_pieces = fullPath.split('/')
    return send_from_directory('/'.join(path_pieces[0:-1]), path_pieces[-1])

@app.route('/application')
def application():
    template = Template(open('templates/application.html', 'r').read())
    return template.render()

if __name__ == '__main__':
    app.run(debug=True)
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
def main():
    template = Template(open('templates/overview.html', 'r').read())
    return template.render()


@app.route('/add-to-queue', methods=['GET', 'POST'])
def addToQueue():
    print(request.form)
    with open('data/queue.csv', 'a') as queue:
        writer = csv.writer(queue, delimiter='\t')
        writer.writerow([str(request.form['datetime']),
                         str(request.form['location']), str(request.form['status'])])
    return redirect('/queue')


@app.route('/send-file/<path:fullPath>')
def downloadModelData(fullPath):
    pathPieces = fullPath.split('/')
    return send_from_directory('/'.join(pathPieces[0:-1]), pathPieces[-1])


if __name__ == '__main__':
    app.run()

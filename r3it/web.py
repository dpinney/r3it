from flask import Flask
from jinja2 import Template

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/queue')
def queue():
	template = Template(open('templates/queue.html', 'r').read())
	return template.render(entries=['a','b','c'])

if __name__ == '__main__':
	app.run()
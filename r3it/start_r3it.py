import os, logging, config
from flask import Flask, redirect, request, render_template, url_for, send_from_directory
from subprocess import Popen

# Note: sudo python start_r3it.py on macOS since this will open low numbered ports.
# If you need some test certs: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout privkey.pem -days 365 -subj '/CN=localhost/O=NoCompany/C=US'

reApp = Flask('R3ITR')

@reApp.route('/')
def index():
	return 'NA'

@reApp.route('/.well-known/acme-challenge/<path:filename>')
def cert_renewal(filename):
	return send_from_directory('/opt/r3it/r3it/.well-known/acme-challenge/', filename)


@reApp.before_request
def before_request():
	if not request.url.startswith('http://' + config.DOMAIN + '/.well-known') and request.url.startswith('http://'):
		url = request.url.replace('http://', 'https://', 1)
		code = 301
		return redirect(url, code=code)

if __name__ == "__main__":
	# Start redirector:
	redirProc = Popen(['gunicorn', '-w', '1', '-b', '0.0.0.0:80', 'start_r3it:reApp'])
	# Start application:
	appProc = Popen(['gunicorn', '-w', '4', '-b', '0.0.0.0:443', '--certfile=cert.pem', '--ca-certs=fullchain.pem', '--keyfile=privkey.pem', '--preload', 'web:app','--worker-class=sync', '--access-logfile', 'r3it.access.log', '--error-logfile', 'r3it.error.log', '--capture-output'])
	appProc.wait()

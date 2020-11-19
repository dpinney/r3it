bind = '0.0.0.0:443'
workers = 4
worker_class = 'gevent'
worker_connections = 1000
keepalive = 5

keyfile = 'privkey.pem'
certfile = 'cert.pem'
ca_certs = 'chain.pem'

import os
import rq
import sys
import logging
import redis
from flask import Flask
from worker import conn

# Set module name
__module__ = 'cslocks'

app = Flask(__name__, static_folder=None)
app.config.update({
    'SIGNING_SECRET': os.environ.get('SIGNING_SECRET'),
    'REDIS_URL': os.environ.get('REDIS_URL','redis://')
})

app.task_queue = rq.Queue(connection=conn)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

# Allow app to find @app.route views
from cslocks import views

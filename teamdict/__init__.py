import os
import rq
import sys
import logging
import redis
import psycopg2
from flask import Flask
from worker import conn

# Set module name
__module__ = 'teamdict'

app = Flask(__name__, static_folder=None)
app.config.update({
    'SIGNING_SECRET': os.environ.get('SIGNING_SECRET'),
    'REDIS_URL': os.environ.get('REDIS_URL','redis://'),
    'DATABASE_URL': os.environ.get('DATABASE_URL')
})

app.task_queue = rq.Queue(connection=conn)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

app.dbconn = psycopg2.connect(app.config['DATABASE_URL'], sslmode='require')

# Allow app to find @app.route views
from teamdict import views

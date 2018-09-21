import os
import rq
import sys
import logging
import redis
from flask import Flask

# Set module name
__module__ = 'cslocks'

app = Flask(__name__, static_folder=None)
app.config.update({
    'SIGNING_SECRET': os.environ.get('SIGNING_SECRET'),
    'REDIS_URL': os.environ.get('REDIS_URL','redis://')
})


app.redis = redis.from_url(app.config['REDIS_URL'])
app.task_queue = rq.Queue('combo-queue', connection=app.redis)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

# Allow app to find @app.route views
from cslocks import views

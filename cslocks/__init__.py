import os
import rq
import sys
import logging
from redis import Redis
from flask import Flask

# Set module name
__module__ = 'cslocks'

app = Flask(__name__)
app.config.update({
    'SIGNING_SECRET': os.environ.get('SIGNING_SECRET'),
    'REDIS_URL': os.environ.get('REDIS_URL','redis://')
})


app.redis = Redis.from_url(app.config['REDIS_URL'])
app.task_queue = rq.Queue('combo-queue', connection=app.redis)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

class Config(object):
    # Get Redis server url from environment or use default
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    SIGNING_SECRET = os.environ.get('SIGNING_SECRET') or ''


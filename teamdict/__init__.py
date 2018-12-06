import os
import rq
import sys
import logging
import redis
import psycopg2
from pkg_resources import get_provider
from flask import Flask
from worker import conn

# Set module name
__module__ = 'teamdict'

def set_app_config():
    app_name = 'teamdict'
    upload_folder = '/uploads'
    provider = get_provider(app_name)

    return  {
        'name': app_name,
        'full_name': 'Slack Team Dictionary',
        'version': '0.1',
        'github_url': 'https://github.com/ChristopherDaw/slack-teamdict',
        'package_path': provider.module_path,
        'SIGNING_SECRET': os.environ.get('SIGNING_SECRET'),
        'SESSION_TYPE': 'redis',
        'REDIS_URL': os.environ.get('REDIS_URL','redis://'),
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'ACCESS_TOKEN': os.environ.get('ACCESS_TOKEN'),
        'ALLOWED_EXTENSIONS': set(['txt', 'csv']),
        'UPLOAD_FOLDER': provider.module_path + upload_folder,
    }

db_user=os.environ.get('DB_USER')
db_pass=os.environ.get('DB_PASS')
# Initialize flask app
app = Flask(__name__)
app.config.update(set_app_config())
app.task_queue = rq.Queue(connection=conn)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.dbconn = psycopg2.connect(app.config['DATABASE_URL'], sslmode='require', user=db_user, password=db_pass)

# Set up database table for mass data entry
with app.dbconn.cursor() as cur:
    query = ('CREATE TABLE IF NOT EXISTS data_entry_queue (' +
            'url_ext VARCHAR PRIMARY KEY, ' +
            'table_name VARCHAR, ' +
            'response_url VARCHAR, ' +
            'user_id VARCHAR, ' +
            'channel_id VARCHAR, ' +
            'message_ts NUMERIC(16, 6), ' +
            "exp_date TIMESTAMP NOT NULL DEFAULT now() + interval '2 minutes'" +
            ');')
    cur.execute(query)
    app.dbconn.commit()

# Allow app to find @app.route views
from teamdict import views

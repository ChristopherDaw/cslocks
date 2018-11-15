"""
util.py
Chris Daw
October 4, 2018

This module contains utility functions necessary for other modules of this app.
"""
import os
import psycopg2.extras
from teamdict import app
from teamdict.slack import *
from teamdict.validate import is_valid_request
import teamdict.postgres as db

def triage_command(job_data):
    """
    Send the request to the correct function

    Args:
        job_data (JobData): Object containing necessary informationr
            headers, form, and body of the original POST request.

    Returns:
        None
    """
    form = job_data.form
    job_type = job_data.job_type
    response_url = form['response_url']
    slash_command = form['command']

# Comment out for testing purposes
    if not is_valid_request(job_data):
        message = 'Access denied!'
        send_delayed_message(message, response_url)
        return

    text = form['text'].lower().split()

    if len(text) == 0:
        send_help(slash_command, response_url)
        return
    else:
        command = text[0]

    #TODO: Parameter checking before passing the buck to the database handler.
    if command == 'help' or command == '':
        #TODO: Allow for help on specific commands /lookup help <cmd>
        send_help(slash_command, response_url)

    if slash_command[1:] == 'dbmod' and job_type == 'modify':
        if command == 'create':
            db.create_table(form)
        elif command == 'drop':
            db.drop_table(form)
        elif command == 'add':
            db.add_data(form)
        elif command == 'populate':
            url = job_data.url
            db.data_entry(form, url)
        elif command == 'delete':
            db.delete_data(form)
        else:
            #TODO: make global vars for help and usage strings
            send_help(slash_command, response_url, message='Accepted commands')
    elif slash_command[1:] == job_type == 'lookup':
        if command == 'show':
            db.show_tables(form)
        elif len(text) <= 2:
            db.lookup(form)
        else:
            send_help(slash_command, response_url, message='Accepted commands')
    else:
        send_help(slash_command, response_url, message='Command not found.')

    return

def triage_response(job_data):
    """
    Send the interactive response to the correct function.

    Args:
        job_data (JobData): Object containing necessary informationr
            headers, form, and body of the original POST request.

    Returns:
        None
    """
    form = job_data.form
    response_url = form['response_url']

# Comment out for testing purposes
    if not is_valid_request(job_data):
        message = 'Access denied!'
        send_delayed_message(message, response_url)
        return

    actions = form['actions'][0] #'actions' is an array containing only a dict
    #TODO: sanity check on this triaging
    if actions['value'] == 'cancel':
        delete_original_msg(response_url)
    elif actions['value'] == 'done':
        message = "Thank You!"
        send_delayed_message(message, response_url, replace_original=True)
    elif actions['value'] == 'drop':
        db.drop_table(form)
    elif actions['value'] == 'delete':
        db.delete_data(form)
    elif actions['value'] == 'url_button':
        channel = form['channel']['id']
        message_ts = form['message_ts']
        api_call('chat.delete', token=app.config['ACCESS_TOKEN'],
                channel=channel, ts=message_ts)
    else:
        message = f'Action `{actions["value"]}` not supported!'
        send_delayed_message(message, response_url)

def handle_data_entry(job_data):
    data_entry = job_data.data
    token = app.config['ACCESS_TOKEN']
    channel = data_entry['channel_id']
    ts = data_entry['message_ts']

    response = api_call('chat.delete', token=token, channel=channel, ts=ts)

    print(f'Response from api_call: {response}')

def handle_file_upload(**kwargs):
    if 'ext' not in kwargs:
        return {}

    ext = kwargs['ext']
    with app.dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        query = ('DELETE FROM data_entry_queue WHERE ' +
                'url_ext = %s RETURNING *;')
        cur.execute(query, (ext,))
        dbrow = cur.fetchone()

    key = ''
    value = ''
    form = {}
    form['response_url'] = dbrow['response_url']
    form['table_name'] = dbrow['table_name']
    key_value_dict = {}
    uploads = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(uploads):
        if filename.split('_')[0] == ext:
            with open(os.path.join(uploads, filename), mode='r') as user_data:
                for row in user_data:
                    data = row.rstrip('\n').split(',')
                    if len(data) < 2:
                        #Improper formatting for this key-value pair
                        continue
                    key = data[0]
                    value = ' '.join(data[1:])
                    key_value_dict[key] = value
                    form['text'] = f'dbmod add table {key} {value}'
                    db.add_data(form)

            os.remove(os.path.join(uploads, filename))

def handle_upload_cancellation(**kwargs):
    if 'ext' not in kwargs:
        return {}

    ext = kwargs['ext']
    # Delete the database row for this file upload
    with app.dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        query = ('DELETE FROM data_entry_queue WHERE ' +
                'url_ext = %s RETURNING *;')
        cur.execute(query, (ext,))
        app.dbconn.commit()

    delete_uploaded_files(ext)

def delete_uploaded_files(ext):
    # Delete files associated with this upload session
    uploads = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(uploads):
        if filename.split('_')[0] == ext:
            os.remove(os.path.join(uploads, filename))

def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and ext in app.config['ALLOWED_EXTENSIONS']

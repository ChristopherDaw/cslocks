"""
util.py
Chris Daw
October 4, 2018

This module contains utility functions necessary for other modules of this app.
"""
from teamdict import app
from teamdict.slack import send_delayed_message, send_help, delete_original_msg
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
    url = job_data.url
    response_url = form['response_url']
    slash_command = form['command']

# Comment out for testing purposes
    if not is_valid_request(job_data):
        message = 'Access denied!'
        send_delayed_message(message, response_url)
        return

    text = form['text'].lower().split()
    print(text)

    if len(text) == 0:
        send_help(slash_command, response_url)
        return
    else:
        command = text[0]

    print(command)

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
    elif actions['value'] == 'drop':
        db.drop_table(form)
    elif actions['value'] == 'delete':
        db.delete_data(form)
    else:
        message = 'Action not supported!'
        send_delayed_message(message, response_url)

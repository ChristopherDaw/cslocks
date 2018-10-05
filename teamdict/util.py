"""
util.py
Chris Daw
October 4, 2018

This module contains utility functions necessary for other modules of this app.
"""
import teamdict.postgres as db
from teamdict.slack import send_delayed_message, send_help
from teamdict.validate import is_valid_request

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

# Commented out for testing purposes
#    if not is_valid_request(job_data):
#        message = "Access denied!"
#        send_delayed_message(message, response_url)
#        return

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
        elif command == 'add' or command == 'populate':
            db.add_data(form)
        elif command == 'delete':
            db.delete_data(form)
        else:
            #TODO: make global vars for help and usage strings
            send_help(slash_command, response_url, message='Accepted commands')
    elif slash_command[1:] == job_type == 'lookup':
        if text[0] == 'show':
            db.show_tables(form)
        elif len(text) <= 2:
            db.lookup(form)
        else:
            send_help(slash_command, response_url, message='Accepted commands')
    else:
        send_help(slash_command, response_url, message='Command not found.')

    return

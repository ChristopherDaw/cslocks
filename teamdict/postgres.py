"""
postgres.py
Chris Daw
October 4, 2018

This module defines functions to interface with a PostgreSQL database to
create and drop tables, add and delete rows of key-value pairs, and lookup
a key from one or many tables.

All methods in this module expect the command arguments to be formatted
correctly.
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import request
from hashlib import blake2b
from teamdict import app
from teamdict.slack import *

conn = app.dbconn

def create_table(form):
    """
    Build and execute a query to create a table to the database given a table
    with that name in the current channel does not yet exist.

    /dbmod create table_name

    Table names are formatted as:
        <team_domain>_<channel_id>_<table_name>
    to ensure every table across all workspaces are unique.

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        None
    """
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form, 1)
        if table_name is None:
            return

        query = ('CREATE TABLE %s (' +
                 'key VARCHAR PRIMARY KEY, ' +
                 'value VARCHAR, ' +
                 'date_modified TIMESTAMPTZ NOT NULL DEFAULT now()' +
                 ');'
                 )
        cur.execute(query, (as_is(table_name),))
        send_delayed_message(
                    f'Table `{short_name}` created!',
                    form['response_url'])
        conn.commit()

def drop_table(form):
    """
    Build and execute a query to drop a table from the database given the table
    specified exists in the current channel.

    /dbmod drop table_name

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        None
    """
    #Request coming from a slash command directly
    if 'text' in form:
        short_name, table_name = get_table_names(form, 1)
        if table_name is None:
            return

        drop_conf = {
                "title": "Are you sure?",
                "text": f"All data in {short_name} will be lost!",
                "ok_text": "Confirm",
                "dismiss_text": "Cancel"
                }
        drop_btn = Button('drop', f'Drop {short_name}',
                          danger = True, confirm=drop_conf)
        cancel_btn = Button('cancel', 'Cancel')
        buttons = [drop_btn, cancel_btn]
        send_delayed_message(
                f'Are you sure you want to drop {short_name}?',
                form['response_url'],
                attachments='This action cannot be undone.',
                callback_id=table_name,
                buttons=buttons
                )
    #Request coming from a button press in Slack
    else:
        with conn.cursor() as cur:
            short_name, table_name = add_short_name(form['callback_id'])
            if not is_table(table_name):
                send_delayed_message(
                        f'No table named `{short_name}` exists.',
                        form['response_url'])
                return
            query = 'DROP TABLE %s;'
            cur.execute(query, (as_is(table_name),))
            send_delayed_message(
                        f'Table `{short_name}` dropped!',
                        form['response_url'], replace_original=True)
            conn.commit()

def add_data(form):
    """
    Add a row containing a key-value pair and the date in the table specified.
    Rows are formatted like so:

        | key | value | date modified |

    Where the key must be unique to the table.

    /dbmod add table key value

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        None
    """
    with conn.cursor() as cur:
        if 'table_name' in form:
            short_name, table_name = add_short_name(form['table_name'])
        if not 'table_name' in form:
            short_name, table_name = get_table_names(form, 1)
            if table_name is None:
                return

        text = form['text'].split()
        key = text[2]
        value = ' '.join(text[3:])
        query = ('INSERT INTO %s (key, value) ' +
                'VALUES (%s, %s);')
        try:
            cur.execute(query, (as_is(table_name), key, value,))
        except psycopg2.IntegrityError:
            #TODO: Ask user if they wish to update the value of duplicate key.
            send_delayed_message(
                    f'Key `{key}` already exists in `{short_name}`',
                    form['response_url'])
            return

        send_delayed_message(
                f'Key `{key}` added to `{short_name}`',
                form['response_url'])
        conn.commit()

def data_entry(form, url):
    """Prepare a url for mass data entry"""
    with conn.cursor() as cur:
        response_url = form['response_url']
        short_name, table_name = get_table_names(form, 1)
        if table_name is None:
            return

        user_id = form['user_id']
        channel_id = form['channel_id']
        url_ext = blake2b(f'{user_id} {datetime.now()}'.encode('utf-8'),
                          digest_size=15).hexdigest()
        url = f'{url}data_entry/{url_ext}'

        query = ('INSERT INTO data_entry_queue ' +
                '(url_ext, table_name, response_url, user_id, channel_id) ' +
                'VALUES (%s, %s, %s, %s, %s);')
        cur.execute(query, (url_ext, table_name, response_url, user_id,
                            channel_id,))

        # Use api call for data_entry to allow for editing the message later
        done_button = Button('done', 'Done', style='primary')
        cancel_button = Button('cancel', 'Cancel')
        buttons = [done_button.dict, cancel_button.dict]
        atext = f'Link expires in two minutes\n<{url}>'
        attachments = [{
                'pretext': 'Data Entry',
                'actions': buttons,
                'text': atext,
                'color': '#003F87',
                'callback_id': url,
                'fallback': url,
                }]

        token = app.config['ACCESS_TOKEN']
        channel = form['channel_id']
        user = form['user_id']
        response = api_call('chat.postEphemeral', token=token, channel=channel,
                user=user, attachments=json.dumps(attachments))

        # Add message timestamp to data_entry queue
        print(f'Message_ts from api_call response: {response["message_ts"]}')
        message_ts = response['message_ts']
        query = ('UPDATE data_entry_queue ' +
                'SET message_ts = %s;')
        cur.execute(query, (message_ts,))

        conn.commit()

def delete_data(form):
    """
    Delete a row from the specified table where the key matches the given key.

    /dbmod delete table key

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        None
    """
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form, 1)
        if table_name is None:
            return

        text = form['text'].lower().split()
        key = text[2]
        query = ('DELETE FROM %s ' +
                'WHERE key = %s;')
        cur.execute(query, (as_is(table_name), key,))
        item_existed = int(cur.statusmessage.split()[1]) > 0
        if item_existed:
            send_delayed_message(
                    f'Key `{key}` deleted from `{short_name}`',
                    form['response_url'])
            conn.commit()
        else:
            send_delayed_message(
                    f'Key `{key}` was not found in `{short_name}`',
                    form['response_url'])

def show_tables(form):
    """
    Send a message with a list of all the tables in the current channel.

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        None
    """
    channel_name = form['channel_name']
    table_names = get_channel_tables(form)

    if len(table_names) == 0:
        send_delayed_message(
                f'No tables found in {channel_name}.',
                form['response_url'])
    else:
        plural_s = 's' if len(table_names) > 1 else ''
        short_name_arr = [table_name[0] for table_name in table_names]
        short_name_str = '\n'.join(short_name_arr)

        send_delayed_message(
                f'{len(table_names)} table{plural_s} found in {channel_name}.',
                form['response_url'],
                attachments=short_name_str)

#TODO: Add functionality to lookup multiple keys.
def lookup(form):
    """
    Lookup a value from the channel in which the command originated. If no
    table is specified, all the tables are searched.

    /lookup key [table]

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        None
    """
    text = form['text'].lower().split()

    key = text[0]
    values_found = [] #List of tuples, e.g. [(table, val), (table2, val2)]
    if len(text) == 1: #Find all instances of 'key' in all tables
        table_names = get_channel_tables(form)
        for names in table_names:
            short_name = names[0]
            value = lookup_helper(form, key, names)
            if len(value) > 0:
                values_found.append((short_name, value))
    elif len(text) == 2: #Find 'key' in the given table name
        names = get_table_names(form, 1)
        if names[0] is None:
            return
        short_name = names[0]
        value = lookup_helper(form, key, names)
        values_found.append((short_name, value))
    else:
        send_delayed_message(
                'Unable to execute command:',
                form['response_url'],
                attachments=f"form['command'] form['text']")
        return

    if len(values_found) == 0:
        send_delayed_message(
                f'No key found matching `{key}`.',
                form['response_url'])
    elif len(values_found) == 1:
        send_delayed_message(
                f'`{key}` found in {values_found[0][0]}:',
                form['response_url'],
                attachments=f'{key}: {values_found[0][1]}')
    else:
        values_str = ''
        for value_table_pair in values_found:
            table = value_table_pair[0]
            value = value_table_pair[1]
            values_str += f'{table}: {value}\n'
        send_delayed_message(
                f'`{key}` found in {len(values_found)} tables:',
                form['response_url'],
                attachments=values_str)


#TODO: document that this function does the query and returns the result
# and that the lookup() function sends a message to slack once it gets all the
# queries done.
def lookup_helper(form, key, table_names):
    """
    Builds and executes a query for the lookup() function to allow for multiple
    tables to be searched.

    Args:
        form (dict): Form data from the original POST request.
        key (str): The key for which we are searching.
        table_names (tuple): A tuple containing the long and short forms of
            the table name.

    Returns:
        A string containing the found value or an empty string if the key
        is not found in the table.
    """
    result = []
    with conn.cursor() as cur:

        short_name, table_name = table_names
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return ''

        query = ('SELECT value FROM %s ' +
                'WHERE key = %s;')
        cur.execute(query, (as_is(table_name), key,))
        result = cur.fetchall()

    if len(result) > 0:
        return result[0][0] #Extract value from a tuple in an array
    else:
        return result

def verify_ext(ext):
    """take an extension from /data_entry/<ext> and ensure it's in the
    data_entry_queue table"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        query = ('SELECT * FROM data_entry_queue WHERE ' +
                'url_ext = %s;')
        cur.execute(query, (ext,))
        results = cur.fetchone()
        #Check if request has not expired
        if results is None or results['exp_date'] < datetime.now():
            results = []

        return results

def fetch_data_entry_row(ext):
    """take an extension from /data_entry/<ext> and ensure it's in the
    data_entry_queue table"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        query = ('DELETE FROM data_entry_queue WHERE ' +
                'url_ext = %s RETURNING *;')
        cur.execute(query, (ext,))
        results = cur.fetchone()
        #Check if request has not expired
        if results is None or results['exp_date'] < datetime.now():
            results = []
        conn.commit()

        return results

#######################
#  UTILITY FUNCTIONS  #
######################

def get_table_names(form, tn_index):
    """
    Finds the table name and builds the long form table name stored in the db.
    This function does not ensure the table exists. This should be done in the
    function using get_table_names().

    Args:
        form (dict): Form data from the original POST request.
        tn_index (int): The index at which the table_name appears in the
            command args.

    Returns:
        A tuple containing the short and long forms of the table name found.
    """
    text = form['text'].lower().split()
    team_domain = form['team_domain']
    channel_id = form['channel_id']
    short_name = text[tn_index]
    table_name = f'{team_domain}_{channel_id}_{short_name}'
    if not is_table(table_name) and not text[0] == 'create':
        send_delayed_message(
                f'No table named `{short_name}` exists.',
                form['response_url'])
        return (None, None)
    return (short_name, table_name)

def add_short_name(table_name):
    """
    Adds the short form name of the table specified. The input is expected to
    match the format of table names specified in create_table().

    Args:
        table_name (str): The long form name of the table.

    Returns:
        A tuple containing the short and long forms of the table name found.
    """
    name = table_name.split('_')
    name.pop(0)
    name.pop(0)
    short_name = '_'.join(name)

    return (short_name, table_name)

def get_channel_tables(form):
    """
    Finds and returns all tables in the channel where the command originated.

    Args:
        form (dict): Form data from the original POST request.

    Returns:
        A list of tuples each containing the short and long form of the
        table name found.
    """
    short_long_names = []
    with conn.cursor() as cur:
        team_domain = form['team_domain']
        channel_id = form ['channel_id']
        table_prefix = f"^{team_domain}_{channel_id}".lower()

        query = ('SELECT table_name ' +
                'FROM information_schema.tables ' +
                'WHERE table_name ~ %s;')
        cur.execute(query, (table_prefix,))
        tables = [table[0] for table in cur.fetchall()]
        short_long_names = [add_short_name(table) for table in tables]

    return short_long_names

def is_table(table_name):
    """
    Utility function to test existance of a given table name.

    Args:
        table_name (str): The name of the table to be checked.

    Returns:
        True if table exists
        False if table does not exist
    """
    table_name = table_name.lower()
    with conn.cursor() as cur:
        query = ('SELECT EXISTS (' +
                'SELECT 1 FROM pg_tables ' +
                'WHERE tablename = %s' +
                ');'
                )
        cur.execute(query, (table_name,))
        result = cur.fetchone()[0]

    return result

def as_is(table_name):
    """Returns an AsIs object to avoid quoted table_names for db queries."""
    return psycopg2.extensions.AsIs(table_name)

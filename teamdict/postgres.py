import os
import psycopg2
from teamdict import app
from teamdict.slack import send_delayed_message

conn = app.dbconn

def create_table(form):
    """
    Build and execute a query to create a table on the database given a table
    with that name in the current channel does not yet exist. This function
    assumes the command is formatted properly with the correct amount of
    arguments, e.g.:

    </command> create table_name

    Args:
        form (dict): Dictionary containing information from the original POST.

    Returns:
        None
    """
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form)
        if is_table(table_name):
            send_delayed_message(
                    f'Table `{short_name}` exists.',
                    form['response_url'])
            return

        query = ('CREATE TABLE %s (' +
                 'key VARCHAR UNIQUE NOT NULL PRIMARY KEY, ' +
                 'value VARCHAR, ' +
                 'date_modified TIMESTAMPTZ NOT NULL DEFAULT now()' +
                 ');'
                 )
        cur.execute(query, (psycopg2.extensions.AsIs(table_name),))
        send_delayed_message(
                    f'Table `{short_name}` created!',
                    form['response_url'])
        conn.commit()

#TODO: Add a confirmation button/text to ensure the user wants to delete a table
#Slack api has "destructive buttons" for confirmation of destructive actions.
def drop_table(form):
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form)
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return

        query = 'DROP TABLE %s;'
        cur.execute(query, (psycopg2.extensions.AsIs(table_name),))
        send_delayed_message(
                    f'Table `{short_name}` dropped!',
                    form['response_url'])
        conn.commit()

def add_data(form):
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form)
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return

        text = form['text'].split()
        key = text[2]
        value = text[3]
        query = ('INSERT INTO %s (key, value)' +
                'VALUES (%s, %s);')
        try:
            cur.execute(query, (psycopg2.extensions.AsIs(table_name), key, value,))
        except psycopg2.IntegrityError:
            #TODO: Ask user if they wish to update the value of duplicate key.
            send_delayed_message(
                    f'Key `{key}` already exists in `{short_name}`',
                    form['response_url'])
            return

        send_delayed_message(
                f'Key `{key}` added to `{table_name}`',
                form['response_url'])
        conn.commit()

def delete_data(form):
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form)
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return

        text = form['text'].split()
        key = text[2]
        query = ('DELETE FROM %s ' +
                'WHERE key = %s;')
        cur.execute(query, (psycopg2.extensions.AsIs(table_name), key,))
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


def lookup(form):
    return

def get_table_names(form):
    text = form['text'].lower().split()
    team_domain = form['team_domain']
    channel_id = form['channel_id']
    short_name = text[1]
    table_name = f'{team_domain}_{channel_id}_{short_name}'

    return (short_name, table_name)

def is_table(table_name):
    """
    Utility function to test existance of a given table name.

    Args:
        table_name (str): The name of the table to be checked.

    Returns:
        True if table exists
        False if table does not exist
    """
    result = False
    with conn.cursor() as cur:
        query = ('SELECT EXISTS (' +
                'SELECT 1 FROM pg_tables ' +
                'WHERE tablename = %s' +
                ');'
                )
        cur.execute(query, (table_name,))
        result = cur.fetchone()[0]

    return result


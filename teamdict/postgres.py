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
        short_name, table_name = get_table_names(form, 1)
        if is_table(table_name):
            send_delayed_message(
                    f'Table `{short_name}` exists.',
                    form['response_url'])
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

#TODO: Add a confirmation button/text to ensure the user wants to delete a table
#Slack api has "destructive buttons" for confirmation of destructive actions.
def drop_table(form):
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form, 1)
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return

        query = 'DROP TABLE %s;'
        cur.execute(query, (as_is(table_name),))
        send_delayed_message(
                    f'Table `{short_name}` dropped!',
                    form['response_url'])
        conn.commit()

def add_data(form):
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form, 1)
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return

        text = form['text'].split()
        key = text[2]
        value = text[3]
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

def delete_data(form):
    with conn.cursor() as cur:
        short_name, table_name = get_table_names(form, 1)
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
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

def lookup(form):
    text = form['text'].lower().split()

    if text[0] == 'find':
        text.pop(0)

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
    result = []
    with conn.cursor() as cur:

        short_name, table_name = table_names
        if not is_table(table_name):
            send_delayed_message(
                    f'No table named `{short_name}` exists.',
                    form['response_url'])
            return

        query = ('SELECT value FROM %s ' +
                'WHERE key = %s;')
        cur.execute(query, (as_is(table_name), key,))
        result = cur.fetchall()

    if len(result) > 0:
        return result[0][0] #Extract value from a tuple in an array
    else:
        return result

#######################
#  UTILITY FUNCTIONS  #
######################

def get_table_names(form, tn_index):
    text = form['text'].lower().split()
    team_domain = form['team_domain']
    channel_id = form['channel_id']
    short_name = text[tn_index]
    table_name = f'{team_domain}_{channel_id}_{short_name}'

    return (short_name, table_name)

def add_short_name(table_name):
    name = table_name.split('_')
    name.pop(0)
    name.pop(0)
    short_name = '_'.join(name)

    return (short_name, table_name)

def get_channel_tables(form):
    tables = []
    with conn.cursor() as cur:
        team_domain = form['team_domain']
        channel_id = form ['channel_id']
        table_prefix = f"^{team_domain}_{channel_id}"

        query = ('SELECT table_name ' +
                'FROM information_schema.tables ' +
                'WHERE table_name ~ %s;')
        cur.execute(query, (table_prefix,))
        tables = [table[0] for table in cur.fetchall()]
        #TODO: Figure out how to break apart what the cursor fetched
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

    if result:
        return result
    else:
        return False

def as_is(table_name):
    return psycopg2.extensions.AsIs(table_name)

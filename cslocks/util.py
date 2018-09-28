import cslocks.postgres as db
from cslocks.validate import is_valid_request

def triage_command(request):
    """
    Send the request to the correct function

    Args:
        request (Request): Flask object containing necessary information.

    Returns:
        None
    """
    form = request.form
    response_url = form['response_url']
    slash_command = form['command']

    if not is_valid_request(request):
        message = "Access denied!"
        send_delayed_message(message, response_url)
        return

    text = form['text'].lower().split()

    if len(text) < 2:
        send_help(slash_command, response_url)
        return
    else:
        command = text[0]

    if command == 'help' or command == '':
        send_help(slash_command, response_url)
    elif command == 'create':
        db.create_table(form)
    elif command == 'add' or command == 'populate':
        db.add_data(form)
    elif command == 'delete':
        db.delete_data(form)
    elif command == 'drop':
        db.drop_table(form)
    elif db.is_table(command):
        db.lookup(form)
    else:
        send_help(slash_command, response_url, message='Command not found.')

    return

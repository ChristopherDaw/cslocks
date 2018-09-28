import json
import requests

def send_help(command, response_url, message=''):
    """
    Wrapper for send_delayed_message to send the user the help text along
    with any relevant error message they may have caused.

    Args:
        command (str): The slash command they used, e.g. /lookup.
        response_url (str): The url to which we send the message POST request.
        message (str): (Optional) Text to be displayed before the help message.

    Returns:
        None
    """
    usage_str = f'Usage: {command} <command> [<args>] [--help]'
    if message == '':
        send_delayed_message(usage_str, response_url)
    else:
        send_delayed_message(message, response_url, attachments=usage_str)

#TODO: Flesh this out to accept the creation of buttons and other special
#formatting like optional markdown, etc.
def send_delayed_message(message, response_url, attachments=''):
    """
    Sends a message to the response url provided in the original
    POST request with specified contents.

    Args:
        message (str): The contents of the base message sent to user.
        response_url (str): The url to send our response POST request to.
        attachments (str): The contents of the sub-message sent to user.

    Returns:
        None
    """
    # Slack requires the Content-type header be application/json
    print(message + "\n" + attachments)
    headers = {'Content-type': 'application/json'}
    payload_dict = {
        "text": message,
        "mrkdwn": True,
        "attachments": [
            {
                "text": attachments,
                "mrkdwn_in": ["text"]
            }
        ]
    }

    req = requests.post(
            response_url,
            data=json.dumps(payload_dict),
            headers=headers
        )


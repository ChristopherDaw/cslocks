"""
slack.py
Chris Daw
October 4, 2018

This module interfaces directly with the Slack API to perform actions
necessary to communicate with the end user in Slack such as sending messages
in response to the use of a slash command.
"""

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
        attachments (str): (Optional) The contents of the message attachment.

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


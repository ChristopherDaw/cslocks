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

def delete_original_msg(response_url):
    """Deletes a message at the invocation of a cancelling button press"""
    headers = {'Content-type': 'application/json'}
    payload_dict = {'delete_original': True}
    req = requests.post(
            response_url,
            data=json.dumps(payload_dict),
            headers=headers
        )


#TODO: Flesh this out to accept the creation of buttons and other special
#formatting like optional markdown, etc.
def send_delayed_message(message, response_url, callback_id='',
                        attachments='', buttons=[], replace_original=False):
    """
    Sends a message to the response url provided in the original
    POST request with specified contents.

    Args:
        message (str): The contents of the base message sent to user.
        response_url (str): The url to send our response POST request to.
        callback_id (str): Required if using buttons, id used in slack response.
        attachments (str): (Optional) The contents of the message attachment.
        buttons (list): (Optional) A list with details for buttons in the msg.
        replace_original (bool): (Optional) Used only when replacing a message
            with buttons in it with a resulting consequent message.

    Returns:
        None
    """
    if len(buttons) > 0:
        buttons = [btn.dict for btn in buttons]

    # Slack requires the Content-type header be application/json
    headers = {'Content-type': 'application/json'}
    payload_dict = {
        "text": message,
        "mrkdwn": True,
        "replace_original": replace_original,
        "attachments": [
            {
                "text": attachments,
                "mrkdwn_in": ["text"],
                "callback_id": callback_id,
                "actions": buttons
            }
        ]
    }

    req = requests.post(
            response_url,
            data=json.dumps(payload_dict),
            headers=headers
        )

class Button:
    """
    Button object for easily sending buttons to send_delayed_message()

    If included, the confirm dictionary must include 4 keys:
        'title': Title of the confirmation message
        'text': Text in the confirmation message
        'ok_text': The text shown if the confirmation button is selected
        'dismiss_text': The text shown if the confirmation button is dismissed
    """
    def __init__(self, name, text, danger=False, confirm={}):
        self.name = name
        self.text = text
        self.danger = danger
        self.confirm = confirm
        self.build_dict()

    def build_dict(self):
        self.dict = {
                "name": self.name,
                "text": self.text,
                "type": "button",
                "value": self.name,
                }
        if self.danger:
            self.dict["style"] = "danger"
        if len(self.confirm) > 0:
            self.dict["confirm"] = self.confirm

import time
import json
import requests
from cslocks.validate import is_valid_request

def send_delayed_message(req_form):
    response_url = req_form['response_url']
    content = str(req_form)

    payload_dict = {
        "text": "Original POST request",
        "attachments": [
            {
                "text": content
            }
        ]
    }

    req = requests.post(response_url, data=json.dumps(payload_dict))

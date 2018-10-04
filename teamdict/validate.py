"""
validate.py
Chris Daw
October 4, 2018

This module reviews a POST request to ensure it originated from slack. The
computation done here complies with Slack's "Verifying requests from Slack"
API docs page found here:
    https://api.slack.com/docs/verifying-requests-from-slack
"""
import os
import hmac
import hashlib

def is_valid_request(request):
    """
    Follows Slack's cryptographic method of ensuring a POST request
    originates from Slack by comparing a signature in the request to
    a signature computed with HMAC.

    Args:
        request (Request): A POST request from flask.

    Returns:
        True if the request originates from Slack, False otherwise.
    """
    computed_signature = compute_signature(request)
    slack_signature = request.headers['X-Slack-Signature']

    return hmac.compare_digest(computed_signature, slack_signature)

def compute_signature(request):
    """
    Computes the SHA256 HMAC hash using the signing secret from Slack
    as the key and specific data from the POST request as the body.

    Args:
        request (Request): A POST request from flask.

    Returns:
        Return a string containing the computed signature for verification
    """
    versionno = 'v0'
    timestamp = request.headers['X-Slack-Request-Timestamp']
    body = request.body

    basestr = bytes(f"{versionno}:{timestamp}:{body}", 'utf-8')
    secret = bytes(os.environ.get('SIGNING_SECRET'), 'utf-8')

    # Prepend 'v0=' onto the string as the 'X-Slack-Signature also includes it.
    return 'v0=' + hmac.new(secret, basestr, hashlib.sha256).hexdigest()

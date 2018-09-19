import os
import hmac
import hashlib

def valid_request(request):
    computed_signature = compute_signature(request)
    slack_signature = request.headers['X-Slack-Signature']

    return compare_signatures(computed_signature, slack_signature)

def compute_signature(request):
    body = request.get_data(as_text=True)
    versionno = 'v0'
    timestamp = request.headers['X-Slack-Request-Timestamp']

    basestr = bytes("{}:{}:{}".format(versionno, timestamp, body), 'utf-8')
    secret = bytes(os.environ.get('SIGNING_SECRET'), 'utf-8')

    return 'v0=' + hmac.new(secret, basestr, hashlib.sha256).hexdigest()

def compare_signatures(sig1, sig2):
    return hmac.compare_digest(sig1, sig2)

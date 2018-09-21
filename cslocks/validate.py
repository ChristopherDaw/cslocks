import os
import hmac
import hashlib

def is_valid_request(request):
    computed_signature = compute_signature(request)
    slack_signature = request.headers['X-Slack-Signature']

    return hmac.compare_digest(computed_signature, slack_signature)

def compute_signature(request):
    body = request.get_data(as_text=True)
    versionno = 'v0'
    timestamp = request.headers['X-Slack-Request-Timestamp']

    basestr = bytes(f"{versionno}:{timestamp}:{body}", 'utf-8')
    secret = bytes(os.environ.get('SIGNING_SECRET'), 'utf-8')

    return 'v0=' + hmac.new(secret, basestr, hashlib.sha256).hexdigest()

import os
import hmac
import hashlib

def is_valid_request(request):
    """Return true is request originates from Slack

    Follows Slack's cryptographic method of ensuring a POST request
    originates from Slack by comparing a signature in the request to
    a computed signature.
    """
    computed_signature = compute_signature(request)
    slack_signature = request.headers['X-Slack-Signature']
    print(f"Received: {computed_signature}\nExpted:{slack_signature}")

    return hmac.compare_digest(computed_signature, slack_signature)

def compute_signature(request):
    """Return a string containing the computed signature for verification

    Computes the SHA256 HMAC hash  using the signing secret from Slack
    as the key and specific data from the POST request as the body.
    """
    versionno = 'v0'
    timestamp = request.headers['X-Slack-Request-Timestamp']
    body = request.body

    basestr = bytes(f"{versionno}:{timestamp}:{body}", 'utf-8')
    print(basestr)
    secret = bytes(os.environ.get('SIGNING_SECRET'), 'utf-8')

    # Prepend 'v0=' onto the string as the 'X-Slack-Signature also includes it.
    return 'v0=' + hmac.new(secret, basestr, hashlib.sha256).hexdigest()

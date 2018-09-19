import sys
import logging
from hmac_hash import compute_signature, compare_signatures
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

@app.route('/')
def homepage():
    the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")

    return """
    <h1>Hello heroku</h1>
    <p>It is currently {time}.</p>

    <img src="http://loremflickr.com/600/400">
    """.format(time=the_time)

@app.route('/slack/receive', methods=['POST', 'GET'])
def slash_command():
    if request.method == 'POST':
        #Ensure the request came from Slack
        return request.get_data()
        computed_signature = compute_signature(request)
        slack_signature = request.headers['X-Slack-Signature']
        if compare_signatures(computed_signature, slack_signature):
            return 'success'
        else:
            return "expecting: {}\ngot: {}".format(slack_signature, computed_signature);


        form_dict = request.form.to_dict()
        return form_dict['text']

    return "This is from flask for slack"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

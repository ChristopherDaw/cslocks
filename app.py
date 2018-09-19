import sys
import logging
from validate import valid_request
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
        if valid_request(request):
            return 'success'
        else:
            return 'Access Denied'


        form_dict = request.form.to_dict()
        return form_dict['text']

    return "This is from flask for slack"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

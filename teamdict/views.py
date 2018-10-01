from flask import request
from datetime import datetime
from teamdict import app
from teamdict.redis import queue_task

@app.route('/')
def homepage():
    the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")

    return """
    <h1>Hello heroku</h1>
    <p>It is currently {time}.</p>

    <img src="http://loremflickr.com/600/400/bird">
    """.format(time=the_time)

@app.route('/slack/receive', methods=['POST', 'GET'])
def slash_command():
    if request.method == 'POST':
        return queue_task(request)

    return "This is from flask for slack"

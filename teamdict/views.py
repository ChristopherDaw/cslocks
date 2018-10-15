"""
views.py
Chris Daw
October 4, 2018

This module defines the routes for flask endpoints.
"""
from flask import request
from datetime import datetime
from teamdict import app
from teamdict.postgres import verify_ext
from teamdict.redis import queue_task
from teamdict.slack import send_delayed_message, delete_original_msg

@app.route('/')
def homepage():
    the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")

    return """
    <h1>Hello heroku</h1>
    <p>It is currently {time}.</p>

    <img src="http://loremflickr.com/600/400/bird">
    """.format(time=the_time)

@app.route('/slack/lookup', methods=['POST', 'GET'])
def lookup():
    if request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'lookup')

    return "This is from flask for slack"

@app.route('/slack/modify', methods=['POST', 'GET'])
def modify():
    print(request.url_root)
    if request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'modify')

    return "This is from flask for slack"

@app.route('/slack/response', methods=['POST', 'GET'])
def response():
    if request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'response')

    return "This is from flask for slack"

@app.route('/data_entry/<ext>', methods=['POST', 'GET'])
def data_entry(ext):
    if request.method == 'GET':
        data = verify_ext(ext)
        if len(data) == 0:
            #Render failure page
            return ("<h1>Try again</h1>", 403)
        elif len(data) > 0:
            #Render data entry page
            db_row = data[0]
            response_url = db_row[2]
            table_name = db_row[1]
            #TODO: Find way to delete or change message with the url in it
            send_delayed_message("Thank you", response_url, replace_original=True)
            the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")
            return ("""
            <h1>Populate {table_name}</h1>
            <p>It is currently {time}.</p>

            <img src="http://loremflickr.com/600/400/bird">
            """.format(table_name=table_name,time=the_time), 200)

    return "This is from flask for slack"

@app.route('/test', methods=['POST', 'GET'])
def testing():
    if request.method == 'POST':
        print(request)

    return ('', 200)


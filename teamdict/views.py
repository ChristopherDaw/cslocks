"""
views.py
Chris Daw
October 4, 2018

This module defines the routes for flask endpoints.
"""
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
        verify_ext(ext)
        the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")
        return """
        <h1>Hello heroku</h1>
        <p>It is currently {time}.</p>

        <img src="http://loremflickr.com/600/400/bird">
        """.format(time=the_time)

    elif request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'response')

    return "This is from flask for slack"

@app.route('/test', methods=['POST', 'GET'])
def testing():
    if request.method == 'POST':
        print(request)

    return ('', 200)

def verify_ext(ext):
    """Take an extension from /data_entry/<ext> and ensure it's in the
    data_entry_queue"""
    with app.dbconn.cursor() as cur:
        query = ('DELETE FROM data_entry_queue WHERE ' +
                'url_ext = %s RETURNING *;')
        cur.execute(query, (ext,))
        results = cur.fetchall()
        print(results)

        #TODO: Find what was returned by the query if anything

        app.dbconn.commit()


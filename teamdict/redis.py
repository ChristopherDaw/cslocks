"""
redis.py
Chris Daw
October 4, 2018

This module takes a POST request from flask originating from Slack and queues
a job to handle the incomming request in a Redis queue. After the task is
queued, a 200 response is sent to confirm receipt of payload. For the purposes
of this module, the request is assumed to be a POST request.
"""
import rq
import json
from redis import Redis
from flask import request
from teamdict import app
from teamdict.util import triage_command, triage_response

def queue_task(request, req_body, job_type):
    """
    Enqueue a job in the Redis queue.

    Args:
        request (Request): The request object from flask.
        req_body (str): Text representation of the request for validation.
        job_type (str): Describes what functions the command has access to.

    Returns:
        A tuple containing the empty string and the integer 200 to respond to
        the original request.
    """
    headers = dict(request.headers.to_list())
    form = request.form.to_dict()

    if job_type == 'response':
        form = json.loads(form['payload'])
        job_data = JobData(headers, form, req_body, job_type)
        rq_job = app.task_queue.enqueue(triage_response, job_data)
    else:
        job_data = JobData(headers, form, req_body, job_type)
        rq_job = app.task_queue.enqueue(triage_command, job_data)
    return ('', 200)

class JobData:
    """JobData object for communicating a job's data to triage_command()"""
    def __init__(self, headers, form, body, job_type):
        self.headers = headers
        self.form = form
        self.body = body
        self.job_type = job_type

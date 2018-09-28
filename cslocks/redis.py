import rq
from redis import Redis
from cslocks import app
from flask import request
from cslocks.util import triage_command
from cslocks.slack import send_help

def queue_task(request):
    headers = dict(request.headers.to_list())
    form = request.form.to_dict()
    validation_data = request.get_data(as_text=True)

    job_data = JobData(headers, form, validation_data)
    rq_job = app.task_queue.enqueue(triage_command, job_data)
    return ('', 200)

class JobData:
    def __init__(self, headers, form, body):
        self.headers = headers
        self.form = form
        self.body = body

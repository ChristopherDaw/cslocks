import rq
from redis import Redis
from cslocks import app
from cslocks.fetch import send_delayed_message
from cslocks.validate import is_valid_request

def queue_task(request):
    if is_valid_request(request):
        form = request.form.to_dict()
        rq_job = app.task_queue.enqueue(send_delayed_message, form)
        print(f"rq job made\n{rq_job.get_id()}\n{rq_job.is_finished}\n")
        print(f"# jobs: {len(app.task_queue)}")
        print(f"failed jobs: {app.redis.get_failed_queue().count}")
        return ('', 200)
    else:
        return ('', 403)

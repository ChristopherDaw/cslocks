web: gunicorn cslocks:app --log-file=-
worker: rq worker -u $REDIS_URL combo-queue

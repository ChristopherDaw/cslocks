"""
views.py
Chris Daw
October 4, 2018

This module defines the routes for flask endpoints.
"""
import os
from flask import request, render_template, url_for, redirect, flash, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from teamdict import app
from teamdict.postgres import verify_ext
from teamdict.redis import queue_task, queue_util
from teamdict.util import handle_upload_cancellation, handle_file_upload, allowed_file

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/slack/lookup', methods=['POST', 'GET'])
def lookup():
    if request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'lookup')

    else:
        return redirect(url_for('homepage'))

@app.route('/slack/modify', methods=['POST', 'GET'])
def modify():
    if request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'modify')

    else:
        return redirect(url_for('homepage'))

@app.route('/slack/response', methods=['POST', 'GET'])
def response():
    if request.method == 'POST':
        req_body = request.get_data(as_text=True)
        return queue_task(request, req_body, 'response')

    else:
        return redirect(url_for('homepage'))

@app.route('/data_entry/<ext>', methods=['POST', 'GET'])
def data_entry(ext):
    # When a user navigates to the URL for data entry
    if request.method == 'GET':
        #TODO: Make this in the redis queue
        data = verify_ext(ext)
        if len(data) == 0:
            # Render failure page
            return ("<h1>Try again</h1>", 403)
        elif len(data) > 0:
            # Extract data from database row
            print(data)
            table_name = data['table_name'].split('_')[1]
            req_body = request.get_data(as_text=True)

            # Render data entry page
            return render_template('dataentry.html', table_name=table_name, url_ext=ext)

    # When a user uploads a file for data entry
    elif request.method == 'POST':
        # Make sure the file is valid and then save it
        if 'file' in request.files:
            file = request.files['file']
            if not allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                flash(f'Files of {ext} type are not allowed!')
                return('', 200)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(f'saving {filename} to {os.path.join(app.config["UPLOAD_FOLDER"], ext+"_"+filename)}')
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], ext + '_' + filename))
                print(f'os.listdir(upload_folder):\n{os.listdir(app.config["UPLOAD_FOLDER"])}')
                return('', 200)

        # If user presses a nav button 'Continue' or 'Cancel'
        else:
            form = request.form.to_dict()
            if 'navigation' in form:
                navigation = form['navigation']
                if navigation == 'continue':
                    # Handle file(s) that have been uploaded
                    response_json = queue_util(handle_file_upload, 'continue', ext=ext)
                    return jsonify(response_json), 202
                elif navigation == 'cancel':
                    # Handle cancellation of file upload
                    response_json = queue_util(handle_upload_cancellation, 'cancel', ext=ext)
                    return jsonify(response_json), 202
            # Ajax request for the status of the Redis task
            elif 'task_id' in form:
                task_id = form['task_id']
                rq_task = app.task_queue.fetch_job(task_id)
                if rq_task:
                    response_json = {
                        'status': 'success',
                        'data': {
                            'task_id': task_id,
                            'task_status': rq_task.get_status(),
                        }
                    }
                    if rq_task.get_status() == 'finished':
                        if rq_task.meta['type'] == 'continue':
                            response_json['data']['redirect'] = url_for('success')
                        elif rq_task.meta['type'] == 'cancel':
                            response_json['data']['redirect'] = url_for('homepage')
                else:
                    response_json = {'status': 'error'}
                return jsonify(response_json), 202

@app.route('/success')
def success():
    return render_template('success.html'), 200

@app.route('/test', methods=['POST', 'GET'])
def testing():
    if request.method == 'POST':
        print(request.get_data(as_text=True))

    else:
        return redirect(url_for('homepage'))

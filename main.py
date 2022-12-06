from flask import (
    Flask,
    request,
    jsonify,
    url_for
)
from celery_flask_configuration import make_celery
import time

flask_app = Flask(__name__)
celery = make_celery(flask_app)


@celery.task(name="simple_celery_flask_demo.long_sleep", bind=True)
def long_sleep(self, tot_time, name):
    for i in range(tot_time):
        time.sleep(i)
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': tot_time,
                                'status': name+str(i)})

    return {'current': tot_time, 'total': tot_time, 'status': 'Task completed!',
            'result': 42}


@flask_app.route('/status/<task_id>')
def task_status(task_id):
    task = long_sleep.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@flask_app.route("/time_sleep/", methods=["GET", "POST"])
def hello():
    params = request.get_json(force=True)
    time = params.get("time")
    name = params.get("name")
    task = long_sleep.apply_async(args=[time, name])
    return jsonify({"task_id": task.id}), 202, {'Location': url_for('task_status',
                                                                    task_id=task.id)}
@flask_app.route("/check/")
def check():
    i = celery.control.inspect()
    return i.active()

@flask_app.route('/')
def hello_world():
    return "hello"


if __name__ == "__main__":
    flask_app.run(host='127.0.0.1', port=5000)


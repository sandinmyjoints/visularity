import atexit
from collections import OrderedDict, defaultdict
import Queue
import json
import logging
import threading
import sys

from flask import Flask, request, render_template
from flask.helpers import jsonify
from flask.wrappers import Response
import requests

import workers

try:
    import settings
except Exception, ex:
    raise Exception("settings could not be imported: %s" % ex)

app = Flask(__name__)
app.config.from_object(__name__)


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(levelname)s:%(name)s:%(threadName)s: %(message)s")
logger = logging.getLogger(__name__)
#logger = logging


# App globals
similarity_scores = OrderedDict()
cluster_data = defaultdict(dict, **{k: {"name": "top", "size": 10} for k in settings.CLUSTER_TYPES.iterkeys()})
dict_and_scores_lock = threading.RLock()
counter = 0

new_submissions = Queue.Queue()
processed_submissions = Queue.Queue()

@app.route('/')
def submit_text_form():
    return render_template('submit_text.html', hookbox_channel=settings.CHANNEL_NAME)


@app.route('/submit_text', methods=['POST'])
def submit_text():
    text = request.form.get('text', '').strip()
    if text:
        new_submissions.put(text)
    return Response('ok')


@app.route('/hookbox/', methods=['GET', 'POST'])
def connect():

    global counter
    response_data = None

    if request.method == 'POST':

        action = request.form.get('action')

        logger.debug("hookbox action: %s" % action)
        if action == 'connect':
            counter += 1
            response_data = [True, {'name': 'User%d' % counter}]

        elif action == 'subscribe':
            response_data = [True, {}]

        elif action == 'publish':
            response_data = [False, {}]

        elif action == 'poll':
            response_data = [False, {}]

        elif action == 'create_channel':
            response_data = [True, {}]

        else:
            logger.warning('got unknown hookbox action %s' % action)
            response_data = [False, {}]

    return Response(json.dumps(response_data))


@app.route('/visualize/')
def visualize():
    global similarity_scores

    return render_template('visualize.html', computed_matches=similarity_scores, hookbox_channel=settings.CHANNEL_NAME)


@app.route('/cluster/<type>/')
def cluster(type):
    global cluster_data
    with dict_and_scores_lock:
        return jsonify(**cluster_data[type])


class DataRefresher(workers.StoppableThread):

    def __init__(self, processed_submissions, **kwargs):
        super(DataRefresher, self).__init__(**kwargs)
        self.processed_submissions = processed_submissions

    def run(self):
        global cluster_data, similarity_scores

        while not self.stopped():
            try:
                work_done = self.processed_submissions.get(timeout=1)
                with dict_and_scores_lock:
#                    similarity_scores = work_done["similarity_scores"]

                    for cluster_type in settings.CLUSTER_TYPES:
                        cluster_data[cluster_type] = work_done[cluster_type]

                # tell hookbox clients to refresh
                params = {
                    "payload": json.dumps([work_done["document"]]),  # hookbox wants json in the query string
                    "channel_name": settings.CHANNEL_NAME,
                    "security_token": settings.API_SECRET,
                }
                r = requests.get("http://127.0.0.1:8001/web/publish", params=params)
                if r.status_code != 200:
                    logger.warning("got %d status code sending refresh message to hookbox" % r.status_code)

                self.processed_submissions.task_done()
            except Queue.Empty:
                continue

        logger.info("exiting")


if __name__ == '__main__':
    similarity_calculator = workers.SimilarityCalculator(name="calculator", in_queue=new_submissions, out_queue=processed_submissions)
    similarity_calculator.start()

    data_refresher = DataRefresher(name="refresher", processed_submissions=processed_submissions)
    data_refresher.start()

    app.run()
    #    app.run(host='0.0.0.0')


@atexit.register
def stop_consumer():
    logger.debug("atexit")
    similarity_calculator.stop()
    data_refresher.stop()
    similarity_calculator.join()
    data_refresher.join()

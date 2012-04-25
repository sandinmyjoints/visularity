import atexit
from collections import OrderedDict, defaultdict
import Queue
import json
import logging
import subprocess
import threading
import sys

from flask import Flask, request, render_template
from flask.helpers import jsonify
from flask.wrappers import Response
import requests

import similarity


# Config
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s:%(name)s:%(threadName)s: %(message)s")
logger = logging.getLogger(__name__)

try:
    import settings
except Exception, ex:
    raise Exception("settings could not be imported: %s" % ex)

app = Flask(__name__)
app.config.from_object(__name__)

CHANNEL_NAME = "refresh"  # hookbox channel


# App globals
similarity_score_matrix = OrderedDict()
cluster_data = defaultdict(dict, **{k: {"name": "top", "size": 10} for k in settings.CLUSTER_TYPES.iterkeys()})
dict_and_scores_lock = threading.RLock()
user_counter = 0
hookbook_process = None
new_submissions = Queue.Queue()
processed_submissions = Queue.Queue()


# Endpoints
@app.route('/')
def submit_text_form():
    return render_template('submit_text.html', hookbox_channel=CHANNEL_NAME, hookbox_ip=settings.SERVER_IP)


@app.route('/submit_text', methods=['POST'])
def submit_text():
    text = request.form.get('text', '').strip()
    if text:
        new_submissions.put(text)
    return Response('ok')


@app.route('/hookbox/', methods=['GET', 'POST'])
def connect():

    global user_counter
    response_data = None

    if request.method == 'POST':

        action = request.form.get('action')

        logger.debug("hookbox action: %s" % action)
        if action == 'connect':
            user_counter += 1
            response_data = [True, {'name': 'User%d' % user_counter}]

        elif action == 'subscribe':
            response_data = [True, {}]

        elif action == 'publish':
            response_data = [False, {}]

        elif action == 'poll':
            response_data = [False, {}]

        elif action == 'create_channel':
            response_data = [True, {}]

        elif action == 'destroy_channel':
            response_data = [True, {}]

        elif action == 'disconnect':
            response_data = [True, {}]

        else:
            logger.warning('got unknown hookbox action %s' % action)
            response_data = [False, {}]

    return Response(json.dumps(response_data))


@app.route('/visualize/')
def visualize():

    return render_template('visualize.html',
        hookbox_channel=CHANNEL_NAME,
        hookbox_ip=settings.SERVER_IP,
        server_address=settings.SERVER_IP,
    )


@app.route('/similarity_scores')
def similarity_scores():
    global similarity_score_matrix
    with dict_and_scores_lock:
        return Response(json.dumps(similarity_score_matrix))


@app.route('/cluster/<type>/')
def cluster(type):
    global cluster_data
    with dict_and_scores_lock:
        return jsonify(**cluster_data[type])


class DataRefresher(similarity.StoppableThread):
    """Pulls similarity scores off the queue and makes them available to the Flask app. Tells hookbox to tell
    clients to refresh when new data is available."""

    def __init__(self, processed_submissions, **kwargs):
        super(DataRefresher, self).__init__(**kwargs)
        self.processed_submissions = processed_submissions

    def run(self):
        global cluster_data, similarity_score_matrix

        while not self.stopped():
            try:
                work_done = self.processed_submissions.get(timeout=1)
            except Queue.Empty:
                continue

            with dict_and_scores_lock:

                for cluster_type in settings.CLUSTER_TYPES:
                    cluster_data[cluster_type] = work_done[cluster_type]

                documents = work_done["documents"]
                similarity_score_matrix = work_done["similarity_scores"]

                # tell hookbox clients to refresh
                params = {
                    # TODO This sends every calculated query to every client--fix this
                    "payload": json.dumps(work_done["documents"]),  # hookbox wants json in the query string
                    "channel_name": CHANNEL_NAME,
                    "security_token": settings.HOOKBOX_API_SECRET,
                }
                r = requests.get("http://%s:8001/web/publish" % settings.SERVER_IP, params=params)
                if r.status_code != 200:
                    logger.warning("got %d status code sending refresh message to hookbox" % r.status_code)

                self.processed_submissions.task_done()

        logger.info("exiting")


def cleanup():
    global hookbox_process, similarity_calculator, data_refresher

    if hookbox_process:
        hookbox_process.kill()

    if not similarity_calculator.stopped():
        similarity_calculator.stop()

    if not data_refresher.stopped():
        data_refresher.stop()

    similarity_calculator.join()
    data_refresher.join()


@atexit.register
def at_exit_cleanup():
    logger.debug("atexit")
    cleanup()


if __name__ == '__main__':

    # Start hookbox server
    import shlex
    args = shlex.split("hookbox --cb-single-url=http://%s:%s/hookbox/ -r %s --admin-password=%s"
    % (settings.HOST, settings.PORT, settings.HOOKBOX_API_SECRET, settings.HOOKBOX_ADMIN_PASSWORD))
    hookbox_process = subprocess.Popen(args)

    # Start calculator thread
    similarity_calculator = similarity.SimilarityCalculator(name="calculator", in_queue=new_submissions, out_queue=processed_submissions)
    similarity_calculator.start()

    # Start data refreshing thread
    data_refresher = DataRefresher(name="refresher", processed_submissions=processed_submissions)
    data_refresher.start()

    # Start flask app
    try:
        app.run(host=settings.HOST, port=settings.PORT)
    finally:
        cleanup()




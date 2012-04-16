import atexit
from collections import OrderedDict, defaultdict
import Queue
import logging
import threading
import sys

from flask import Flask, request, render_template, flash
from flask.helpers import jsonify

import workers

try:
    from settings import *
except Exception, ex:
    raise Exception("settings could not be imported: %s" % ex)

app = Flask(__name__)
app.config.from_object(__name__)


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(levelname)s:%(name)s:%(threadName)s: %(message)s'")
#logger = logging.getLogger(__name__)
logger = logging


# Globals
similarity_scores = OrderedDict()
cluster_data = defaultdict(dict)
dict_and_scores_lock = threading.RLock()

new_submissions = Queue.Queue()
processed_submissions = Queue.Queue()

@app.route('/')
def submit_text():
    if request.args.get('submit', ''):
        text = request.args.get('text', '').strip()
        new_submissions.put(text)
        flash("Submitted: '%s'" % text)
        return render_template('submit_text.html', last_submitted=text)

    else:
        return render_template('submit_text.html')

@app.route('/visualize/')
def visualize():
    global similarity_scores

    return render_template('visualize.html', computed_matches=similarity_scores)

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
                    similarity_scores = work_done["similarity_scores"]
                    for cluster_type in CLUSTER_TYPES:
                        cluster_data[cluster_type] = work_done[cluster_type]

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

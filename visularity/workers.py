#!/usr/bin/env python

import threading
import logging
import Queue
import pprint
import sys
from gensim import models, corpora, similarities

try:
    from settings import *
except Exception, ex:
    raise Exception("settings could not be imported: %s" % ex)


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Shared among all threads:
corpus, index = None, None
original_corpus = [
    "The bus drove along the highway, full of many people going from one city to another city that night.",
    "A whale can eat up to fifteen tons of plankton and other fish every day of its life.",
    "The distance to the nearest star is measured in light years, the distance light travels at its fantastic speed over an entire year.",
    "Planets are giant bodies of gas or rock out in the vacuum of space.",
    ]
corpus_index_lock = threading.RLock()


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class SimilarityCalculator(StoppableThread):
    """
    Adds new documents to the global corpus and index, and returns pairwise similarity index for the corpus.
    """

    def __init__(self, in_queue, out_queue=None, **kwargs):
        global corpus, index, original_corpus

        super(SimilarityCalculator, self).__init__(**kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue

        # These are invariant
        self.dictionary, self.tfidf_transformation, self.lsi_transformation = load_gensim_tools()

        # TODO These are going to be changed by adding documents--how to sync between threads?
        # For now, just have one SimilarityCalculator running at a time
        with corpus_index_lock:
            # Create the gensim.corpora.TextCorpus from the original sentences
            corpus = create_corpus(original_corpus, self.dictionary)
            # Create the index from the loaded tools and the TextCorpus
            index = create_index(corpus, self.tfidf_transformation, self.lsi_transformation)

    def run(self):
        global index, original_corpus

        while not self.stopped():

            try:
                doc = self.in_queue.get(timeout=1)
            except Queue.Empty:
                continue

            lsi_vec_doc = get_transformed_doc(doc, self.dictionary, self.tfidf_transformation, self.lsi_transformation)

            with corpus_index_lock:
                sims_to_doc = calc_sims_to_doc(index, lsi_vec_doc, original_corpus)

                add_doc_to_index(doc, index, lsi_vec_doc, original_corpus)

                sims = [s for s in index]
                results = {
                    "document": doc,
                    "similarity_scores": sims_to_doc
                }

                for cluster_type, cluster_func in CLUSTER_TYPES.iteritems():
                    results[cluster_type] = cluster_func(sims, original_corpus)

            if self.out_queue:
                self.out_queue.put(results)
                logger.info("%s put matches for '%s' on out_queue" % (threading.currentThread().name, doc))

            self.in_queue.task_done()

        logger.info("exiting")


def load_gensim_tools():

    dictionary = corpora.Dictionary.load_from_text(DICTIONARY_FILE)

    # TODO chain transformations
    tfidf_transformation = models.tfidfmodel.TfidfModel.load(TFIDF_MODEL_FILE)

    lsi_transformation = models.lsimodel.LsiModel.load(LSI_MODEL_FILE)

    return dictionary, tfidf_transformation, lsi_transformation


def create_corpus(docs, word2id):
    with corpus_index_lock:
        return corpora.TextCorpus(input=docs, word2id=word2id)


def create_index(corpus, tfidf_transformation, lsi_transformation):

    with corpus_index_lock:

        # Ensure a dir exists to store the shards
        index_dir = SHARD_DIR
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)

        # Create the index
        index = similarities.Similarity(index_dir + "/shard",
            corpus=lsi_transformation[tfidf_transformation[corpus]],
            num_features=400,  # TODO don't hard code this
        )

        return index


def get_transformed_doc(doc, dictionary, tfidf_transformation, lsi_transformation):
    # TODO chain transformation into a more flexible object that can set at runtime

    # Get sims of everything in the index compared to the new query
    tokenized_query = corpora.wikicorpus.tokenize(doc)
    bow_vec_doc = dictionary.doc2bow(tokenized_query)

    # Transform the new document and get the similarity scores of all the existing documents compared to it
    tfidf_vec_doc = tfidf_transformation[bow_vec_doc]
    lsi_vec_doc = lsi_transformation[tfidf_vec_doc]

    return lsi_vec_doc


def calc_sims_to_doc(index, lsi_vec_doc, original_corpus):
    # Calculate the similarities of the existing docs to the new one and sort
    sims_to_doc = index[lsi_vec_doc]
    sims_to_doc = zip(sims_to_doc, original_corpus)
    sims_to_doc = sorted(sims_to_doc, key=lambda sim: -sim[0])
    return sims_to_doc


def add_doc_to_index(doc, index, lsi_vec_doc, original_corpus):
    # Add the new query to the corpus and index, so now we can see how everything in the index compares to everything else,
    # allowing us to cluster like terms
    logger.info("%s adding to index '%s'" % (threading.currentThread().name, str(doc)))
    original_corpus.append(doc)
    index.add_documents([lsi_vec_doc])


if __name__ == "__main__":
    dictionary, tfidf_transformation, lsi_transformation = load_gensim_tools()
    corpus = create_corpus(original_corpus, dictionary)
    index = create_index(corpus, tfidf_transformation, lsi_transformation)
    while True:
        doc = raw_input("> ")

        lsi_vec_doc = get_transformed_doc(doc, dictionary, tfidf_transformation, lsi_transformation)

        sims_to_doc = calc_sims_to_doc(index, lsi_vec_doc, original_corpus)

        add_doc_to_index(doc, index, lsi_vec_doc, original_corpus)

        sims = [s for s in index]

        dcluster_dict = simcluster.sims_to_dendrogram(sims, original_corpus)
        pprint.pprint(dcluster_dict)

        hcluster_dict = simcluster.sims_to_hcluster(sims, original_corpus)
        pprint.pprint(hcluster_dict)

        apcluster_dict = simcluster.sims_to_apcluster(sims, original_corpus)
        pprint.pprint(apcluster_dict)
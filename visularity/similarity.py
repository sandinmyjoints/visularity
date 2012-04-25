#!/usr/bin/env python
import os

import threading
import logging
import Queue
import pprint
import sys
from gensim import models, corpora, similarities
from cluster import simcluster

try:
    import settings
except Exception, ex:
    raise Exception("settings could not be imported: %s" % ex)


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s:%(name)s:%(threadName)s: %(message)s")
logger = logging.getLogger(__name__)


# Shared among all worker threads:
corpus, index = None, None
try:
    original_corpus = settings.SEED_CORPUS
    _ = settings.SEED_CORPUS[0]
except IndexError:
    original_corpus = []
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

            # Get data from the queue, breaking every second so we can check if we've stopped
            try:
                docs = [self.in_queue.get(timeout=1)]
            except Queue.Empty:
                continue

            # Once there's data on the queue, pull out as much as we can get because it's faster to work in batches
            try:
                while True:
                    docs.append(self.in_queue.get_nowait())
            except Queue.Empty:
                pass

            doc_pairs = [(doc, get_transformed_doc(doc, self.dictionary, self.tfidf_transformation, self.lsi_transformation)) for doc in docs]

            with corpus_index_lock:

                add_docs_to_index(doc_pairs, index, original_corpus)
                similarity_scores = [[''] + [doc for doc in original_corpus]]

                sims = [s for s in index]
                similarity_scores.extend([[round(score, 3) for score in sim_arr] for sim_arr in sims])
                for i, doc in enumerate(original_corpus):
                    similarity_scores[i+1].insert(0, doc)

                results = {
                    "documents": docs,
                    "similarity_scores": similarity_scores
                }

                for cluster_type, cluster_func in settings.CLUSTER_TYPES.iteritems():
                    results[cluster_type] = cluster_func(sims, original_corpus)

                if self.out_queue:
                    self.out_queue.put(results)
                    logger.debug("%s put matches for '%s' on out_queue" % (threading.currentThread().name, docs))

            for i in range(0, len(docs)):
                self.in_queue.task_done()

        logger.info("exiting")


def load_gensim_tools():
    """Load serialized objects."""

    dictionary = corpora.Dictionary.load_from_text(settings.DICTIONARY_FILE)

    # TODO chain transformations
    tfidf_transformation = models.tfidfmodel.TfidfModel.load(settings.TFIDF_MODEL_FILE)

    lsi_transformation = models.lsimodel.LsiModel.load(settings.LSI_MODEL_FILE)

    return dictionary, tfidf_transformation, lsi_transformation


def create_corpus(docs, word2id):
    with corpus_index_lock:
        return corpora.TextCorpus(input=docs, word2id=word2id)


def create_index(corpus, tfidf_transformation, lsi_transformation):
    """Create an index given a corpus and transformation(s).
        :param corpus: The index corpus (documents against which new unseen documents will be compared)
        :param tfidf_transformation: A vector space transformation model
        :param lsi_transformation: A vector space transformation model
        """

    with corpus_index_lock:

        # Ensure a dir exists to store the shards
        index_dir = settings.SHARD_DIR
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)

        # Create the index
        index = similarities.Similarity(index_dir + "/shard",
            corpus=lsi_transformation[tfidf_transformation[corpus]],
            num_features=400,  # TODO don't hard code this
        )

        return index


def get_transformed_doc(doc, dictionary, tfidf_transformation, lsi_transformation):
    """Transform a document from plain language to a vector space.
        TODO chain transformation into a more flexible object that can set at runtime

        :param doc: The untokenized, plain-language document string to be transformed
        :param dictionary: The word-to-id mapping used by the corpus that the transformation models were generated from
        :param tfidf_transformation: A vector space transformation model
        :param lsi_transformation: A vector space transformation model
        """

    tokenized_query = corpora.wikicorpus.tokenize(doc)
    bow_vec_doc = dictionary.doc2bow(tokenized_query)

    tfidf_vec_doc = tfidf_transformation[bow_vec_doc]
    lsi_vec_doc = lsi_transformation[tfidf_vec_doc]

    return lsi_vec_doc


def calc_sims_to_doc(index, transformed_doc, index_corpus):
    """
        Calculate the similarities of the existing docs to a new document, sort, and pair with original text documents.

        :param index: The index against which to calculate similarity scores
        :param transformed_doc: The document vector transformed to the same vector space as the index
        :param index_corpus: The plain language documents so that similarity matches can be paired with their text
        """
    sims_to_doc = index[transformed_doc]
    sims_to_doc = zip(sims_to_doc, index_corpus)
    sims_to_doc = sorted(sims_to_doc, key=lambda sim: -sim[0])
    return sims_to_doc


def add_docs_to_index(docs, index, index_corpus):
    """Add the new query to the corpus and index, so now we can see how everything in the index compares to everything else,
    allowing us to cluster like terms.

    :param docs: iterable of (doc, transformed_doc) tuples
    :param index: the index to add the transformed documents to
    :param index_corpus: the English language corpus to add the untransformed doc to
    """

    docs, transformed_docs = zip(*docs)
    logger.info("%s adding to index '%s'" % (threading.currentThread().name, docs))
    index_corpus.extend(docs)
    index.add_documents(transformed_docs)


if __name__ == "__main__":
    dictionary, tfidf_transformation, lsi_transformation = load_gensim_tools()
    corpus = create_corpus(original_corpus, dictionary)
    index = create_index(corpus, tfidf_transformation, lsi_transformation)

    while True:
        doc = raw_input("> ")

        lsi_vec_doc = get_transformed_doc(doc, dictionary, tfidf_transformation, lsi_transformation)

        sims_to_doc = calc_sims_to_doc(index, lsi_vec_doc, original_corpus)

        add_docs_to_index(((doc, lsi_vec_doc),), index, original_corpus)

        sims = [s for s in index]
        print "similarity matrix:"
        pprint.pprint(sims)

        print "dendrogram cluster:"
        dcluster_dict = simcluster.sims_to_dendrogram(sims, original_corpus)
        pprint.pprint(dcluster_dict)

        print "hierarchical cluster:"
        hcluster_dict = simcluster.sims_to_hcluster(sims, original_corpus)
        pprint.pprint(hcluster_dict)

        print "affinity propagation cluster:"
        apcluster_dict = simcluster.sims_to_apcluster(sims, original_corpus)
        pprint.pprint(apcluster_dict)
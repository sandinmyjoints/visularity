import os

from visularity.cluster import simcluster


# Flask settings
DEBUG = True
SECRET_KEY = "yoursecretkeyhere"

# Hookbox settings
CHANNEL_NAME = "refresh"
API_SECRET = "secret"

# Visularity settings
SERVER_ADDRESS = "127.0.0.1:5000"
PROJECT_ROOT = os.path.dirname(__file__)
GENSIM_DATA_ROOT = "/home/wbert/gensimdata/"
VIS_DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

LSI_MODEL_FILE = os.path.join(GENSIM_DATA_ROOT, "wiki_en_model.lsi")
TFIDF_MODEL_FILE = os.path.join(GENSIM_DATA_ROOT, "wiki_en_tfidf.model")
DICTIONARY_FILE = os.path.join(GENSIM_DATA_ROOT, "wiki_en_wordids.txt")
SHARD_DIR = os.path.join('/tmp', "index_shards")


CLUSTER_TYPES = {
    "hcluster": simcluster.sims_to_hcluster,
    "apcluster": simcluster.sims_to_apcluster,
    "dcluster": simcluster.sims_to_dendrogram,
}

try:
    from local_settings import *
except:
    pass
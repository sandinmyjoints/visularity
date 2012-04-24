import os

from cluster import simcluster


# Flask settings
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True
SECRET_KEY = "yoursecretkeyhere"

# Hookbox settings
HOOKBOX_API_SECRET = "secret"
HOOKBOX_ADMIN_PASSWORD = "admin"

# Visularity settings
SERVER_IP = "192.168.1.102"  # Need to set this to whatever IP your machine is using
SERVER_ADDRESS = "%s:%d" % (SERVER_IP, PORT)
PROJECT_ROOT = os.path.dirname(__file__)

GENSIM_DATA_ROOT = "/home/wbert/gensimdata/"
VIS_DATA_ROOT = os.path.join(PROJECT_ROOT, "data")
SEED_CORPUS = [
    "The bus drove along the highway, full of many people going from one city to another city that night.",
    "A whale can eat up to fifteen tons of plankton and other fish every day of its life.",
    "The distance to the nearest star is measured in light years, the distance light travels at its fantastic speed over an entire year.",
    "Planets are giant bodies of gas or rock out in the vacuum of space.",
    ]

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
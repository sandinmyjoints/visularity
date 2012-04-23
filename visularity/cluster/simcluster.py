#!/usr/bin/env python
from collections import defaultdict
import json
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster, ward
from sklearn.cluster.affinity_propagation_ import affinity_propagation


def linkage_to_d3(Z, origin_corpus=None):
    """
            Convert linkage array arr into a dictionary suitable for dumping to json for d3
        Z has n-1 elements, so n is len(Z)+1, and there are 2*n-1 clusters, the highest index of  which is 2*n-2.

    """
    if not len(Z):
        return {}

    n = len(Z)+1
    return _make_cluster(Z, 2*n-2, origin_corpus=origin_corpus)


def _make_cluster(Z, index, origin_corpus=None):
    """
        Recurse through arr to generate a dictionary representation of cluster index.
        n is len(Z)+1, and we want to start with the container cluster as the index, which is len(Z)+n-1, so first call like this:
        d3_dict = _do_linkage_to_d3(len(Z)+1, 2 * len(Z), Z)

        :param Z: invariant; is an array produced by linkage()
        :param index: this cluster's index, like the name of the cluster
        :param origin_corpus: The original data points, to be added to the cluster names if available
    """
    n = len(Z) + 1
    index = int(index)
    assert 0 <= index < (n*2)  # one less cluster than double the number of observations

    c = { "name": "cluster" + str(index) }
    if origin_corpus:
        try:
            datum = origin_corpus[index]
            c.update({ "name": ": ".join([c["name"], str(datum)])})
        except IndexError, ex:
            pass

    if index < n:
        # base case: if index < n, this is an original observation, corresponding to original_observations[index]
        c.update({"size": 10})
    else:
        pos = index - n
        assert 0 <= pos < len(Z)
        cluster_a_index, cluster_b_index, distance, size = Z[pos]
        # otherwise, need to get children
        c.update({
            "children": [
                _make_cluster(Z, cluster_a_index, origin_corpus),  # could call with a slice of Z, and pass n as invariant
                _make_cluster(Z, cluster_b_index, origin_corpus),
                ]
        })

    return c


def hcluster_to_d3(arr, origin_corpus=None):
    d3_dict = {"name": "top", "children": []}
    for observation, clusterno in enumerate(arr):
        clusterno = str(clusterno)
        # if a dict for clusterno is in children, use it, else create one
        cluster = defaultdict(list)
        found = False
        for d in d3_dict["children"]:
            if d["name"] == "cluster" + str(clusterno):
                cluster = d
                found = True
                break

        if not cluster:
            cluster["name"] = "cluster" + clusterno

        cluster["children"].append({
            "name": origin_corpus[observation] if origin_corpus else "observation" + str(observation),
            "size": 10}
        )

        if not found:
            d3_dict["children"].append(cluster)

    return d3_dict


def sims_to_linkage(sim_scores):
    return linkage(sim_scores)


def sims_to_wards(sim_scores):
    return ward(sim_scores)


def sims_to_dendrogram(sim_scores, origin_corpus=None):
    Z = sims_to_linkage(sim_scores)
    return linkage_to_d3(Z, origin_corpus=origin_corpus)


def sims_to_hcluster(sim_scores, origin_corpus=None):
    Z = sims_to_linkage(sim_scores)
    cluster = fcluster(Z, t=0.5)
    return hcluster_to_d3(cluster, origin_corpus=origin_corpus)


def sims_to_apcluster(sim_scores, origin_corpus=None):
    cluster_centers_indices, labels = affinity_propagation(sim_scores)

    ap_cluster_dict = {}
    ap_cluster_dict["name"] = "top"
    ap_cluster_dict["children"] = []

    for i, label in enumerate(labels):
        label = str(label)
        found = False
        for c in ap_cluster_dict["children"]:  # use itemgetter?
            if c["name"] == ("cluster" + label):
                cluster = c
                found = True
                break

        if not found:
            cluster = {}
            ap_cluster_dict["children"].append(cluster)

        if not cluster.has_key("name"):
            cluster["name"] = "cluster" + label

        if not cluster.has_key("children"):
            cluster["children"] = []

        cluster["children"].append({"name": origin_corpus[i], "size": 10})

    return ap_cluster_dict

def plot(sim_scores):
    # Just for now
    import matplotlib
    Z = linkage(sim_scores)

    dendrogram(Z)
    matplotlib.pylab.show()


def serialize_cluster(cluster, fname):
    with open(fname, "w+") as output:
        json.dump(cluster, output)


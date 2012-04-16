from numpy.core.numeric import array
from visularity.cluster.simcluster import linkage_to_d3

__author__ = 'wbert'

import unittest


class LinkageToD3Test(unittest.TestCase):

    def test_linkage_to_d3_0_observations(self):
        Z = array([])
        expected = {}
        d3_dict = linkage_to_d3(Z)
        self.assertDictEqual(expected, d3_dict)

    def test_linkage_to_d3_2_observations(self):
        Z = array([[ 0.        ,  1.        ,  0.45015331,  2.        ]])   # arr[0], cluster2

        expected = {
            "name": "cluster2",
            "children": [
                {
                    "name": "cluster0",
                    "size": 10
                },
                {
                    "name": "cluster1",
                    "size": 10
                }
            ]
        }

        d3_dict = linkage_to_d3(Z)
        self.assertDictEqual(expected, d3_dict)

    def test_linkage_to_d3_3_observations(self):
        Z = array([[ 1.        ,  2.        ,  0.45015331,  2.        ],   # arr[0], cluster3
            [ 0.        ,  3.        ,  1.29504919,  2.        ],   # arr[1], cluster4
            ])

        expected = {
            "name": "cluster4",
            "children": [
                { "name": "cluster0", "size": 10 },
                {
                    "name": "cluster3",
                    "children": [
                        { "name": "cluster1", "size": 10 },
                        { "name": "cluster2", "size": 10 },
                    ]
                },
            ]
        }

        d3_dict = linkage_to_d3(Z)
        self.assertDictEqual(expected, d3_dict)

    def test_linkage_to_d3_4_observations(self):
        Z = array([[ 1.        ,  3.        ,  0.45015331,  2.        ],   # arr[0], cluster4
            [ 0.        ,  2.        ,  1.29504919,  2.        ],   # arr[1], cluster5
            [ 4.        ,  5.        ,  1.55180264,  4.        ]])  # arr[2], cluster6

        expected = {
            "name": "cluster6",
            "children": [
                    {
                    "name": "cluster4",
                    "children": [
                            {"name": "cluster1", "size": 10},
                            {"name": "cluster3", "size": 10},
                    ]
                },
                {
                "name": "cluster5",
                "children": [
                        {"name": "cluster0", "size": 10},
                        {"name": "cluster2", "size": 10},
                ],
                },
            ]
        }

#        n = len(Z)+1
#        d3_dict = _do_linkage_to_d3(n, len(Z)+n-1, Z)
        d3_dict = linkage_to_d3(Z)
        self.assertDictEqual(expected, d3_dict)

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
@author: huangjunjie
@file: signlens_model.py
@time: 2021/01/02
"""
import os
import re
import sys
import time
import json
import math
import random
import pickle
import logging
import argparse
import subprocess

from collections import defaultdict

import pandas as pd
import networkx as nx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dirpath', default=BASE_DIR, help='Current Directory')
    parser.add_argument('--debug', default=True, type=bool, help='Current Directory')

    args = parser.parse_args()


class SignLens(object):
    def __init__(self, edgelist_fpath, edgeinfo_fpath, nodeinfo_fpath):
        self.tsv_header = None
        self.edgelist_fpath = edgelist_fpath
        self.edgeinfo_fpath = edgeinfo_fpath
        self.nodeinfo_fpath = nodeinfo_fpath

        self.edge_df = pd.read_csv(self.edgelist_fpath)

        self.edgelist = self.read_edgelist_from_file()
        self.nodeinfo = self.read_nodeifno_from_file()
        self.edgeinfo = self.read_edgeinfo_from_file()

        self.G = self.generate_networkx_object(self.edgelist)

    def read_edgelist_from_file(self):
        edgelist = defaultdict(lambda: defaultdict(int))
        num = 0
        with open(self.edgelist_fpath) as f:
            for ind, line in enumerate(f):
                line = line.strip()
                if ind == 0:
                    # start with alpha
                    self.tsv_header = line.split('\t')
                    continue
                ll = line.split('\t')
                a, b, s = map(int, ll[: 3]) # first 3
                num += 1
                if s >= 0:
                    edgelist[a][b] += 1
                    edgelist[b][a] += 1
                else:
                    edgelist[a][b] += -1
                    edgelist[b][a] += -1
        print('NUM', num, 69)
        return edgelist
    
    def generate_networkx_object(self, edgelist):
        G = nx.Graph()
        num = 0
        for i in edgelist:
            for j in edgelist[i]:
                v = edgelist[i][j]
                num += 1
                G.add_edge(i, j, weight=v)
        print('num', num)
        return G

    def read_edgeinfo_from_file(self):
        edgeinfo_dict = {}
        with open(self.edgeinfo_fpath) as f:
            for ind, l in enumerate(f):
                if ind == 0: 
                    continue
                note_id, _, info = l.strip().partition('\t')
                edgeinfo_dict[note_id] = json.loads(info)
        return edgeinfo_dict

    def read_nodeifno_from_file(self):
        nodeinfo_dict = {}
        with open(self.nodeinfo_fpath) as f:
            for ind, l in enumerate(f):
                if ind == 0:
                    continue
                note_id, _, info = l.strip().partition('\t')
                nodeinfo_dict[note_id] = json.loads(info)
        return nodeinfo_dict

    def get_pos_top(self, k):
        pass

    def get_neg_top(self, k):
        pass
    
    def get_subgraph(self, node_list=[], depth=0):
        pass

    def get_infos(self):
        res = {
            'node_num': len(self.nodeinfo),
            'node_num_in_graph': self.G.number_of_nodes(),
        }
        self.print_a_json(res)

    def print_a_json(self, json_data):
        for k, v in json_data.items():
            print(k, v)


def main():
    cbdb_edgelist_fpath = os.path.join(BASE_DIR, 'datas', 'cbdb_edgelist.tsv')
    cbdb_edgeinfo_fpath = os.path.join(BASE_DIR, 'datas', 'cbdb_edgeinfo.tsv')
    cbdb_nodeinfo_fpath = os.path.join(BASE_DIR, 'datas', 'cbdb_nodeinfo.tsv')
    model = SignLens(edgelist_fpath=cbdb_edgelist_fpath, edgeinfo_fpath=cbdb_edgeinfo_fpath, nodeinfo_fpath=cbdb_nodeinfo_fpath)
    model.get_infos()

if __name__ == "__main__":
    main()


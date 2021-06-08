#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
@author: huangjunjie
@file: utils.py
@time: 2021/01/02
"""
import os
from collections import defaultdict

import networkx as nx
from networkx.readwrite import json_graph


def get_subgraph(g, query_nodes = ['1762'], depth = 3):
    # 
    print(g)
    g_edges = g.edges()
    g_edges_dict = defaultdict(set)
    for edge in g_edges:
        n1 = edge[0]
        n2 = edge[1]
        g_edges_dict[n1].add(n2)
        g_edges_dict[n2].add(n1)
    # print(len(g_edges_dict['1762']))
    subgraph_nodes = set(query_nodes)
    now_nlists = list(query_nodes)
    k = depth
    while k:
        k -= 1
        next_nlists = []
        for node in now_nlists:
            for n in g_edges_dict[node]:
                if n not in subgraph_nodes:
                    next_nlists.append(n)

        next_nlists = list(set(next_nlists))
        print(len(next_nlists))
        tmp = list(subgraph_nodes)
        tmp.extend(next_nlists)
        subgraph_nodes = set(tmp)
        now_nlists = next_nlists
    print(len(subgraph_nodes))
    sub_g = g.subgraph(subgraph_nodes)
    print(44, subgraph_nodes, g, sub_g)
    return sub_g


def naive_plot(g, query_nodes):
    '''
    1384, 歐陽修 22
    3762,蘇洵 2
    1493,蘇轍 13
    3767,蘇軾 2
    1762,王安石 6
    7364,曾鞏 0    
    '''
        
    sub_g = get_subgraph(g=g, query_nodes=query_nodes, depth=0)

    pos = nx.circular_layout(sub_g)
    # 为了保证画出来顺序是确定的，
    # print(pos.items())
    values = sorted(pos.items(), key = lambda x:x[1][1]/x[1][0], reverse=True)

    nodes = {i[0]: {'position': list(i[1])} for i in values}
    pos_key = [i for i in pos.keys()]
    pos_key.sort()
    
    for index, i in enumerate(pos_key):
        pos[i] = values[index][1]

    d = json_graph.node_link_data(sub_g) # node-link format to serialize
    print(d)
    # print(pos_values)
    return d, nodes

def get_directed_links(df):
    edge_lists_v = defaultdict(int)
    for i, j, v in df[['PersonIdA', 'PersonIdB', 'Sign']].values.tolist():
        edge_lists_v[(str(i),str(j))] += v
    tmp_g = nx.Graph()
    for (i, j), v in edge_lists_v.items():
        tmp_g.add_edge(i,j, weight=v)
    tmp = json_graph.node_link_data(tmp_g)
    return tmp['links']
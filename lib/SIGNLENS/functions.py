#!/usr/bin/env python
# -*- coding=utf-8 -*-

import re
import os
import json
import heapq
import math
from collections import defaultdict

import networkx as nx
from networkx.readwrite import json_graph
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import igraph as ig
import pandas as pd
import louvain
from louvain import Optimiser

# from googletrans import Translator

CENTRALITY_DIR = 'centrality'
VIS_DATA_DIR = './csv'

def check_contain_chinese(text):
    """check if need to translated
    
    Arguments:
        text {string} -- string to be detected
    
    Returns:
        Boolean -- whether or not contain chinese
    """
    if not text.strip(): return False
    return not all('0' <= char <= '9' for char in text)

# def translate_json(input_data):
#     """using google trans api to translate datas
    
#     Arguments:
#         input_data {[json, str]}
    
#     Returns:
#         input_data_translated 
#     """
#     if isinstance(input_data, list):
#         datas = []
#         for item in input_data:
#             datas.append(translate_json(item))
#         return datas
#     elif isinstance(input_data, dict):
#         data = dict()
#         for item in input_data:
#             data[item] = translate_json(input_data[item])
#         return data
#     elif isinstance(input_data, str) and check_contain_chinese(input_data):
#         trans = Translator(service_urls = ['translate.google.cn'])
#         trans_str = trans.translate(input_data, dest='en').text
#         print(input_data, trans_str)
#         return trans_str
#     else:
#         return input_data


def get_topPeople(dynasty = 'song', topk = 10, sort_by = 0):
    """get Topk central figures
    
    Keyword Arguments:
        dynasty {str} -- dyansty name (default: {'song'})
        topk {int} -- topk (default: {10})
        sort_by {int} -- sorted by which centrality (default: {0})
        degree_centrality, betweenness_centrality,closeness_centrality,eigenvector_centrality
    Returns:
        [type] -- topk results
    """
    json_file_path = os.path.join(CENTRALITY_DIR, '{}_centrality.json'.format(dynasty))
    with open(json_file_path) as f:
        json_data = json.load(f)
        top_degree = []
        for people in json_data:
            heapq.heappush(top_degree, (json_data[people][sort_by], json_data[people], people))
        res =  heapq.nlargest(topk, top_degree)
        return [i[1] for i in res]


def get_subgraph(node_list = ['1762'], depth = 3, graph_path='song-signed.gexf'):
    '''
    node-list 是起点节点，
    depth是深度
    '''
    gexf_path = os.path.join(VIS_DATA_DIR, graph_path)
    g = nx.read_gexf(gexf_path)
    # 
    g_edges = g.edges()
    g_edges_dict = defaultdict(set)
    for edge in g_edges:
        n1 = edge[0]
        n2 = edge[1]
        g_edges_dict[n1].add(n2)
        g_edges_dict[n2].add(n1)
    # print(len(g_edges_dict['1762']))
    subgraph_nodes = set(node_list)
    now_nlists = list(node_list)
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
            # 获取这个节点的所有连接节点
    print(len(subgraph_nodes))
    sub_g = g.subgraph(subgraph_nodes)
    return sub_g


def get_property(sub_g) :
    fname = os.path.join(VIS_DATA_DIR, 'song.csv')
    people_df = pd.read_csv(fname)
    attrs = dict()
    centrality_attrs = dict()

    with open('./centrality/song_centrality.json') as f:
        json_data = json.load(f)
    
    for n in sub_g.nodes():
        p = people_df[people_df.nid == int(n)]
        name1 = p['ChName']
        name2 = p['EngName']
        attrs[n]= "".join(name1.values)

        d = dict()
        d["EngName"] = "".join(name2.values)
        d["ChName"] = "".join(name1.values)
        d["PersonID"] = n
        pku = json_data[n]
        d["c1"] = round(pku[0], 3)
        d["c2"] = round(pku[1], 3)
        d["c3"] = round(pku[2], 3)
        d["c4"] = round(pku[3], 3)
        centrality_attrs[n] = d
    return attrs, centrality_attrs


def naive_plot(node_list, cate="1"):
    '''
    1384, 歐陽修 22
    3762,蘇洵 2
    1493,蘇轍 13
    3767,蘇軾 2
    1762,王安石 6
    7364,曾鞏 0    
    '''
        
    graph_path_dict = {
        '1': 'song-pos.gexf',
        '2': 'song-neg.gexf',
        '3': 'song-signed.gexf'
    }
    graph_path = graph_path_dict[cate]
    sub_g = get_subgraph(node_list=node_list, depth=0, graph_path=graph_path)
    attrs , centrality_attrs = get_property(sub_g)
    e_pos = [(u, v) for (u, v, d) in sub_g.edges(data=True) if d['weight'] > 0]
    e_neg = [(u, v) for (u, v, d) in sub_g.edges(data=True) if d['weight'] < 0]
    pos = nx.circular_layout(sub_g)
    # 为了保证画出来顺序是确定的，
    # print(pos.items())
    values = sorted(pos.items(), key = lambda x:x[1][1]/x[1][0], reverse=True)

    nodes = {i[0]: {'position': list(i[1]), 'name': attrs[i[0]], 'centrality': centrality_attrs[i[0]]} for i in values}
    pos_key = [i for i in pos.keys()]
    pos_key.sort()
    
    for index, i in enumerate(pos_key):
        pos[i] = values[index][1]

    for n in sub_g:
        sub_g.node[n]['name'] = n
    d = json_graph.node_link_data(sub_g) # node-link format to serialize
    # print(d)
    # print(pos_values)
    return d, nodes


def layer_partition(sub_g):
    
    graphml_path = os.path.join(VIS_DATA_DIR, 'song-tmp.graphml')
    nx.write_graphml(sub_g, graphml_path)
    G = ig.Graph.Read_GraphML(graphml_path)
    G_pos = G.subgraph_edges(G.es.select(weight_gt = 0), delete_vertices=False)
    G_neg = G.subgraph_edges(G.es.select(weight_lt = 0), delete_vertices=False)
    G_neg.es['weight'] = [-w for w in G_neg.es['weight']]
    part_pos = louvain.ModularityVertexPartition(G_pos, weights='weight')
    part_neg = louvain.ModularityVertexPartition(G_neg, weights='weight')
    optimiser = louvain.Optimiser()
    part_pos = louvain.ModularityVertexPartition(G_pos, weights='weight')
    part_neg = louvain.ModularityVertexPartition(G_neg, weights='weight')
    diff = optimiser.optimise_partition_multiplex([part_pos, part_neg],layer_weights=[1,-1])
    # while diff > 0:
    #     diff = optimiser.optimise_partition_multiplex([part_pos, part_neg],layer_weights=[1,-1])
    # print(diff)
    # print(part_neg)
    # print(part_pos)
    # for v in G.vs:
    #     print(v.index, v["label"])
    # print(dir(part_pos), part_pos.membership)
    # print(dir(part_pos))
    # print(part_pos.summary())
    # print(part_pos.modularity, part_pos.q, part_pos)
    
    node_partition = {}
    for v in G.vs:
        node_partition[v["label"]] = v.index
    node_partition2 = {}
    memberships = [i for i in part_pos.membership]
    assert len(memberships) == len(node_partition)
    for i in node_partition:
        node_partition2[i] = memberships[node_partition[i]]
        
    return node_partition2
    

def generate_group_results(node_list = ['1384', '3762', '1493', '3767', '1762', '7364'], depth = 0):
    print(node_list, depth)
    sub_g = get_subgraph(node_list, depth)
    # 得倒聚类结果，然后挑选每个组里前depth * 5
    results = layer_partition(sub_g)
    attrs , centrality_attrs = get_property(sub_g)
    groups = defaultdict(list)
    for i in results:
        groups[results[i]].append(i)
    allow_groups = set([results[i] for i in node_list])
    res_groups = defaultdict(list)
    for group in groups:
        if group in allow_groups:
            group_i = groups[group]
            some_group_people = set()
            group_i_sorted = sorted(group_i, key=lambda x:centrality_attrs[x]['c1'], reverse=True)
            # 
            for node in node_list:
                if node in group_i:
                    some_group_people.add(node)

            for node in group_i_sorted[:5*(depth+1)]:
                some_group_people.add(node)
            res_groups[group] = list(some_group_people)
    print(allow_groups, len(res_groups))

    all_nodes = [] 
    for group in res_groups:
        for node in res_groups[group]:
            tmp =  {
                "group": group,
                "id": node,
                "label": node,
                "name": centrality_attrs[node]["ChName"],
                "data": centrality_attrs[node]
            }
            all_nodes.append(tmp)
    all_node_list = [i["id"] for i in all_nodes]
    res_sub_g = get_subgraph(all_node_list, depth = 0)
    result_json = json_graph.node_link_data(res_sub_g)
    for link in result_json["links"]:
        print(link)
        link['value'] = link['weight']
    result_json["nodes"] = all_nodes
    return result_json

def generate_direct_results(node_list):
    links1, nodes1 = naive_plot(node_list)
    links2, nodes2 = naive_plot(node_list, cate='2')
    links3, nodes3 = naive_plot(node_list, cate='3')
    if (json.dumps(nodes1) != json.dumps(nodes2)):
        print('sth not good!')
    return links1['links'], links2['links'], links3['links'], nodes1

def compute(node_list, depth=0):
    result_json = generate_group_results(node_list, depth)
    links1, links2, links3, nodes = generate_direct_results(node_list)
    datas = {}
    datas["links1"] =  links1
    datas["links2"] =  links2
    datas["links3"] =  links3
    datas["nodes"] =  nodes
    datas["link_datas"] = result_json
    return datas

def main():
    node_list = ['1384', '3762', '1493', '3767', '1762', '7364']
    # result = compute(node_list, 0)
    links1, links2, links3, nodes1 = generate_direct_results(node_list)
    # print(result)
    print(links1)

if __name__ == '__main__':
    main()
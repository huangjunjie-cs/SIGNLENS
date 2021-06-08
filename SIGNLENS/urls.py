"""SIGNLENS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

import json
import pandas as pd
import networkx as nx
from networkx.readwrite import json_graph

from django.contrib import admin
from django.urls import path
from collections import defaultdict
from ninja import NinjaAPI, Schema

api = NinjaAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))



node_fpath = os.path.join(BASE_DIR, '../datas/cbdb_nodeinfo.tsv')
node_df = pd.read_csv(node_fpath, sep='\t')
eng_dict = {}
for ind, id, info in node_df.to_records():
    info = json.loads(info)
    eng_name = info['EngName']
    eng_dict[eng_name] = id
eng_list = list(eng_dict.keys())
node_df['name'] = node_df['Info'].apply(lambda x:json.loads(x)['EngName'])

edge_fpath = os.path.join(BASE_DIR, '../datas/cbdb_edgelist.tsv')
edge_df = pd.read_csv(edge_fpath, sep='\t')
edge_lists = edge_df[['PersonIdA', 'PersonIdB']].astype(str).values.tolist()
G = nx.Graph()
G.add_edges_from(edge_lists)

def map_df_to_json(records):
    res = []
    for i in records.to_records():
        t = {}
        t['label'] = json.loads(i['Info'])['EngName']
        t['value'] = str(i["PersonId"])
        res.append(t)
    return res

@api.get("/getNodeList")
def add(request, query: str=''):
    if query:
        records = node_df[node_df['name'].str.contains(query, na=False)].sort_values('PersonId')
    else:
        query_nodes = [1384, 1493, 1762, 3762, 3767, 7364]
        records = node_df[node_df['PersonId'].isin(query_nodes)]
    nodes = map_df_to_json(records)
    return {"results": nodes}

class IndividualQueryItem(Schema):
    algorithms: int = 1
    depth: int = 0
    nodes: list

def get_node_degree_info(nodes):
    cen_res = {}
    for node in nodes:
        df2 = edge_df[(edge_df['PersonIdA'] == node) | (edge_df['PersonIdB'] == node )]
        deg_pos = len(df2[df2['Sign'] >= 0])
        deg_neg = len(df2[df2['Sign'] < 0])
        deg = len(df2)
        cen_res[node] = {
            deg_pos:deg_pos,
            deg_neg:deg_neg,
            deg:deg,
        }
    return cen_res


from .utils import naive_plot, get_subgraph, get_directed_links


@api.post("/getIndividualAnalysis")
def getIndividualAnalysis(request, item: IndividualQueryItem):
    print(item)
    print(item.nodes)
    # query nodes
    query_nodes = [i['value'] for i in item.nodes]
    depth = item.depth
    print(len(G))

    sub_g = get_subgraph(g=G, query_nodes=query_nodes, depth=depth)
    print(len(sub_g), 99)
    # subgraph nodes
    nodes_list = set(sub_g.nodes)
    

    # 
    print(nodes_list)
    df1 = edge_df[(edge_df['PersonIdA'].astype(str).isin(nodes_list) & edge_df['PersonIdB'].astype(str).isin(nodes_list) )]
    pos_tie_num = len(df1[df1['Sign'] >= 0])
    neg_tie_num = len(df1[df1['Sign'] < 0])
    subgraph_info = {
        "pos_tie_num": pos_tie_num,
        "neg_tie_num": neg_tie_num,
        "tie_num": len(df1)
    }

    links1 = get_directed_links(df1[df1['Sign'] > 0])
    links2 = get_directed_links(df1[df1['Sign'] < 0])
    links3 = get_directed_links(df1)
    res = {
        'subgraph_info':subgraph_info,
        'links1': links1,
        'links2': links2,
        'links3': links3,
    }
    print(res, 128)
    d, nodes = naive_plot(G, query_nodes)
    print(nodes)
    return res






# urlpatterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
]

#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
@author: huangjunjie
@file: function.py
@time: 2020/12/11
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
from tqdm import tqdm
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--dirpath', default=BASE_DIR, help='current dir')
args = parser.parse_args()


def statistic_relation():
    relations = set()
    relations_codes = set()
    relations_c = defaultdict(int)
    error = 0
    edge_list = []
    with open('datas/all_data.jl') as f:
        for line in tqdm(f):
            try:
                json_data = json.loads(line)
                if 'Person' not in json_data['Package']['PersonAuthority']['PersonInfo']:
                    continue
                person_data = json_data['Package']['PersonAuthority']['PersonInfo']['Person']
                basic_info_person = person_data['BasicInfo']
                if 'PersonSocialAssociation' in person_data:
                    person_association = person_data["PersonSocialAssociation"]
                    if 'Association' in person_association:
                        person_assoc = person_association['Association']
                        if isinstance(person_assoc, list):
                            for person in person_association['Association']:
                                if 'AssocName' in person and 'AssocCode' in person:
                                    relations.add(person['AssocName'])
                                    relations_codes.add(person['AssocCode'])
                                    tmp = (person['AssocName'], person['AssocCode'])
                                    relations_c[tmp] += 1
                                    t = person['Year'] if 'Year' in person else -1
                                    if t == '':
                                        t = -1
                                    else:
                                        t = int(t)
                                    edge_list.append((basic_info_person['PersonId'], person['AssocPersonId'], person['AssocCode'], t))
                        elif isinstance(person_assoc, dict):
                            person = person_assoc
                            relations.add(person['AssocName'])
                            relations_codes.add(person['AssocCode'])
                            tmp = (person['AssocName'], person['AssocCode'])
                            t = person['Year'] if 'Year' in person else -1
                            if t == '':
                                t = -1
                            else:
                                t = int(t)
                            edge_list.append((basic_info_person['PersonId'], person['AssocPersonId'], person['AssocCode'], t))
                            relations_c[tmp] += 1
            except json.decoder.JSONDecodeError:
                error += 1
                print(line)
    with open('./data_clean/cbdb_edgelists.tsv', 'w') as f:
        print("PersonIdA", 'PersonIdB', 'AssocCode', 'time', file=f, sep='\t')
        for edge in edge_list:
            print("\t".join([str(i) for i in edge]), file=f)

    print(len(relations), len(relations_codes), len(relations_c))
    print(relations)
    print(relations_codes)
    res_f = open('./data_clean/cbdb_relationship.tsv', 'w')
    print('AsscoName', 'AssocCode', 'CodeCount', file=res_f, sep='\t')
    for r in relations_c:
        print(r[0], r[1], relations_c[r], file=res_f, sep='\t')
    print('done!')

def cbdb_edgelist_data():
    # with open('./data_clean/icwsm-sign.tsv') as f:
    df = pd.read_csv('./data_clean/cbdb-sign.tsv', sep='\t')
    code_2_sign_dict = {i['CODE']:i['SIGN'] for i in df.to_dict(orient='records')}
    print(code_2_sign_dict)

    # get cbdb input results, A, B, t, s
    df_res = pd.read_csv("./data_clean/cbdb_edgelists.tsv", sep='\t')
    df_res['sign'] = df_res['AssocCode'].apply(lambda x: code_2_sign_dict[x])
    df_res['time'].replace({0: -1}, inplace=True)
    print(df_res.columns)
    ## 如果是负1，就填一下均值
    df_res.to_csv('./data_clean/cbdb_edgelists_with_sign.tsv', sep='\t', index=False)

def clean_cbdb_edge_list_data():
    ## 对于缺少的时间取均值作为时间记录。

    df = pd.read_csv('./data_clean/cbdb_edgelists_with_sign.tsv', sep='\t')
    df['a_b'] = df['PersonIdA'].astype(str) + '-' + df['PersonIdB'].astype(str)
    dic = defaultdict(list)
    for ind, item in df.iterrows():
        if item['time']!=-1:
            dic[item['a_b']].append(item['time'])
    res_dic = {}
    for i in dic:
        res_dic[i] = np.mean(dic[i])
    
    for i in dic:
        df.loc[(df['a_b']==i) & (df['time']==-1), 'time'] = int(res_dic[i])

    df = df.drop(columns=['a_b'])
    df.to_csv('./data_clean/cbdb_edgelists_with_sign_2.tsv', sep='\t', index=False)


def get_cbdb_person_data():
    res_dic = {}
    res_f = open('data_input/cbdb_person.tsv', 'w', encoding='utf8') 

    with open('datas/cbdb_all_data.jl') as f:
        for line in f:
            try:
                json_data = json.loads(line)
                if 'Person' not in json_data['Package']['PersonAuthority']['PersonInfo']:
                    continue
                person_data = json_data['Package']['PersonAuthority']['PersonInfo']['Person']
                basic_info_person = person_data['BasicInfo']
                pid = basic_info_person['PersonId']
                data_info = basic_info_person
                if 'PersonSocialAssociation' in data_info:
                    del data_info['PersonSocialAssociation']
                data_info['url'] = f'https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={pid}&o=json'
                res_dic[pid] = data_info
                print(pid, json.dumps(data_info), sep='\t', file=res_f)
            except json.decoder.JSONDecodeError:
                error += 1
                print(line)
    print('output cbdb_person.json done! total:', len(res_dic))

def main():
    # statistic_relation()
    # cbdb_edgelist_data()
    # clean_cbdb_edge_list_data()
    get_cbdb_person_data()

if __name__ == "__main__":
    main()


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

import lxml.html as html
import lxml.html.clean as html_clean

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--dirpath', default=BASE_DIR, help='current dir')
args = parser.parse_args()

CUR_DIR = args.dirpath

def main():
    fpath = './all_htmls/all/-congress-votes-29-1-s204.html'
    data_dir = './all_htmls/all'
    cleaner = html_clean.Cleaner()
    cleaner.style = True
    cleaner.javascript = True
    res_f = open('res.txt', 'w')
    for fname in os.listdir(data_dir):
        fpath = os.path.join(data_dir, fname)
        with open(fpath) as f:
            dom = html.fromstring(f.read())
            print(dom)
            res = dom.xpath('//div[@id="vote_notes"]')
            if len(res) != 1:
                print(fpath)
                return 
            res = res[0]
            js = {}
            js[fname] = str(html.tostring(cleaner.clean_html(res)))
            print(json.dumps(js), file=res_f)
    res_f.close()
    print('done!')


def get_bill_category(fname):
    fpath = os.path.join('govtrack', fname)
    res = set()
    with open(fpath) as f:
        for line in f:
            json_data = json.loads(line)
            for item in json_data['results']:
                dom = html.fromstring(item)
                link = "".join(dom.xpath('//div[@class="col-xs-12"]//a/@href')).strip()
                fname = link.replace('/', '-')
                res.add(fname)
    return res


def get_bill_category_dict():
    category_dic = {}
    for i in os.listdir('govtrack'):
        if i.endswith('.jl'):
            category_dic[i] = get_bill_category()

def get_bill_a_b():
    dirpath = os.path.join(CUR_DIR, 'all')
    for fname in os.listdir(dirpath):
        fpath = os.path.join(dirpath, fname)
        with open(fpath) as f:
            for l in f:
                print(l)

def get_bill_category_dict():
    category_dic = {}
    for fname in os.listdir('govtrack'):
        if fname.endswith('.jl'):
            cate, _, _ = fname.rpartition('.')
            category_dic[cate] = get_bill_category(fname)
            print(cate, 'done')
    return category_dic



def main():
    result_files = open('bill_results.txt', 'w')
    dirpath = os.path.join(CUR_DIR, 'all')
    for fname in os.listdir(dirpath):
        link = fname
        link = link.replace('-congress-votes-', '/congress/votes/')
        link, _, a = link.rpartition('-')
        link = link + '/' + a
        link = 'https://www.govtrack.us' + link + '/export/csv'
        print(fname, link, file=result_files)
    result_files.close()


def get_bill_features():
    # get name: features, 
    category_dic = get_bill_category_dict()
    dirpath = os.path.join(CUR_DIR, 'all')
    final_res = defaultdict(list)
    for fname in os.listdir(dirpath):
        for cate in category_dic:
            values = category_dic[cate]
            if fname in values:
                final_res[fname].append(cate)
    res_f = open('bill_features.txt', 'w')
    for fname in final_res:
        print(fname, final_res[fname], file=res_f)
    
    res_f.close()
    print('bill_features.txt', 'done!')


import logging
# https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial

# create logger
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

fh = logging.FileHandler('xxx.log')
fh.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add handler to logger
logger.addHandler(ch)
logger.addHandler(fh)


def get_bill_a_c():

    ## 得到bill_a_c.txt的数据，包括人物，法案，符号，时间，标题
    from io import StringIO

    # congressman, bill, sign, t, note 
    res_f = open('bill_a_c.txt', 'w', encoding='utf8')
    print('\t'.join(['person', 'bill_name', 'sign', 'date', 'title']), file=res_f)
    # res_f2 = open('bill_a_b.txt', 'w')

    with open('bill_features.txt') as f:
        for l in tqdm(f):
            try:
                fname, _, features = l.partition(' ')
                fname2 = fname +  '.csv'
                fpath = os.path.join('csv/vote_results', fname2)
                html_fpath = os.path.join('all', fname)
                with open(html_fpath, encoding='utf8') as f:
                    dom = html.fromstring(f.read())
                title = "".join([i for i in dom.xpath('//h1/text()')]).strip()
                title = re.sub(r'[\t\n\r]', ' ', title)
                title = title.strip()
                date = "".join(list(dom.xpath('//h1/following-sibling::div/text()')[0])).strip() 
                date = re.sub(r'[\t\n\r]', ' ', date)            
                # print(date, title)
                lins = []
                flag = 0
                with open(fpath, encoding='utf8') as f:
                    for ind, l in enumerate(f):
                        if l.startswith('person,state'):
                            flag = 1
                        if flag:
                            lins.append(l)
                df = pd.read_csv(StringIO("".join(lins)))
                cols = df.columns.values

                assert json.dumps(list(cols)) == json.dumps(["person", "state", "district", "vote", "name", "party"]), (fpath, list(cols))
                
                yes_set = []
                no_set = []

                for k, row in df.iterrows():
                    person = row.to_dict()
                    bill = {}
                    bill['name'] = fname
                    bill['title'] = title
                    sign = person['vote']

                    if sign == 'Yea':
                        yes_set.append(person['person'])
                    if sign == 'Nay':
                        no_set.append(person['person'])

                    with open(f'persons/{person["person"]}.jl', 'a') as f:
                        f.write(json.dumps(person) + '\n')
                    t = date
                    print(person['person'], bill['name'].strip(), sign.strip(), t.strip(), bill['title'], sep='\t', file=res_f)

                # for a in yes_set:
                #     for b in no_set:
                #         print(a, b, fname, -1, date, file=res_f2)
                    
                #     for b in yes_set:
                #        print(a, b, fname, 1, date, file=res_f2)

                # for a in no_set:
                #     for a in no_set:
                #         print(a, b, fname, 1, date, file=res_f2)

            except Exception as e:
                logger.error(e, exc_info=True)
                logger.error(l)
    
    res_f.close()
    # res_f2.close()


def clean_a_c_data():
    datas = []
    from datetime import datetime
    log_file = open('logs/dirty_data.log', 'w')
    data_path = './datas/bill_a_c.txt'
    with open(data_path) as f:
        for ind, line in tqdm_notebook(enumerate(f)):
            if ind == 0: continue #首行为header
            data = line.split('\t')
            d = {}
            try:
                assert len(data) == 5, line
                d['person_id'] = data[0]
                d['bill_name'] = data[1]
                def replace_yea_aye(x):
                    x = x.upper()
                    x = x.replace('NAY', 'NO')
                    x = x.replace('AYE', 'YEA')
                    return x
                d['sign'] = replace_yea_aye(data[2])
                assert d['sign'] in set(['NO', 'NOT VOTING', 'YEA', 'PRESENT', 'UNKNOWN']), d['sign'] + line
                x = data[3]
                if x.find('at') > -1:
                    x, _, _ = x.partition('at')
                t = x.replace('.', '').strip()
                res = datetime.strptime(t, '%b %d, %Y')
                d['date'] = res
                d['title'] = data[4]
                datas.append(d)
            except Exception as e:
                print(data, traceback.format_exc(), file=log_file)
    log_file.close()
    df = pd.DataFrame(datas)
    df.to_csv('./data_clean/bill_a_c_clean.tsv', sep='\t')


def main():
    # get_bill_features()
    get_bill_a_c_a_b()

    
if __name__ == "__main__":
    main()

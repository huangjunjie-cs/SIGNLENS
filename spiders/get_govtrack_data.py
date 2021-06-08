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
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--dirpath', default=BASE_DIR, help='Current directory')

args = parser.parse_args()

DATA_DIR = os.path.join(BASE_DIR, 'govtrack')

from functools import wraps
def retry(operation):
    @wraps(operation)
    def wrapped(*args, **kwargs):
        last_raised = None
        RETRIES_LIMIT = 3
        for _ in range(RETRIES_LIMIT):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                print("retrying %s", operation.__qualname__)
                last_raised = e
                time.sleep(5)
        raise last_raised

    return wrapped


@retry
def get_json_data(url):
    content = requests.get(url).content
    json_data = json.loads(content)
    return json_data


def get_list_data_0(option_name='all', url='https://www.govtrack.us/congress/votes?sort=-created&page={}&faceting=false&allow_redirect=true&do_search=1'):
    url1 = url.format(1)
    content = requests.get(url1).content
    json_data = json.loads(content)
    res_num = json_data['total']
    fpath = os.path.join(DATA_DIR, f'{option_name}.jl')
    if os.path.exists(fpath):
        print(fpath, 'done!')
        return
    res_f = open(fpath, 'w')
    for i in range(1, res_num // 20 + 1):
        url1 = url.format(i)
        print(url1)
        json_data = get_json_data(url1)
        res_f.write(json.dumps(json_data) + '\n')
        time.sleep(0.5)
        print(i, 'done!')
    res_f.close()

def get_list_data_1():
    """get list datas
    """
    url = 'https://www.govtrack.us/congress/votes?sort=-created&page=1&faceting=false&allow_redirect=true&do_search=1'
    content = requests.get(url).content
    json_data = json.loads(content)

    url_template = 'https://www.govtrack.us/congress/votes?sort=-created&page={}&faceting=false&allow_redirect=true&do_search=1'
    options = json_data['options']
    for option in options:
        option_name = option[0] # session
        values = option[2] 
        for value in values:
            v = value[0] # 304
            v_name = value[1] # 2020 (116th Congress)
            v_name = v_name.replace(' ', '-')
            if v == '__ALL__':
                continue
            else:
                url_t = url_template + f'&{option_name}={v}'
                get_list_data_0(option_name+'-'+v_name, url_t)
                print(option_name, v_name, 'done!')



def get_detail_data_2():
    cases_list_fpath = os.path.join(DATA_DIR, 'lists.txt')
    cases_list_f = open(cases_list_fpath, 'w')
    for fname in os.listdir(DATA_DIR):
        if fname.startswith('.') or fname.endswith('.txt'):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        print(fname)
        with open(fpath) as f:
            json_data = json.load(f)
            res = json_data['results']
        for i in res:
            dom = html.fromstring(i)
            title = "".join(dom.xpath('//div[@class="col-xs-12"]//a/text()')).strip()
            link = "".join(dom.xpath('//div[@class="col-xs-12"]//a/@href')).strip()
            source = "".join(dom.xpath('//span[@class="fa fa-barcode fa-fw"]/parent::div/text()')).strip()
            date = "".join(dom.xpath('//span[@class="fa fa-calendar fa-fw"]/parent::div/text()')).strip()
            result = "".join(dom.xpath('//span[@class="fa fa-info fa-fw"]/parent::div/text()')).strip()
            print(title, link, date, source, result, sep='\t', file=cases_list_f)
    cases_list_f.close()

@retry
def crawl_a_page(url):
    content = requests.get(url).content
    return content



def get_list_data_2():
    cases_list_fpath = os.path.join(DATA_DIR, 'lists.txt')
    cases_list_f = open(cases_list_fpath, 'w')
    all_links = []
    with open('all.jl') as f:
        for line in f:
            json_data = json.loads(line)
            res = json_data['results']
            for i in res:
                dom = html.fromstring(i)
                title = "".join(dom.xpath('//div[@class="col-xs-12"]//a/text()')).strip()
                link = "".join(dom.xpath('//div[@class="col-xs-12"]//a/@href')).strip()
                source = "".join(dom.xpath('//span[@class="fa fa-barcode fa-fw"]/parent::div/text()')).strip()
                date = "".join(dom.xpath('//span[@class="fa fa-calendar fa-fw"]/parent::div/text()')).strip()
                result = "".join(dom.xpath('//span[@class="fa fa-info fa-fw"]/parent::div/text()')).strip()
                print(title, link, date, source, result, sep='\t', file=cases_list_f)
                all_links.append(link)
    all_dir = os.path.join(DATA_DIR, 'all')
    if not os.path.exists(all_dir):
        os.mkdir(all_dir)

    for link in all_links:
        fname = link.replace('/', '-')
        url = 'https://www.govtrack.us' + link
        content = crawl_a_page(url)
        fpath = os.path.join(all_dir, fname)
        with open(fpath, 'wb') as f:
            f.write(content)
            print(url, 'done!')


def main():
    # get_list_data_0()
    # get_list_data_1()
    get_list_data_2()

if __name__ == "__main__":
    main()



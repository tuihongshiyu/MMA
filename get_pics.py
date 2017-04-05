import requests
import urllib.request
import time
import re
from bs4 import BeautifulSoup
import os
import threading
import fileinput
from multiprocessing import Pool
import log
import multiprocessing

PATH = '/Users/HirosueRyouko/Pictures/MMA/'
ID_LIST = []
KEYWORD='Oil paintings'

def get_page(keyword, page_no=1):
    url = 'http://www.metmuseum.org/api/search?page=' + str(page_no) + '&q=' + keyword
    # print(url)
    page = requests.get(url)
    soup = str(BeautifulSoup(page.text, 'lxml'))
    soup_dic = str2dic(soup)
    # print(soup_dic)
    return soup_dic


def keyword2id(keyword='Oil on canvas'):
    log.log_write(sentence='keyword2id begin,keyword = '+keyword,path=PATH,name='MMA '+KEYWORD)

    LIST = []
    cal = 0
    for i in range(1000):

        try:
            page = get_page(keyword, page_no=i + 1)
        except:
            print('Error on page : ', i)
            return
        id_list = []

        try:
            page_info = page['results']
        except:
            cal = cal + 1
            if cal < 5:
                continue
            else:
                break

        for paint in page_info:
            try:
                if paint['cardType'] != 'art': continue
                id = int(paint['id'])
                id_list.append(id)

                if id not in LIST:
                    LIST.append(id)
            except:
                continue
        # print(i,id_list)
        # print(i,LIST)
        if (id_list == []): break
        log.log_write(sentence='page = '+str(i+1)+' Num of IDs: '+str(len(id_list)),path=PATH,name='MMA '+KEYWORD)
    # print(LIST)
    list_create(LIST, kind='id', keyword=keyword)
    return LIST


def id2url(list, keyword):
    id_url_list = []
    result = []
    div = []
    num_process = 16
    step = int(len(list) / num_process)
    for i in range(num_process):
        div.append(list[i * step:step * (1 + i)])
    # div=[list[0:step],list[step:2*step],list[2*step:3*step],list[3*step:]]

    p = Pool(num_process)
    for i in range(num_process):
        result.append(p.apply_async(url_sub, (div[i],)))

    p.close()
    p.join()
    for res in result:
        id_url_list[len(id_url_list):len(id_url_list)] = res.get()

    list_create(id_url_list, kind='url', keyword=keyword)
    return id_url_list


def url_sub(list):
    url_list = []
    pid = os.getpid()
    for pic in list:
        url = 'http://www.metmuseum.org/art/collection/search/' + pic
        # print(url)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'lxml')
        for tag in soup.find_all(property="og:image"):
            url = tag['content']
            if url not in url_list:
                url_list.append(str(pic))
                url_list.append(str(url))
        if(len(url_list)%20==0):
            print('pid: ', pid, str(len(url_list)/2), ' of ', str(len(list)), 'done')

    # print(url_list)

    return url_list


def list_create(list, kind, keyword):
    path = PATH + str(kind) + '_list_' + str(keyword) + '.txt'
    if not os.path.exists(path):
        f = open(path, 'w')
        f.close()
    else:
        os.remove(path)
        f = open(path, 'w')
        f.close()
    f_w = open(path, 'a')
    for id in list:
        f_w.write(str(id) + ' ')
    f_w.close()


def list_read(kind, keyword):
    path = PATH + str(kind) + '_list_' + str(keyword) + '.txt'
    if not os.path.exists(path):
        return
    f_r = open(path, 'r')
    with fileinput.input(path) as f:
        for line in f:
            return line.split()


def str2dic(str):
    str = str.replace("true", '1')
    str = str.replace("false", '0')
    str = str.replace("null", '0')
    pat = re.compile(r'<([^<>]*)>')
    str = pat.sub('', str)
    try:
        dic = eval(str)
    except:
        str = str.replace(",\"", '\n\"')
        pat = re.compile(r'/"([^/"]*)"')
        str = pat.sub('', str)
        return 'Error'
    return dic


def url2jpg(id_url_list, keyword='Oil on canvas'):
    if not id_url_list:
        id_url_list = list_read('url', 'Oil on canvas')
    url = []
    id = []
    div_id = []
    div_url = []

    num_process = 16

    for i in range(len(id_url_list)):
        if i % 2 == 0:
            id.append(id_url_list[i])
        else:
            url.append(id_url_list[i])

    step = int(len(url) / num_process)
    for i in range(num_process):
        div_id.append(id[i * step:step * (1 + i)])
        div_url.append(url[i * step:step * (1 + i)])

    p=Pool(num_process)
    for i in range(num_process):
        p.apply_async(downloads_multi,([div_id[i],div_url[i]],))
    p.close()
    p.join()
    return 0

def downloads_multi(id_url):
    id=id_url[0]
    url=id_url[-1]
    pid = os.getpid()

    for i in range(len(id)):
        download_pic(url[i], keyword=KEYWORD, name=id[i])
        if (i % 10 == 0):
            print('pid: ', pid, str(i), ' of ', str(len(url)), 'done')


def multi_process(target, num_process, list):
    result = []
    div = []
    step = int(len(list) / num_process)
    for i in range(num_process):
        div.append(list[i * step:step * (1 + i)])
    # div=[list[0:step],list[step:2*step],list[2*step:3*step],list[3*step:]]

    p = Pool(num_process)
    for i in range(num_process):
        result.append(p.apply_async(url_sub, (div[i],)))

    p.close()
    p.join()
    return result


def download_pic(url, keyword, name):
    path = PATH
    pic = requests.get(url)
    if not os.path.exists(path + keyword):
        os.mkdir(path + keyword)
    if os.path.exists(path + keyword + '/' + name + '.jpg'):
        return True
    # print(path + keyword + '/' + name + '.jpg')
    f = open(path + keyword + '/' + name + '.jpg', 'wb')
    f.write(pic.content)
    f.close()
    return False

def all_in_one(keyword):
    KEYWORD=keyword
    id_list = keyword2id(keyword=keyword)
    id_url_list = id2url(id_list, keyword=keyword)
    url2jpg(id_url_list=id_url_list, keyword=keyword)
    print('All things done.')


# keyword2id()
# print(get_page(keyword='Oil on canvas',page_no=7))
# list_read(keyword='Oil on canvas')
# url2jpg(id_url_list=list_read(kind='url', keyword='Oil paintings'), keyword='Oil paintings')
# url_sub(['206321'])
# id2url(list_read(kind='id',keyword='Oil paintings'))
all_in_one('Oil paintings')

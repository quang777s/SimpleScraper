# -*- coding: utf-8 -*-
import sys
import subprocess
import ast
import html
import json
import re
import requests
import logging
import datetime
from bs4 import BeautifulSoup
from dateutil.parser import parse

CURL_TEMPLATE = """
curl 'https://batdongsan.com.vn/cho-thue-van-phong-duong-ben-van-don-phuong-12-prj-the-tresor/can-ho-office-q4-30m2-nt-co-ban-12tr-th-lh-0903812456-pr{id}' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: en-US,en;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: max-age=0' -H 'Cookie: SERVERID=E; __cfduid=ddecd2be7769689a7d70d16dd179654c61513070065; ASP.NET_SessionId=2bwtv1fm5jd5jldq2is2xz0f; _ga=GA1.3.1508381977.1513070065; _gid=GA1.3.1634987642.1513070065; USER_SEARCH_PRODUCT_CONTEXT=49%7C50%7CSG%7C56%7C103%7C1319%7C2044%2C14126738; statsinfo=1513070085648%2C45aa57e8-9eb1-4892-bdf2-5dc4267303a8; __asc=8134524d1604a00fc488a963078; __auc=8134524d1604a00fc488a963078; sidtb=WdiwXIxcrxY6zXmpxPqwNsxkXhJTKQ8C; usidtb=ECyiRVvxaguOYodc2P0tYRWuH3QNosoM' -H 'Connection: keep-alive' -H 'If-Modified-Since: Tue, 12 Dec 2017 09:20:36 GMT' --compressed
"""
CURL_TEMPLATE_RETRY = """
curl '{url}' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: en-US,en;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: max-age=0' -H 'Cookie: SERVERID=E; __cfduid=ddecd2be7769689a7d70d16dd179654c61513070065; ASP.NET_SessionId=2bwtv1fm5jd5jldq2is2xz0f; _ga=GA1.3.1508381977.1513070065; _gid=GA1.3.1634987642.1513070065; USER_SEARCH_PRODUCT_CONTEXT=49%7C50%7CSG%7C56%7C103%7C1319%7C2044%2C14126738; statsinfo=1513070085648%2C45aa57e8-9eb1-4892-bdf2-5dc4267303a8; __asc=8134524d1604a00fc488a963078; __auc=8134524d1604a00fc488a963078; sidtb=WdiwXIxcrxY6zXmpxPqwNsxkXhJTKQ8C; usidtb=ECyiRVvxaguOYodc2P0tYRWuH3QNosoM' -H 'Connection: keep-alive' -H 'If-Modified-Since: Tue, 12 Dec 2017 09:20:36 GMT' --compressed
"""
START_ID = 16462532
END_ID = 16463532

city_address = {
    'Hồ Chí Minh': 1,
    'Hà Nội': 2,
    'Đà Nẵng': 3,
    'Bình Dương': 4,
    'Bà Rịa Vũng Tàu': 5,
    'Long An': 6,
    'Kiên Giang': 7,
    'Quảng Nam': 8,
    'Hải Phòng': 9,
    'Đồng Nai': 10,
    'Lâm Đồng': 11,
    'Khánh Hòa': 12,
    'Tiền Giang': 13,
    'Huế': 14,
    'Quảng Ninh': 15,
    'Thanh Hóa': 16
}

ad_types = {
    'Bán nhà riêng': 1,
    'Bán căn hộ chung cư': 2,
    'Bán đất': 3,
    'Bán nhà mặt phố': 4,
    'Bán đất nền dự án': 5,
    'Cho thuê văn phòng': 6,
    'Cho thuê căn hộ chung cư': 7,
    'Cho thuê nhà riêng': 8
}

def run_curl(command):
    p = subprocess.Popen(command, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response, err = p.communicate()
    return BeautifulSoup(response, 'html.parser')


def get_encode_email(html):
    return re.search('>(.*)</a>', html).group(1)


def process_html(response):
    info = {}
    titles = response.find_all('h1', attrs={"itemprop": "name"})
    if not titles:
        if not response.h2:
            return {'retry': False}
        if not response.h2.a:
            return {'retry': False}
        url = 'https://batdongsan.com.vn' + response.h2.a['href']
        return {'retry': url}

    for field in ['road', 'direction', 'front', 'floor', 
                    'bedroom', 'restroom', 'furniture', 'user_name', 
                    'user_address', 'user_phone', 'user_mobile', 'user_email']:
        info[field] = ''
    for field in ['bedroom', 'restroom']:
        info[field] = 'NULL'

    info['title'] = titles[0].getText()
    info['desc'] = response.find_all(
        'div', attrs={"class": "pm-desc"})[0].getText()

    detail_info = response.find_all('div', attrs={"class": "table-detail"})[0]
    detail_len = len(detail_info.find_all('div', attrs={'class': 'left'}))
    info['ad_type'] = detail_info.find_all(
        'div', attrs={'class': 'right'})[0].getText()
    info['address'] = detail_info.find_all(
        'div', attrs={'class': 'right'})[1].getText()

    contact_info = response.find_all('div', attrs={"class": "table-detail"})[1]
    contact_len = len(contact_info.find_all('div', attrs={'class': 'left'}))

    price_span = response.find_all('span', attrs={"class": "gia-title"})[0]
    info['price'] = price_span.find_all('strong')[0].getText()

    area_span = response.find_all('span', attrs={"class": "gia-title"})[1]
    info['area'] = area_span.find_all('strong')[0].getText()

    info['imgs'] = []
    thumbs = response.find_all('ul', attrs={"id": "thumbs"})
    if thumbs:
        imgs = thumbs[0].find_all('img')
        for img in imgs:
            src = img['src'].replace('resize/200x200/', '')
            info['imgs'].append(src)
    info['imgs'] = ','.join(info['imgs'])

    more_info = response.find_all('div', attrs={"class": "prd-more-info"})[0]
    info['date'] = more_info.find_all('div')[3].getText().replace(
        'Ngày đăng:', '').strip('\r\n')
    info['date'] = str(parse(info['date']))

    for i in range(2, detail_len):
        left = detail_info.find_all('div', attrs={'class': 'left'})[
            i].getText().strip('\r\n')
        right = detail_info.find_all(
            'div', attrs={'class': 'right'})[i].getText()
        if left == 'Đường vào':
            info['road'] = right
        elif left == 'Hướng nhà':
            info['direction'] = right
        elif left == 'Mặt tiền':
            info['front'] = right
        elif left == 'Số tầng':
            info['floor'] = right
        elif left == 'Số phòng ngủ':
            info['bedroom'] = re.search(r'\d+', right).group()
        elif left == 'Số toilet':
            info['restroom'] = re.search(r'\d+', right).group()
        elif left == 'Nội thất':
            info['furniture'] = right

    for i in range(0, contact_len):
        left = contact_info.find_all('div', attrs={'class': 'left'})[
            i].getText().strip('\r\n')
        right = contact_info.find_all(
            'div', attrs={'class': 'right'})[i].getText()
        if left == 'Tên liên lạc':
            info['user_name'] = right
        elif left == 'Địa chỉ':
            info['user_address'] = right
        elif left == 'Điện thoại':
            info['user_phone'] = right
        elif left == 'Mobile':
            info['user_mobile'] = right
        elif left == 'Email':
            info['user_email'] = html.unescape(get_encode_email(right))

    for attr in info:
        info[attr] = info[attr].strip('\r\n')

    return {'retry': False, 'info': info}


def get_detail(command):
    response = run_curl(command)
    return process_html(response)


def write_to_file(info):
    with open('result.sql', mode='a') as outfile:
        city_id = 0
        for city in city_address:
            if city in info['address']:
                city_id = city_address[city]
                break
        
        ad_type_id = 0
        for ad_type in ad_types:
            if ad_type in info['ad_type']:
                ad_type_id = ad_types[ad_type]
                break

        outfile.write('INSERT INTO infos VALUES(NULL, "' + info['title'] + '", "' + 
            info['desc'] + '", "' + info['ad_type'] + '", "' + info['address'] + '", "' +
            info['price'] + '", "' + info['area'] + '", "' + info['imgs'] + '", "' + 
            info['road'] + '", "' + info['direction'] + '", "' +
            info['front'] + '", "' + info['floor'] + '", ' + info['bedroom'] + ', ' + 
            info['restroom'] + ', "' + info['furniture'] + '", "' +
            info['user_name'] + '", "' + info['user_address'] + '", "' + 
            info['user_phone'] + '", "' + info['user_mobile'] + '", "' + 
            info['user_email'] + '", "' + info['date'] + '", '+str(city_id)+', '+str(city_id)+', NULL);\n')


def scrape():
    current_id = START_ID
    while current_id < END_ID:
        command = CURL_TEMPLATE.replace('{id}', str(current_id))
        detail = get_detail(command)
        print(detail)
        if detail['retry']:
            detail = get_detail(
                CURL_TEMPLATE_RETRY.replace('{url}', detail['retry']))
        if 'info' in detail:
            write_to_file(detail['info'])
        current_id += 1


def main():
    try:
        scrape()

    except Exception:
        raise


if __name__ == "__main__":
    main()

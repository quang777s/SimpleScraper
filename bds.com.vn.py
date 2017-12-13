import sys
import subprocess
import ast
import json
import requests
import logging
import datetime
from bs4 import BeautifulSoup

CURL_TEMPLATE = "curl https://batdongsan.com.vn/cho-thue-van-phong-duong-ben-van-don-phuong-12-prj-the-tresor/can-ho-office-q4-30m2-nt-co-ban-12tr-th-lh-0903812456-pr{id}"
CURL_TEMPLATE_RETRY = "curl {url}"
START_ID = 14126738
END_ID = 14126748

def run_curl(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response, err = p.communicate()
    return BeautifulSoup(response, 'html.parser')

def process_html(response):
    titles = response.find_all('h1', attrs={"itemprop": "name"})
    if titles:
        title = titles[0].getText()
        desc = response.find_all('div', attrs={"class": "pm-desc"})[0].getText()

        detail_info = response.find_all('div', attrs={"class": "table-detail"})[0]
        ad_type = detail_info.find_all('div', attrs={'class': 'right'})[0].getText()
        address = detail_info.find_all('div', attrs={'class': 'right'})[1].getText()

        print(title)
        print(desc)
        print(ad_type)
        print(address)
        return {'retry': False}
    else:
        url = 'https://batdongsan.com.vn' + response.h2.a['href']
        return {'retry': url}

def get_detail(command):
    response = run_curl(command)
    return process_html(response)

def scrape():
    current_id = START_ID
    while current_id < END_ID:
        command = CURL_TEMPLATE.replace('{id}', str(current_id))
        detail = get_detail(command)
        print(detail)
        if detail['retry']:
            detail = get_detail(CURL_TEMPLATE_RETRY.replace('{url}', detail['retry']))
        current_id += 1

def main():
    try:
        scrape()

    except Exception:
        raise    

if __name__ == "__main__":
    main()
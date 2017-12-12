import sys
import subprocess
import ast
import json
import requests
import logging
import datetime
from bs4 import BeautifulSoup

CURL_TEMPLATE = """
curl 'https://batdongsan.com.vn/cho-thue-van-phong-duong-ben-van-don-phuong-12-prj-the-tresor/can-ho-office-q4-30m2-nt-co-ban-12tr-th-lh-0903812456-pr{id}' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: en-US,en;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: max-age=0' -H 'Cookie: SERVERID=E; __cfduid=ddecd2be7769689a7d70d16dd179654c61513070065; ASP.NET_SessionId=2bwtv1fm5jd5jldq2is2xz0f; _ga=GA1.3.1508381977.1513070065; _gid=GA1.3.1634987642.1513070065; USER_SEARCH_PRODUCT_CONTEXT=49%7C50%7CSG%7C56%7C103%7C1319%7C2044%2C14126738; statsinfo=1513070085648%2C45aa57e8-9eb1-4892-bdf2-5dc4267303a8; __asc=8134524d1604a00fc488a963078; __auc=8134524d1604a00fc488a963078; sidtb=WdiwXIxcrxY6zXmpxPqwNsxkXhJTKQ8C; usidtb=ECyiRVvxaguOYodc2P0tYRWuH3QNosoM' -H 'Connection: keep-alive' -H 'If-Modified-Since: Tue, 12 Dec 2017 09:20:36 GMT' --compressed
"""
CURL_TEMPLATE_RETRY = """
curl '{url}' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: en-US,en;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: max-age=0' -H 'Cookie: SERVERID=E; __cfduid=ddecd2be7769689a7d70d16dd179654c61513070065; ASP.NET_SessionId=2bwtv1fm5jd5jldq2is2xz0f; _ga=GA1.3.1508381977.1513070065; _gid=GA1.3.1634987642.1513070065; USER_SEARCH_PRODUCT_CONTEXT=49%7C50%7CSG%7C56%7C103%7C1319%7C2044%2C14126738; statsinfo=1513070085648%2C45aa57e8-9eb1-4892-bdf2-5dc4267303a8; __asc=8134524d1604a00fc488a963078; __auc=8134524d1604a00fc488a963078; sidtb=WdiwXIxcrxY6zXmpxPqwNsxkXhJTKQ8C; usidtb=ECyiRVvxaguOYodc2P0tYRWuH3QNosoM' -H 'Connection: keep-alive' -H 'If-Modified-Since: Tue, 12 Dec 2017 09:20:36 GMT' --compressed
"""
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
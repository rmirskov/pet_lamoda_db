import requests
import re

URL = 'https://ru.proxy-tools.com/proxy' 

headers = {   
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 YaBrowser/23.7.1.1215 Yowser/2.5 Safari/537.36',
    'accept': '*/*'
}

ip_address_pattern = r'(?<=\>)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?=\<)'

def add_proxy( url: str, page_num: int, proxy_list: list[str]) -> None:
    '''
    Scraping ip-address proxy-servers from url
    '''
    r = requests.get(f'{url}?page={page_num}', headers=headers)
    if r.status_code == 200:
        text = r.text
        proxy_list.extend(list(re.findall(ip_address_pattern, text)))

def main(url=URL, proxy_list=list(), min_count=200) -> list[str]:
    page = 1
    max_length = len(proxy_list)

    while len(proxy_list) < min_count:
        add_proxy(url, page, proxy_list)
        cur_length = len(proxy_list)
        if max_length < cur_length:
            max_length = cur_length
        else:
            break
        page += 1

    return proxy_list

if __name__ == '__main__':
    with open('proxy.txt', 'w') as f:
        f.write(' '.join(main()))



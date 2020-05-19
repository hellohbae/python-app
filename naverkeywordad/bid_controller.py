from bs4 import BeautifulSoup
import urllib.request as req
from urllib.parse import quote
import json
from pyvirtualdisplay import Display
from selenium import webdriver
import airtable
import naver_ad

AIRTABLE_API_KEY = 'keygLnwALvJEd9AVc'
AIRTABLE_BASE_URL = 'https://api.airtable.com/v0/appFAQcgBJy6jIXSw'

PC_BASE_SEARCH_URL = 'https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query='
MOBILE_BASE_SEARCH_URL = 'https://m.search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query='

NAVER_SECRET_KEY = 'AQAAAABZZNcmQnJhsoPKPB+OVnz+yKMx8Mk5JTgbo9VG/XAJEA=='
NAVER_API_KEY = '01000000005964d726427261b283ca3c1f8e567cfeff6fee2fb0c3e7915c994f165a35bfbe'
CUSTOMER_ID = '910516'
NAVER_BASE_URL = 'https://api.naver.com'

MAXIMUM_CAC = 500
BASE_CAC = 70
INCREASE_UNIT = 10
DEVICE = 'PC'


if __name__=='__main__':
    airtable = airtable.Airtable(AIRTABLE_API_KEY, AIRTABLE_BASE_URL)
    naver_ad = naver_ad.NaverAd(NAVER_SECRET_KEY, NAVER_API_KEY, NAVER_BASE_URL,CUSTOMER_ID)

    keywords = airtable.get_request_all(airtable.get_base_url()+'/test_keywords')

    if DEVICE is 'MOBILE':
        display = Display(visible=0, size=(800, 600))
        display.start()
        browser = webdriver.Chrome('./chromedriver')

    for keyword_record in keywords:
        keyword = keyword_record['fields']['keyword'].replace(' ','')
        byte_keyword = quote(keyword)
        bid = keyword_record['fields']['bid']

        data = {
            'device': DEVICE,
            'period': 'MONTH',
            'items': [keyword]
        }
        signature, m = naver_ad.make_signature('POST', '/estimate/exposure-minimum-bid/keyword')
        last_position_estimate = naver_ad.post_request(signature, naver_ad.get_base_url()+'/estimate/exposure-minimum-bid/keyword', json.dumps(data), m)
        
        data = {
            'device': DEVICE,
            'items': [{
                'key': keyword, 
                'position': 1
                }]
        }
        signature, m = naver_ad.make_signature('POST', '/estimate/average-position-bid/keyword')
        first_position_estimate = naver_ad.post_request(signature, naver_ad.get_base_url()+'/estimate/average-position-bid/keyword', json.dumps(data), m)
        
        if DEVICE is 'PC':
            base_search_url = PC_BASE_SEARCH_URL
        else:
            base_search_url = MOBILE_BASE_SEARCH_URL

        renew_bid = bid
        if first_position_estimate!=last_position_estimate:
            url = base_search_url+byte_keyword
            if DEVICE is 'PC':
                json_data = req.urlopen(url).read()
                soup = BeautifulSoup(json_data, 'html.parser')
                power_link_body = soup.find_all('a', {'class':'lnk_tit'})
            else:
                browser.get(url)
                soup = BeautifulSoup(browser.page_source, 'html.parser')
                power_link_body = soup.find_all('span', {'class':'tit_area'})
            max_depth = len(power_link_body)
            rank = 1
            not_found = True
            for each_link in power_link_body:
                if 'quantastic.ai' in each_link.attrs['onclick']:
                    if rank < max_depth-1:
                        renew_bid = bid-INCREASE_UNIT if bid-INCREASE_UNIT < BASE_CAC else bid
                    found = False
                    break
                rank += 1
            if not_found:
                renew_bid = bid + INCREASE_UNIT
        elif first_position_estimate==last_position_estimate and bid!=BASE_CAC:
            renew_bid = BASE_CAC
            
        if renew_bid > MAXIMUM_CAC:
            airtable.delete_request(airtable.get_base_url()+'/test_keywords/'+keyword_record['id'])
            renew_bid = BASE_CAC
            keyword_record['fields']['bid'] = renew_bid
            keyword_record['fields'].pop('id', None)
            airtable.post_request(airtable.get_base_url()+'/bid_failed', json.dumps({"fields":keyword_record['fields']}))
        elif renew_bid != bid:
            data = {
                'bid': renew_bid
            }
            airtable.update_request(airtable.get_base_url()+'/test_keywords/'+keyword_record['id'], json.dumps({"fields":data}))
        else:
            continue

        data = {
                'nccAdgroupId': keyword_record['fields']['naver_group_id'],
                'nccKeywordId': keyword_record['fields']['naver_keyword_id'],
                'bidAmt': renew_bid,
                'useGroupBidAmt': False
        }
        signature, m = naver_ad.make_signature('PUT', '/ncc/keywords/'+keyword_record['fields']['naver_keyword_id'])
        result = naver_ad.put_request(signature, naver_ad.get_base_url()+'/ncc/keywords/'+keyword_record['fields']['naver_keyword_id']+'?fields=bidAmt', json.dumps(data), m)

        print(result)

    if DEVICE is 'MOBILE':
        browser.quit()
        display.stop()



            




    
"""
result2[1].attrs['onclick']
result2[1].get_text()
result2 = result.findAll('a', {'class':'lnk_tit'})['contents']
"""
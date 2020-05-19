#-*- coding: utf-8 -*-
import json
import airtable
import naver_ad

AIRTABLE_API_KEY = 'keygLnwALvJEd9AVc'
AIRTABLE_BASE_URL = 'https://api.airtable.com/v0/appFAQcgBJy6jIXSw'

NAVER_SECRET_KEY = 'AQAAAABZZNcmQnJhsoPKPB+OVnz+yKMx8Mk5JTgbo9VG/XAJEA=='
NAVER_API_KEY = '01000000005964d726427261b283ca3c1f8e567cfeff6fee2fb0c3e7915c994f165a35bfbe'
CUSTOMER_ID = '910516'
NAVER_BASE_URL = 'https://api.naver.com'

NCC_CAMPAIGN_ID = 'cmp-a001-01-000000001638714'
AD_GROUP_SIZE = 100
MAXIMUM_CAC = 500
BASE_CAC = 70
DEVICE = 'PC'

def classify_by_ad_group(records):
    list_by_keyword_group = [ [records[0]] ]
    for i in range(1, len(records)):
        not_found = True
        for group in list_by_keyword_group:
            if group[0]['ad_group_id']==records[i]['ad_group_id']:
                group.append(records[i])
                not_found = False
                continue
        if not_found:
            list_by_keyword_group.append([ records[i] ])

    return list_by_keyword_group

def find_ad_group(target_url, airtable, ad_group_id, max_group_size):
    naver_ad_group_records = airtable.get_request_all(target_url)
    for record in naver_ad_group_records:
        if record['fields']['ad_group_id'] == ad_group_id and record['fields']['number_of_keywords'] < max_group_size:
            return record['id'], record['fields']['naver_ad_group_id'], max_group_size-record['fields']['number_of_keywords']

    return None, None, None

def create_new_naver_ad_group(airtable, naver_ad, naver_ad_group_number, biz_channel, campaign_id, ad_group_id):
    data = {
        'name': 'group_'+str(naver_ad_group_number),
        'pcChannelId': biz_channel[0]['nccBusinessChannelId'],
        'mobileChannelId': biz_channel[0]['nccBusinessChannelId'],
        'nccCampaignId': campaign_id,
        'adgroupAttrJson': {
            'media': DEVICE
        }
    }
    signature, m = naver_ad.make_signature('POST', '/ncc/adgroups')
    naver_ad_group = naver_ad.post_request(signature,'https://api.naver.com/ncc/adgroups', json.dumps(data), m)
    print(naver_ad_group)
    data = {
        'ad_group_id': ad_group_id,
        'naver_ad_group_id': naver_ad_group['nccAdgroupId'],
        'number_of_keywords': 0
    }
    response = airtable.post_request(airtable.get_base_url()+'/naver_ad_group', json.dumps({"fields": data}))

    return response['id'], response['fields']['naver_ad_group_id']

if __name__=='__main__':
    airtable = airtable.Airtable(AIRTABLE_API_KEY, AIRTABLE_BASE_URL)
    naver_ad = naver_ad.NaverAd(NAVER_SECRET_KEY, NAVER_API_KEY, NAVER_BASE_URL,CUSTOMER_ID)
    keyword_records = airtable.get_request_all(airtable.get_base_url()+'/keywords')
    not_registered_keywords = []
    for record in keyword_records:
        record['fields']['keywords_record_id'] = record['id']
        if not 'naver_keyword_id' in list(record['fields'].keys()):
            not_registered_keywords.append(record['fields'])

    keywords_by_ad_group = classify_by_ad_group(not_registered_keywords)

    signature, m = naver_ad.make_signature('GET', '/ncc/channels')
    biz_channel = naver_ad.get_request(signature, naver_ad.get_base_url()+'/ncc/channels', m)
    signature, m = naver_ad.make_signature('GET', '/ncc/adgroups')
    naver_ad_groups = naver_ad.get_request(signature, naver_ad.get_base_url()+'/ncc/adgroups?nccCampaignId='+NCC_CAMPAIGN_ID, m)
    naver_ad_group_number = len(naver_ad_groups) + 1

    for each_keyword_group in keywords_by_ad_group:
        ad_group_id = each_keyword_group[0]['ad_group_id']
        needed_space = len(each_keyword_group)
        record_id, naver_ad_group_id, rest_size = find_ad_group(airtable.get_base_url()+'/naver_ad_group', airtable, ad_group_id, AD_GROUP_SIZE)
        if not record_id:
            record_id, naver_ad_group_id = create_new_naver_ad_group(airtable, naver_ad, naver_ad_group_number, biz_channel, NCC_CAMPAIGN_ID, ad_group_id)
            rest_size = AD_GROUP_SIZE
            naver_ad_group_number += 1

        index = 0
        while True:
            for i in range( min(needed_space, rest_size) ):
                data = {
                    'device': DEVICE,
                    'period': 'MONTH',
                    'items': [each_keyword_group[index]['keyword'].replace(' ', '')]
                }
                signature, m = naver_ad.make_signature('POST', '/estimate/exposure-minimum-bid/keyword')
                bid_estimate = naver_ad.post_request(signature, naver_ad.get_base_url()+'/estimate/exposure-minimum-bid/keyword', json.dumps(data), m)
                bid = bid_estimate['estimate'][0]['bid'] 
                if bid_estimate['estimate'][0]['bid'] > MAXIMUM_CAC:
                    bid = BASE_CAC
                data = [{
                    'keyword':each_keyword_group[index]['keyword'].replace(' ', ''),
                    'bidAmt': bid
                    }]
                signature, m = naver_ad.make_signature('POST', '/ncc/keywords')
                naver_ad_keyword = naver_ad.post_request(signature, naver_ad.get_base_url()+'/ncc/keywords?nccAdgroupId='+naver_ad_group_id, json.dumps(data), m)
                data = {
                    'naver_keyword_id': naver_ad_keyword[0]['nccKeywordId'],
                    'bid': naver_ad_keyword[0]['bidAmt']
                }
                airtable.update_request(airtable.get_base_url()+'/keywords/'+each_keyword_group[index]['keywords_record_id'], json.dumps({"fields": data}))
                index += 1

            data = {
                'number_of_keywords': AD_GROUP_SIZE-rest_size + min(needed_space, rest_size)
            }
            airtable.update_request(airtable.get_base_url()+'/naver_ad_group/'+record_id, json.dumps({"fields": data}))
            needed_space = needed_space - min(needed_space, rest_size)

            if needed_space>0:
                record_id, naver_ad_group_id = create_new_naver_ad_group(airtable, naver_ad, naver_ad_group_number, biz_channel, NCC_CAMPAIGN_ID, ad_group_id)
                rest_size = AD_GROUP_SIZE
                naver_ad_group_number += 1
            else:
                break


    




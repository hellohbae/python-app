import json
import airtable
import naver_ad

AIRTABLE_BASE_URL = 'https://api.airtable.com/v0/appFAQcgBJy6jIXSw'
AIRTABLE_API_KEY = 'keygLnwALvJEd9AVc'

NAVER_SECRET_KEY = 'AQAAAABZZNcmQnJhsoPKPB+OVnz+yKMx8Mk5JTgbo9VG/XAJEA=='
NAVER_API_KEY = '01000000005964d726427261b283ca3c1f8e567cfeff6fee2fb0c3e7915c994f165a35bfbe'
CUSTOMER_ID = '910516'
NAVER_BASE_URL = 'https://api.naver.com'


if __name__=='__main__':
    airtable = airtable.Airtable(AIRTABLE_API_KEY, AIRTABLE_BASE_URL)
    naver_ad = naver_ad.NaverAd(NAVER_SECRET_KEY, NAVER_API_KEY, NAVER_BASE_URL, CUSTOMER_ID)

    new_ads = airtable.get_request_all(airtable.get_base_url()+'/new_ads')

    for new_ad in new_ads:
        if new_ad['fields']['method'] == 'create':
            data = {
                'ad':{
                    "pc": {
                    "final": "http://quantastic.ai"
                    },
                    "mobile": {
                        "final": "http://quantastic.ai"
                    },
                    "headline": new_ad['fields']['title'],
                    "description": new_ad['fields']['description']
                },
                'nccAdgroupId': '',
                'type': 'TEXT_45'
            }
            new_ad['fields'].pop('id', None)
            new_ad['fields'].pop('method', None)
            new_ad['fields'].pop('ads_id', None)

            ad = airtable.post_request(airtable.get_base_url()+'/ads', json.dumps({"fields":new_ad['fields']}))

            print(ad)

            naver_ad_groups = airtable.get_request_all(airtable.get_base_url()+'/naver_ad_group')
            naver_ad_group_id_list = []
            for naver_ad_group in naver_ad_groups:
                if new_ad['fields']['ad_group_id'] == naver_ad_group['fields']['ad_group_id']:
                    naver_ad_group_id_list.append(naver_ad_group['fields']['naver_ad_group_id'])
            
            for naver_ad_group_id in naver_ad_group_id_list:
                data['nccAdgroupId'] = naver_ad_group_id
                signature, m = naver_ad.make_signature('POST', '/ncc/ads')
                registered_ad = naver_ad.post_request(signature, naver_ad.get_base_url()+'/ncc/ads', json.dumps(data), m)
            
                if not 'nccAdId' in registered_ad.keys():
                    print(registered_ad)
                    airtable.delete_request(airtable.get_base_url()+'/ads/'+ad['id'])
                    break
                data2 = {
                    'naver_ad_id': registered_ad['nccAdId'],
                    'naver_ad_group_id': naver_ad_group_id,
                    'ads_id': [ad['id']]
                }
                result = airtable.post_request(airtable.get_base_url()+'/naver_ads', json.dumps({'fields':data2}))
                print(result)
        else:
            naver_ads = airtable.get_request_all(airtable.get_base_url()+'/naver_ads')
            naver_ad_ids = []
            for each_naver_ad in naver_ads:
                if new_ad['fields']['ads_id'] == each_naver_ad['fields']['ads_id']:
                    airtable.delete_request(airtable.get_base_url()+'/naver_ads/'+each_naver_ad['id'])
                    signature, m = naver_ad.make_signature('DELETE', '/ncc/ads/'+each_naver_ad['fields']['naver_ad_id'])
                    naver_ad.delete_request(signature, naver_ad.get_base_url()+'/ncc/ads/'+each_naver_ad['fields']['naver_ad_id'], m)                

            airtable.delete_request(airtable.get_base_url()+'/ads/'+new_ad['fields']['ads_id'][0])
            
        airtable.delete_request(airtable.get_base_url()+'/new_ads/'+new_ad['id'])
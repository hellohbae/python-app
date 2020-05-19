import pycurl
from io import BytesIO
import json
import time


class Airtable():
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def get_base_url(self):
        return self.base_url

    def get_request(self, target_url):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.HTTPHEADER, ['Authorization: Bearer '+self.api_key])
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body

    def post_request(self, target_url, data):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.HTTPHEADER, ['Authorization: Bearer '+self.api_key, 'Content-Type: application/json'])
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body

    def delete_request(self, target_url):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.HTTPHEADER, ['Authorization: Bearer '+self.api_key])
        c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body

    def update_request(self, target_url, data):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.HTTPHEADER, ['Authorization: Bearer '+self.api_key, 'Content-Type: application/json'])
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(pycurl.CUSTOMREQUEST, 'PATCH')
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body

    def get_request_all(self, target_url):
        all_response = []
        
        response = self.get_request(target_url)
        for record in response['records']:
            all_response.append(record)

        while('offset' in list(response)):
            offset=response['offset']
            response = self.get_request(target_url+'?offset='+offset)
            for record in response['records']:
                all_response.append(record)

        return all_response

    def find_ad_group(self, ad_group_name):
        response = self.get_request(self.base_url+'/ad_group')
        for record in response['records']:
            if record['fields']['name']==ad_group_name:
                return record['id']

        return None

    def get_ad_group(self, group_data, number_of_adjective):
        ad_group_record_id = self.find_ad_group(group_data['ad_group_name'])
        if not ad_group_record_id:
            data = {
                'name': group_data['ad_group_name'],
                'essential_keyword_group_id': group_data['essential_keyword_group_id']
            }
            for i in range(number_of_adjective):
                key = 'adjective_keyword_group_id_'+str(i+1)
                data[key] = group_data[key]
            ad_group_record = self.post_request(self.base_url+'/ad_group', json.dumps({"fields": data}))
            ad_group_record_id = ad_group_record['id']

        return ad_group_record_id
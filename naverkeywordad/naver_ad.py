import pycurl
from io import BytesIO
import json
import hashlib
import hmac
import base64
import time


class NaverAd():
    def __init__(self, secret_key, api_key, base_url, customer_id):
        self.secret_key = secret_key
        self.api_key = api_key
        self.base_url = base_url
        self.customer_id = customer_id
    
    def get_base_url(self):
        return self.base_url

    def create_sha256_signature(self, message):
        byte_message = bytes(message, 'utf-8')
        byte_key = bytes(self.secret_key, 'utf-8')
        hash = hmac.new(byte_key, byte_message, hashlib.sha256)
        #hash.hexdigest()

        return str(base64.b64encode(hash.digest()), 'utf-8')

    def make_signature(self, http_method, request_url):
        milliseconds_since_unix_epoch = str(int(round(time.time() * 1000)))
        message = milliseconds_since_unix_epoch + '.' + http_method + '.' + request_url

        return self.create_sha256_signature(message), milliseconds_since_unix_epoch

    def get_request(self, signature, target_url, milliseconds_since_unix_epoch):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.HTTPHEADER, 
        ['X-Timestamp: '+milliseconds_since_unix_epoch,
        'X-API-KEY: '+self.api_key,
        'X-Customer: '+self.customer_id,
        'X-Signature: '+signature])
        c.setopt(c.URL, target_url)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body

    def post_request(self, signature, target_url, data, milliseconds_since_unix_epoch):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.HTTPHEADER, 
        ['X-Timestamp: '+milliseconds_since_unix_epoch,
        'X-API-KEY: '+self.api_key,
        'X-Customer: '+self.customer_id,
        'X-Signature: '+signature,
        'Content-Type: application/json;charset=UTF-8'])
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body

    def delete_request(self, signature, target_url, milliseconds_since_unix_epoch):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.HTTPHEADER, 
        ['X-Timestamp: '+milliseconds_since_unix_epoch,
        'X-API-KEY: '+self.api_key,
        'X-Customer: '+self.customer_id,
        'X-Signature: '+signature])
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        #dict_body = json.loads(str_body)

        return str_body

    def put_request(self, signature, target_url, data, milliseconds_since_unix_epoch):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.HTTPHEADER, 
        ['X-Timestamp: '+milliseconds_since_unix_epoch,
        'X-API-KEY: '+self.api_key,
        'X-Customer: '+self.customer_id,
        'X-Signature: '+signature,
        'Content-Type: application/json;charset=UTF-8'])
        c.setopt(c.URL, target_url)
        c.setopt(pycurl.POSTFIELDS, data)
        c.setopt(pycurl.CUSTOMREQUEST, 'PUT')
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        byte_body = buffer.getvalue()
        str_body = byte_body.decode('utf-8')
        dict_body = json.loads(str_body)

        return dict_body
        
import os
import requests
import json

from module import log
from django.conf import settings

WD_SERVER_HOST = settings.WD_API_SERVER_HOST
AUTH_API_URL = WD_SERVER_HOST + 'module_auth_mgr/token/obtain_token/'


def _auth_wd_api_token():

    log.debug('auth api token')

    payload = {'username': os.environ.get('WD_USER'),
               'password': os.environ.get('WD_PASSWORD')}
    headers = {'Content-Type': 'application/json'}

    rs = requests.post(AUTH_API_URL,
                       data=json.dumps(payload),
                       headers=headers,
                       timeout=5)

    if rs.status_code == 200:
        content = json.loads(rs.content)
        api_token = content.get('auth_token')
        if api_token:
            os.environ['WD_API_TOKEN'] = api_token


def setup_wd_api_token():
    api_token = os.environ.get('WD_API_TOKEN', "")

    try:
        if api_token == "" or api_token is None:
            _auth_wd_api_token()
    except:
        log.exception()


def get_wd_api_token():
    api_token = os.environ.get('WD_API_TOKEN', "")
    try:
        if api_token == "" or api_token is None:
            _auth_wd_api_token()

        api_token = os.environ.get('WD_API_TOKEN')
        return f'Token {api_token}'
    except:
        log.exception()
        return ""


def get_wd_api_header():
    wd_api = get_wd_api_token()
    return {'Content-Type': 'application/json', 'Authorization': wd_api}


def get_dtu_api_header():
    token = os.environ.get('DTU_STATION_API_TOKEN', "")
    api_token = f'Token {token}'

    return {'Content-Type': 'application/json', 'Authorization': api_token}


def get_anegel_wd_api_header():
    token = os.environ.get('ANGEL_WD_API_TOKEN', "")
    api_token = f'Token {token}'
    return {'Content-Type': 'application/json', 'Authorization': api_token}

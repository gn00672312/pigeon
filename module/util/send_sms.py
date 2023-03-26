'''

This sending SMS module is based on: http://www.kotsms.com.tw/index.php?selectpage=pagenews&kind=4&viewnum=238

'''

import os
import requests

from urllib.parse import parse_qsl

from module import log


SEND_API_URL = 'https://api2.kotsms.com.tw/kotsmsapi-1.php'
GET_POINTS_API_URL = 'https://api.kotsms.com.tw/memberpoint.php'

ERROR_MSGS = {
    -1: "CGI string error ，系統維護中或其他錯誤 ,帶入的參數異常,伺服器異常",
    -2: "授權錯誤(帳號/密碼錯誤)",
    -4: "A Number違反規則 發送端 870短碼VCSN 設定異常",
    -5: "B Number違反規則 接收端 門號錯誤 ",
    -6: "Closed User 接收端的門號停話異常090 094 099 付費代號等",
    -20: "Schedule Time錯誤 預約時間錯誤 或時間已過",
    -21: "Valid Time錯誤 有效時間錯誤",
    -1000: "發送內容違反NCC規範",
    -59999: "帳務系統異常 簡訊無法扣款送出",
    -60002: "您帳戶中的點數不足",
    -60014: "該用戶已申請 拒收簡訊平台之簡訊 ( 2010 NCC新規)",
    -999949999: "境外IP限制(只接受台灣IP發送，欲申請過濾請洽簡訊王客服)",
    -999959999: "在12 小時內，相同容錯機制碼",
    -999969999: "同秒, 同門號, 同內容簡訊",
    -999979999: "鎖定來源IP",
    -999989999: "簡訊為空"
}


def send(phone_number, message):
    params = {
        'username': os.environ['SMS_USERNAME'],
        'password': os.environ['SMS_PASSWORD'],
        'dstaddr': phone_number,
        'smbody': message.encode('big5'),
        'dlvtime': 0,
        'vldtime': 1800
    }
    if len(phone_number) not in [10, 12]:
        raise Exception(f'Invalid phone number format: {phone_number}')

    res = requests.get(SEND_API_URL, params=params)
    res = dict(parse_qsl(res.text))
    res_code = res.get('kmsgid', 0)
    res_code = int(res_code)

    if res_code <= 0:
        raise Exception(f'Send sms to <{phone_number} failed. Error: {ERROR_MSGS.get(res_code, "UNKNOWN")}')
    else:
        log.event(f'Send sms to <{phone_number} successful.')


def get_points():
    params = {
        'username': os.environ['SMS_USERNAME'],
        'password': os.environ['SMS_PASSWORD'],
    }

    res = requests.get(GET_POINTS_API_URL, params=params)
    points = int(res.text)
    if points == -2:
        raise Exception('username or password error')
    elif points < 0:
        raise Exception('unknown error')

    return points

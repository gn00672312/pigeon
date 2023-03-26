import os
import requests
import xml.etree.ElementTree as ET


# 中華民國內政部國土測繪中心
# 這個 url 不會常變, 也沒有替代品, 不需要寫到 settings
NLSC_TOWN_API_URL = 'https://api.nlsc.gov.tw/other/TownVillagePointQuery/'


def latlon2citytown(lat, lon):
    area_api_url = f"{NLSC_TOWN_API_URL}{lon}/{lat}"

    response = requests.get(area_api_url)
    if not response.content:
        return None

    result = response.content.decode('utf8')
    root = ET.fromstring(result)
    result_content = list(root)

    city_name = town_name = None
    for content in result_content:
        if content.tag == 'ctyName':
            city_name = content.text

        elif content.tag == 'townName':
            town_name = content.text

    if city_name is None or town_name is None:
        return None, None, None

    city_name = trans_cht(city_name)
    area_name = city_name + town_name

    return city_name, town_name, area_name


def trans_cht(word):
    return word.replace('臺', '台')


def location2latlon(location=None):
    # 需要時再載入就好
    # 有問題 (例如沒有 googlemaps) 是使用者的問題
    try:
        import googlemaps
        GOOGLE_MAP_API = os.environ["GOOGLE_MAP_API"]

        if location is None or not isinstance(location, str):
            return None

        gm = googlemaps.Client(key=GOOGLE_MAP_API)

        location_info = gm.geocode(location)
        if len(location_info) == 0:
            return None

        latlng_info = location_info[0]['geometry']['location']
        latlng_info['lon'] = latlng_info.pop('lng')
        return latlng_info

    except NameError as e:
        # name 'googlemaps' is not defined
        raise e
    except ValueError as e:
        # Invalid API key provided.
        raise e
    except:
        raise Exception("Invalid location: %s" % location)

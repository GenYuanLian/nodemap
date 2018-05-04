import logging
import requests
import googlemaps
from bitcoin.rpc import Proxy

from django.conf import settings

from .exceptions import APIRequestError

log = logging.getLogger(__name__)


def geo_coder_by_baidu_map(country, province, city):
    """
    通过地址信息获取经纬度数据并返回（基于百度地图）

    若未查询到，默认返回(0, 0)

    配额说明：
        http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding
        未认证用户日配额6000次/天，分钟并发数3000次/分钟（即50次/秒）

    :param country: 国
    :param province: 省
    :param city: 市
    :return: (longitude, latitude)
    """
    longitude, latitude = 0, 0
    response = requests.get(
        url='http://api.map.baidu.com/geocoder',
        params={
            'address': ' '.join([
                country, province, city]),
            'output': 'json',
        })

    response_json = response.json()
    log.info('获取经纬度信息返回结果(百度地图)：{}'.format(response_json))

    result = response_json.get('result', {})
    if result == []:
        return longitude, latitude

    location = result.get('location', {})
    if location:
        longitude = location.get('lng', longitude)
        latitude = location.get('lat', latitude)

    return longitude, latitude


def geo_coder_by_google_map(country, province, city):
    """
    通过地址信息获取经纬度数据并返回（基于谷歌地图）

    若未查询到，默认返回(0, 0)

    配额说明：
        https://developers.google.com/maps/documentation/geocoding/usage-limits?hl=zh-cn
        标准API的用户配额2500次/天，分钟并发数50次/秒

    :param country: 国
    :param province: 省
    :param city: 市
    :return: (longitude, latitude)
    """
    longitude, latitude = 0, 0
    key = settings.GOOGLE_MAPS_API_KEY
    if key == '':
        return longitude, latitude
    gmaps = googlemaps.Client(key=key)
    geocode_result = gmaps.geocode(
        address=' '.join([country, province, city]),
        language='zh-CN')
    log.info('获取经纬度信息返回结果(谷歌地图)：{}'.format(geocode_result))

    if len(geocode_result) > 0:
        location = geocode_result[0].get('geometry', {}).get('location', {})
        if location:
            longitude = location.get('lng', longitude)
            latitude = location.get('lat', latitude)

    return longitude, latitude


def get_ip_info_by_taobao(addr):
    """
    通过ip地址获取三级地理位置信息(淘宝IP地址库)

    配额说明：
        http://ip.taobao.com/restrictions.php
        为了保障服务正常运行，每个用户的访问频率需小于10qps

    :param addr: IP地址字串
    :return: (country, region, city)
    """
    country, region, city = '', '', ''
    response = requests.get(
        url='http://ip.taobao.com/service/getIpInfo.php',
        params={
            'ip': addr,
        })

    response_json = response.json()
    log.info('获取地理名称信息返回结果：{}'.format(response_json))

    code = response_json.get('code', 1)
    data = response_json.get('data', {})
    if code == 0 and data:
        country = data.get('country', country)
        region = data.get('region', region)
        city = data.get('city', city)

    if code == 1 or country == '':
        raise APIRequestError('获取地理名称信息失败：{}', response_json)

    return country, region, city


def get_ip_info_by_ipip(addr):
    """
    通过ip地址获取三级地理位置信息(ipip的IP地址库)

    配额说明：
        https://www.ipip.net/api.html
        免费接口（限速每天1000次，仅供测试）

    :param addr: IP地址字串
    :return: (country, region, city)
    """
    country, region, city = '', '', ''
    response = requests.get(
        url='http://freeapi.ipip.net/{ip}'.format(
            ip=addr))

    response_json = response.json()
    log.info('获取地理名称信息返回结果：{}'.format(response_json))

    rc_len = len(response_json)
    if rc_len > 3:
        country = response_json[0]
        region = response_json[1]
        city = response_json[2]

    return country, region, city


def get_peer_info_from_bitcoin_rpc():
    """
    通过比特币RPC接口获取端点信息列表

    :return: [] 包含端点信息的列表
    """
    rpc = Proxy(btc_conf_file=settings.BTC_CONF_FILE)
    result = rpc.call('getpeerinfo')
    log.info('获取端点信息返回结果：{}'.format(result))
    print('获取端点信息返回结果：{}'.format(result))
    return result


geo_coder = geo_coder_by_google_map
get_ip_info = get_ip_info_by_ipip
get_peer_info = get_peer_info_from_bitcoin_rpc

from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from celery import group

from django.db.models import Count

from .utils import geo_coder
from .utils import get_ip_info
from .utils import get_peer_info

from .models import NodeData
from .models import PeerInfo

from .exceptions import APIRequestError

from restapi.serializers import PeerInfoSerializer

from requests.exceptions import ConnectionError

log = logging.getLogger(__name__)


@shared_task(
    rate_limit='40/s',
    autoretry_for=(ConnectionError,),
    retry_backoff=True)
def fetch_geo_info(nodedata_pk):
    """
    获取地理信息

    此处task考虑较为保守的速率限制，40次每秒，Google Maps的限制为50次每秒
    """
    node = NodeData.objects.get(pk=nodedata_pk)
    node.longitude, node.latitude = geo_coder(
        node.country, node.province, node.city)
    if all([
        node.longitude,
        node.latitude
    ]):
        node.save()


@shared_task(
    rate_limit='2/s',
    autoretry_for=(ConnectionError,),
    retry_backoff=True)
def fetch_ip_info(peerinfo_pk):
    """
    获取IP信息

    根据IP地址字串获取相应的三级行政区划信息

    此处task考虑较为保守的速率限制，6次每秒，淘宝IP地址库限制为10次每秒
    """
    peer = PeerInfo.objects.get(pk=peerinfo_pk)
    try:
        country, region, city = get_ip_info(peer.addr.split(':')[0])
    except APIRequestError as e:
        log.error(e)
        return

    node, created = NodeData.objects.get_or_create(
        country=country,
        province=region,
        city=city)
    if created:
        node.save()
    peer.nodedata = node
    peer.save()


@shared_task
def update_nodedata_count():
    """
    更新节点数据中的节点数数据
    """
    nodes = NodeData.objects.annotate(Count('peerinfo'))
    for node in nodes:
        node.count = node.peerinfo__count
        node.save()


@shared_task
def update_nodemap_data():
    """
    更新节点地图数据

    此方法作为入口心跳任务，以固定间隔时间周期执行

    主要工作为通过RPC通道更新 `PeerInfo` 数据模型（保存时创建/更新 `NodeData` 数据模型，
    并完成外链），以上工作完成后，调用 `update_nodedata_count` 任务，
    更新 `NodeData` 模型中的节点数数据
    """
    # 通过RPC接口获取端点信息列表并更新到数据库中
    peer_info = get_peer_info()
    peer_serializer = PeerInfoSerializer(
        data=peer_info, many=True)
    if not peer_serializer.is_valid():
        log.error('序列化BTC RPC返回数据错误：{}'.format(peer_serializer.errors))
        return
    log.debug('设置Peer信息API序列化器合法验证通过')
    peer_serializer.save()
    log.debug('设置Peer信息API序列化器保存完毕')

    # 创建Work-flows，对所有 `nodedata` 为空的 `PeerInfo` 对象
    # 异步调用 `fetch_ip_info` 任务，并 chord 连接 `update_nodedata_count` 任务
    peers = PeerInfo.objects.filter(nodedata__isnull=True)
    c = (group(
        fetch_ip_info.s(peer.pk) for peer in peers
    ) | update_nodedata_count.si())
    c.delay()

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from node.models import NodeData
from .serializers import NodeDataSerializer
from .serializers import PeerInfoSerializer

log = logging.getLogger(__name__)


class NodesView(APIView):
    """
    ## 节点数据接口

    用于获取所有节点的数据数组
    """
    def get(self, request, format=None):
        nodes_obj = NodeData.objects.filter(
            count__gt=0,
            longitude__isnull=False,
            latitude__isnull=False)
        nodes_data_list = NodeDataSerializer(nodes_obj, many=True)
        log.debug('查询结果：{}'.format(nodes_data_list.data))
        return Response(
            nodes_data_list.data,
            status=status.HTTP_200_OK)


class PeersView(APIView):
    """
    ## 设置Peer信息接口

    添加或更新Peer信息到DB
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        peer_serializer = PeerInfoSerializer(
            data=request.data, many=True)
        if peer_serializer.is_valid():
            log.debug('设置Peer信息API序列化器合法验证通过')
            peer_serializer.save()
            log.debug('设置Peer信息API序列化器保存完毕')
            from node import tasks
            tasks.update_nodemap_data.delay()
            return Response(
                peer_serializer.data,
                status=status.HTTP_200_OK)
        log.debug('设置Peer信息API序列化器合法验证失败')
        return Response(
            peer_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

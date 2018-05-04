import logging

from rest_framework import serializers

from node.constants import PLACENAME_TRANS
from node.models import NodeData
from node.models import PeerInfo

log = logging.getLogger(__name__)


class NodeDataSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        """对三级地名进行翻译"""
        ret = super().to_representation(instance)
        country = ret.get('country', '')
        province = ret.get('province', '')
        city = ret.get('city', '')
        ret['country'] = PLACENAME_TRANS.get(country, country)
        ret['province'] = PLACENAME_TRANS.get(province, province)
        ret['city'] = PLACENAME_TRANS.get(city, city)
        return ret

    class Meta:
        model = NodeData
        exclude = ('id', 'last_updated',)


class PeerInfoSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        """对传入的data进行修饰处理"""
        data['addr'] = data.get('addr', '').split(':')[0]
        ret = super().to_internal_value(data)
        return ret

    def create(self, validated_data):
        try:
            peer = PeerInfo.objects.get(addr=validated_data.get('addr', ''))
            return super().update(peer, validated_data)
        except PeerInfo.DoesNotExist:
            return super().create(validated_data)

    class Meta:
        model = PeerInfo
        exclude = ('id', 'last_updated',)
        extra_kwargs = {
            'addr': {
                'validators': []
            }
        }

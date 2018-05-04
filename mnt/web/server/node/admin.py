from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import *
from node import tasks
from celery import group


class NodeDataAdmin(admin.ModelAdmin):
    list_display = (
        'country', 'province', 'city',
        'count', 'longitude', 'latitude')
    search_fields = [
        'country', 'province', 'city']
    readonly_fields = (
        'last_updated',)


class PeerInfoAdmin(admin.ModelAdmin):
    list_display = (
        'addr', 'lastsend', 'lastrecv',
        'conntime', 'pingtime', 'minping',
        'inbound', 'nodedata')
    search_fields = [
        'addr', 'nodedata__country', 'nodedata__province', 'nodedata__city']
    readonly_fields = (
        'addr', 'lastsend', 'lastrecv',
        'conntime',
        'timeoffset', 'pingtime', 'minping',
        'version', 'subver', 'inbound',
        'startingheight', 'last_updated')
    actions = [
        'action_fetch_ip_info',
        'action_update_nodedata_count']

    def action_fetch_ip_info(self, request, queryset):
        """异步获取IP信息"""
        c = (group(
            tasks.fetch_ip_info.s(peer.pk) for peer in queryset
        ))
        c.delay()
        self.message_user(
            request,
            _('共处理 {num} 条 Peer 数据').format(
                num=len(queryset)))

    def action_update_nodedata_count(self, request, queryset):
        """同步更新所有地理地点的节点数"""
        tasks.update_nodedata_count()
        self.message_user(
            request,
            _('更新节点数成功！'))

    action_fetch_ip_info.short_description = _('获取IP地址信息')
    action_update_nodedata_count.short_description = _('更新节点数')


admin.site.register(NodeData, NodeDataAdmin)
admin.site.register(PeerInfo, PeerInfoAdmin)

from django.db import models
from django.utils.translation import gettext_lazy as _


class NodeData(models.Model):
    """
    节点数据模型，用来为RESTAPI提供数据填充
    """

    country = models.CharField(
        verbose_name=_('国'),
        max_length=255)
    province = models.CharField(
        verbose_name=_('省'),
        blank=True,
        default='',
        max_length=255)
    city = models.CharField(
        verbose_name=_('市'),
        blank=True,
        default='',
        max_length=255)
    count = models.IntegerField(
        verbose_name=_('节点数'),
        default=0)
    longitude = models.FloatField(
        verbose_name=_('经度'),
        blank=True,
        null=True,
        default=None,
        help_text=_('若保存时为空将自动从网络查询并填写'))
    latitude = models.FloatField(
        verbose_name=_('纬度'),
        blank=True,
        null=True,
        default=None,
        help_text=_('若保存时为空将自动从网络查询并填写'))

    last_updated = models.DateTimeField(
        verbose_name=_('最后更新'),
        auto_now=True)

    def __str__(self):
        output = [self.country, self.province, self.city]
        output = [s for s in output if s != '']
        return '-'.join(output)

    class Meta:
        verbose_name = _('节点数据')
        verbose_name_plural = verbose_name
        unique_together = (
            ('country', 'province', 'city'),
        )

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        from node import tasks
        super(NodeData, self).save(
            force_insert, force_update, using, update_fields)
        if not all([
            self.longitude,
            self.latitude
        ]):
            tasks.fetch_geo_info.delay(self.pk)


class PeerInfo(models.Model):
    """
    端点信息模型，保存所有已知端点的数据信息，用以更新节点数据
    """

    addr = models.CharField(
        verbose_name=_('远端地址'),
        help_text=_('远端节点的IP地址'),
        unique=True,
        max_length=15)
    lastsend = models.IntegerField(
        verbose_name=_('最后发送时间'),
        help_text=_('最后一次成功发送数据到这个节点TCP socket的Unix epoch时间'))
    lastrecv = models.IntegerField(
        verbose_name=_('最后接收时间'),
        help_text=_('最后一次从这个节点接收数据的Unix epoch时间'))
    conntime = models.IntegerField(
        verbose_name=_('连接时间'),
        help_text=_('连接到这个节点时的Unix epoch时间'))
    timeoffset = models.IntegerField(
        verbose_name=_('时间偏移'),
        help_text=_('以秒为单位的时间偏移'))
    pingtime = models.FloatField(
        verbose_name=_('Ping时间'),
        help_text=_('该节点最后一次响应我们的P2P ping消息的秒数'))
    minping = models.FloatField(
        verbose_name=_('最短Ping时间'),
        blank=True,
        null=True,
        default=None,
        help_text=_('观测到的最短Ping时间（如果有的话）'))
    version = models.IntegerField(
        verbose_name=_('版本号'),
        help_text=_('该节点使用的协议版本号'))
    subver = models.CharField(
        verbose_name=_('子版本号'),
        help_text=_('该节点在它的version消息中发送的用户代理'),
        max_length=255)
    inbound = models.BooleanField(
        verbose_name=_('入站'),
        help_text=_('如果该节点连接到我们，设为True；如果我们连接到这个节点，设为False'))
    startingheight = models.IntegerField(
        verbose_name=_('起始高度'),
        help_text=_('当它连接到我们时，在其version消息中报告的远端节点的区块链高度'))
    nodedata = models.ForeignKey(
        'NodeData',
        verbose_name=_('节点数据'),
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL)

    last_updated = models.DateTimeField(
        verbose_name=_('最后更新'),
        auto_now=True)

    def __str__(self):
        return '端点[{addr}]'.format(
            addr=self.addr)

    class Meta:
        verbose_name = _('端点信息')
        verbose_name_plural = verbose_name

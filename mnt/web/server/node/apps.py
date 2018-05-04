from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NodeConfig(AppConfig):
    name = 'node'
    verbose_name = _('节点组件')

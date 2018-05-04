from django.conf import settings
from django.urls import path, include

from rest_framework import routers

from .views import NodesView
from .views import PeersView


router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]

search_urls = [
    path('nodes', NodesView.as_view(), name='nodes'),
]

peer_urls = [
    path('peers', PeersView.as_view(), name='peers'),
]

urlpatterns += search_urls

# 仅在调试环境下配置此urls
if settings.DEBUG:
    urlpatterns += peer_urls

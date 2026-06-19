from django.urls import re_path

from .views import (
    ShareDownloadView, ShareManageView, SharePublicView
)


urlpatterns = [
    re_path(
        route=r'^manage/(?P<target_type>document|cabinet)/(?P<target_id>\d+)/$',
        name='share_manage', view=ShareManageView.as_view()
    ),
    re_path(
        route=r'^s/(?P<token>[0-9a-f-]+)/$',
        name='share_public', view=SharePublicView.as_view()
    ),
    re_path(
        route=r'^s/(?P<token>[0-9a-f-]+)/files/(?P<document_file_id>\d+)/(?P<mode>view|download)/$',
        name='share_file', view=ShareDownloadView.as_view()
    ),
]

from django.utils.translation import gettext_lazy as _

from mayan.apps.common.apps import MayanAppConfig


class ExternalSharingApp(MayanAppConfig):
    app_namespace = 'external_sharing'
    app_url = 'external_sharing'
    name = 'mayan.apps.external_sharing'
    verbose_name = _('External sharing')

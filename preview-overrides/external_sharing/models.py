import uuid

from django.apps import apps
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ExternalShare(models.Model):
    TARGET_DOCUMENT = 'document'
    TARGET_CABINET = 'cabinet'
    TARGET_CHOICES = (
        (TARGET_DOCUMENT, _('Document')),
        (TARGET_CABINET, _('Cabinet')),
    )

    PERMISSION_VIEW = 'view'
    PERMISSION_DOWNLOAD = 'download'
    PERMISSION_CHOICES = (
        (PERMISSION_VIEW, _('View only')),
        (PERMISSION_DOWNLOAD, _('View and download')),
    )

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Token'))
    target_type = models.CharField(choices=TARGET_CHOICES, db_index=True, max_length=32, verbose_name=_('Target type'))
    target_id = models.PositiveIntegerField(db_index=True, verbose_name=_('Target ID'))
    permission = models.CharField(choices=PERMISSION_CHOICES, default=PERMISSION_VIEW, max_length=16, verbose_name=_('Permission'))
    password_hash = models.CharField(blank=True, max_length=128, verbose_name=_('Password hash'))
    expires_at = models.DateTimeField(blank=True, db_index=True, null=True, verbose_name=_('Expires at'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    label = models.CharField(blank=True, max_length=255, verbose_name=_('Label'))
    creator = models.ForeignKey(
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='external_shares', to='auth.User', verbose_name=_('Creator')
    )
    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created'))

    class Meta:
        ordering = ('-datetime_created',)
        verbose_name = _('External share')
        verbose_name_plural = _('External shares')

    def __str__(self):
        return self.label or '{} #{}'.format(self.get_target_type_display(), self.target_id)

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    @property
    def is_usable(self):
        return self.is_active and not self.is_expired

    @property
    def password_required(self):
        return bool(self.password_hash)

    @property
    def can_download(self):
        return self.permission == self.PERMISSION_DOWNLOAD

    def check_password(self, password):
        if not self.password_required:
            return True
        return check_password(password=password or '', encoded=self.password_hash)

    def get_absolute_url(self):
        return reverse('external_sharing:share_public', kwargs={'token': self.token})

    def get_target(self):
        if self.target_type == self.TARGET_DOCUMENT:
            model = apps.get_model(app_label='documents', model_name='Document')
            return model.valid.get(pk=self.target_id)
        if self.target_type == self.TARGET_CABINET:
            model = apps.get_model(app_label='cabinets', model_name='Cabinet')
            return model.objects.get(pk=self.target_id)
        raise ValueError('Unsupported share target type: {}'.format(self.target_type))

    def set_password(self, password):
        self.password_hash = make_password(password=password) if password else ''

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import ExternalShare


class ExternalShareForm(forms.ModelForm):
    password = forms.CharField(
        help_text=_('Optional. Leave empty to allow access without a password.'),
        label=_('Password'), required=False, widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password'}
        )
    )
    expires_at = forms.DateTimeField(
        help_text=_('Optional. The link stops working after this date and time.'),
        input_formats=('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'),
        label=_('Expiration time'), required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    class Meta:
        fields = ('label', 'permission', 'password', 'expires_at', 'is_active')
        model = ExternalShare

    def clean_expires_at(self):
        value = self.cleaned_data['expires_at']
        if value and timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(password=self.cleaned_data.get('password'))
        if commit:
            instance.save()
        return instance


class SharePasswordForm(forms.Form):
    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput(attrs={'autofocus': 'autofocus'})
    )

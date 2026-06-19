from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone, translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.i18n import JavaScriptCatalog

from stronghold.views import StrongholdPublicMixin

from mayan.apps.user_management.permissions import (
    permission_user_edit, permission_user_view
)
from mayan.apps.user_management.querysets import get_user_queryset
from mayan.apps.user_management.views.view_mixins import (
    DynamicExternalUserViewMixin
)
from mayan.apps.views.generics import (
    SingleObjectDetailView, SingleObjectEditView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from .forms import LocaleProfileForm, LocaleProfileForm_view
from .icons import (
    icon_user_locale_profile_detail, icon_user_locale_profile_edit
)
from .models import UserLocaleProfile


class JavaScriptCatalogPublic(StrongholdPublicMixin, JavaScriptCatalog):
    """
    Sub class of `JavaScriptCatalog` to bypass authentication and avoid
    JavaScript errors for non authentication users.
    """


class PreviewSetLanguageView(StrongholdPublicMixin, View):
    allowed_languages = {'ar', 'en', 'fr'}

    def get(self, request, *args, **kwargs):
        language = request.GET.get('language') or request.POST.get('language')
        next_url = request.GET.get('next') or request.POST.get('next') or '/'

        if language not in self.allowed_languages:
            language = 'en'

        translation.activate(language=language)

        if getattr(request, 'user', None) and request.user.is_authenticated:
            locale_profile, created = UserLocaleProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'language': language,
                    'timezone': timezone.get_current_timezone_name()
                }
            )
            if not created:
                locale_profile.language = language
                locale_profile.save(update_fields=('language',))

        if not url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}
        ):
            next_url = '/'

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            response = JsonResponse(data={'language': language})
        else:
            response = redirect(to=next_url)

        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME, value=language,
            max_age=60 * 60 * 24 * 365, path='/',
            samesite='Lax'
        )

        return response

    def post(self, request, *args, **kwargs):
        return self.get(request=request, *args, **kwargs)


class UserLocaleProfileDetailView(
    DynamicExternalUserViewMixin, ExternalObjectViewMixin,
    SingleObjectDetailView
):
    form_class = LocaleProfileForm_view
    external_object_permission = permission_user_view
    external_object_pk_url_kwarg = 'user_id'
    view_icon = icon_user_locale_profile_detail

    def get_external_object_queryset(self):
        return get_user_queryset(user=self.request.user)

    def get_extra_context(self, **kwargs):
        return {
            'form': LocaleProfileForm_view(
                instance=self.external_object.locale_profile
            ),
            'object': self.external_object,
            'read_only': True,
            'title': _(
                message='Locale profile for user: %s'
            ) % self.external_object
        }

    def get_object(self):
        return self.external_object.locale_profile


class UserLocaleProfileEditView(
    DynamicExternalUserViewMixin, ExternalObjectViewMixin,
    SingleObjectEditView
):
    form_class = LocaleProfileForm
    external_object_permission = permission_user_edit
    external_object_pk_url_kwarg = 'user_id'
    view_icon = icon_user_locale_profile_edit

    def form_valid(self, form):
        if self.is_current_user:
            language_value = form.cleaned_data['language']
            timezone_value = form.cleaned_data['timezone']

            timezone.activate(timezone=timezone_value)
            translation.activate(language=language_value)

        return super().form_valid(form=form)

    def get_external_object_queryset(self):
        return get_user_queryset(user=self.request.user)

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(
                message='Edit locale profile for user: %s'
            ) % self.external_object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_object(self):
        return self.external_object.locale_profile

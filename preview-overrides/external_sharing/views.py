from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from stronghold.views import StrongholdPublicMixin

from mayan.apps.acls.models import AccessControlList
from mayan.apps.cabinets.models import Cabinet
from mayan.apps.cabinets.permissions import permission_cabinet_view
from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view

from .forms import ExternalShareForm, SharePasswordForm
from .models import ExternalShare


def user_can_manage_target(user, target):
    permission = permission_document_view if isinstance(target, Document) else permission_cabinet_view
    AccessControlList.objects.check_access(
        obj=target, permission=permission, user=user
    )


def get_target_or_404(target_type, target_id):
    if target_type == ExternalShare.TARGET_DOCUMENT:
        return get_object_or_404(Document.valid.all(), pk=target_id)
    if target_type == ExternalShare.TARGET_CABINET:
        return get_object_or_404(Cabinet.objects.all(), pk=target_id)
    raise Http404


def get_document_files_for_share(share):
    target = share.get_target()
    if share.target_type == ExternalShare.TARGET_DOCUMENT:
        return target.files.order_by('-timestamp'), target

    cabinet_tree = target.get_descendants(include_self=True)
    documents = Document.valid.filter(cabinets__in=cabinet_tree).distinct()
    return DocumentFile.valid.filter(document__in=documents).order_by('document__label', '-timestamp'), target


class ShareManageView(View):
    template_name = 'external_sharing/manage.html'

    def dispatch(self, request, *args, **kwargs):
        self.target = get_target_or_404(
            target_type=kwargs['target_type'], target_id=kwargs['target_id']
        )
        user_can_manage_target(user=request.user, target=self.target)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ExternalShare.objects.filter(
            target_type=self.kwargs['target_type'],
            target_id=self.kwargs['target_id']
        )

    def get(self, request, *args, **kwargs):
        return self.render(form=ExternalShareForm())

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        share_id = request.POST.get('share_id')

        if action and share_id:
            share = get_object_or_404(self.get_queryset(), pk=share_id)
            if action == 'delete':
                share.delete()
                messages.success(request, _('External share deleted.'))
            elif action == 'toggle':
                share.is_active = not share.is_active
                share.save(update_fields=('is_active',))
                messages.success(request, _('External share updated.'))
            return HttpResponseRedirect(request.path)

        form = ExternalShareForm(data=request.POST)
        if form.is_valid():
            share = form.save(commit=False)
            share.target_type = self.kwargs['target_type']
            share.target_id = self.kwargs['target_id']
            share.creator = request.user
            share.save()
            messages.success(request, _('External share created.'))
            return HttpResponseRedirect(request.path)

        return self.render(form=form)

    def render(self, form):
        return render(
            request=self.request, template_name=self.template_name, context={
                'form': form,
                'shares': self.get_queryset(),
                'target': self.target,
                'target_type': self.kwargs['target_type']
            }
        )


class ShareAccessMixin:
    def get_share(self):
        return get_object_or_404(ExternalShare, token=self.kwargs['token'])

    def session_key(self, share):
        return 'external_share_{}_password_ok'.format(share.pk)

    def password_ok(self, request, share):
        return not share.password_required or request.session.get(self.session_key(share))

    def require_usable_share(self, share):
        if not share.is_usable:
            raise Http404(_('This share link is no longer available.'))


class SharePublicView(StrongholdPublicMixin, ShareAccessMixin, View):
    template_name = 'external_sharing/public.html'

    def get(self, request, *args, **kwargs):
        share = self.get_share()
        self.require_usable_share(share=share)

        if not self.password_ok(request=request, share=share):
            return render(
                request=request, template_name=self.template_name, context={
                    'form': SharePasswordForm(), 'needs_password': True,
                    'share': share
                }
            )

        files, target = get_document_files_for_share(share=share)
        return render(
            request=request, template_name=self.template_name, context={
                'files': files, 'share': share, 'target': target
            }
        )

    def post(self, request, *args, **kwargs):
        share = self.get_share()
        self.require_usable_share(share=share)
        form = SharePasswordForm(data=request.POST)
        if form.is_valid() and share.check_password(form.cleaned_data['password']):
            request.session[self.session_key(share)] = True
            return HttpResponseRedirect(
                reverse('external_sharing:share_public', kwargs={'token': share.token})
            )

        form.add_error('password', _('Invalid password.'))
        return render(
            request=request, template_name=self.template_name, context={
                'form': form, 'needs_password': True, 'share': share
            }
        )


class ShareDownloadView(StrongholdPublicMixin, ShareAccessMixin, View):
    def get(self, request, *args, **kwargs):
        share = self.get_share()
        self.require_usable_share(share=share)

        if not self.password_ok(request=request, share=share):
            return HttpResponseRedirect(
                reverse('external_sharing:share_public', kwargs={'token': share.token})
            )

        mode = kwargs['mode']
        if mode == 'download' and not share.can_download:
            raise PermissionDenied

        document_file = get_object_or_404(DocumentFile.valid.all(), pk=kwargs['document_file_id'])
        target = share.get_target()
        if share.target_type == ExternalShare.TARGET_DOCUMENT:
            if document_file.document_id != target.pk:
                raise Http404
        elif share.target_type == ExternalShare.TARGET_CABINET:
            cabinet_tree = target.get_descendants(include_self=True)
            if not Document.valid.filter(
                cabinets__in=cabinet_tree, pk=document_file.document_id
            ).exists():
                raise Http404
        else:
            raise Http404

        return FileResponse(
            as_attachment=(mode == 'download'),
            filename=document_file.filename,
            streaming_content=document_file.get_download_file_object(),
            content_type=document_file.mimetype or 'application/octet-stream'
        )

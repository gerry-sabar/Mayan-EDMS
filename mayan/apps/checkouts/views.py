from __future__ import absolute_import, unicode_literals

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _, ungettext

from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.generics import (
    ConfirmView, MultipleObjectConfirmActionView, MultipleObjectFormActionView,
    SingleObjectCreateView, SingleObjectDetailView
)
from mayan.apps.common.utils import encapsulate
from mayan.apps.documents.models import Document
from mayan.apps.documents.views import DocumentListView

from .exceptions import DocumentAlreadyCheckedOut, DocumentNotCheckedOut
from .forms import DocumentCheckoutForm, DocumentCheckoutDefailForm
from .icons import icon_check_out_info
from .models import DocumentCheckout
from .permissions import (
    permission_document_check_in, permission_document_check_in_override,
    permission_document_check_out, permission_document_check_out_detail_view
)


"""
class DocumentCheckinView(ConfirmView):
    def get_extra_context(self):
        document = self.get_object()

        context = {
            'object': document,
        }

        if document.get_check_out_info().user != self.request.user:
            context['title'] = _(
                'You didn\'t originally checked out this document. '
                'Forcefully check in the document: %s?'
            ) % document
        else:
            context['title'] = _('Check in the document: %s?') % document

        return context

    def get_object(self):
        return get_object_or_404(klass=Document, pk=self.kwargs['pk'])

    def get_post_action_redirect(self):
        return reverse(
            viewname='checkouts:check_out_info', kwargs={
                'pk': self.get_object().pk
            }
        )

    def view_action(self):
        document = self.get_object()

        if document.get_check_out_info().user == self.request.user:
            AccessControlList.objects.check_access(
                obj=document, permissions=(permission_document_check_in,),
                user=self.request.user
            )
        else:
            AccessControlList.objects.check_access(
                obj=document,
                permissions=(permission_document_check_in_override,),
                user=self.request.user
            )

        try:
            document.check_in(user=self.request.user)
        except DocumentNotCheckedOut:
            messages.error(
                message=_('Document has not been checked out.'),
                request=self.request
            )
        else:
            messages.success(
                message=_(
                    'Document "%s" checked in successfully.'
                ) % document, request=self.request
            )
"""

class DocumentCheckinView(MultipleObjectConfirmActionView):
    error_message = 'Unable to check in document "%(instance)s". %(exception)s'
    model = Document
    object_permission = permission_document_check_in
    pk_url_kwarg = 'pk'
    success_message_singular = '%(count)d document checked in.'
    success_message_plural = '%(count)d documents checked in.'

    def get_extra_context(self):
        queryset = self.get_object_list()

        result = {
            'title': ungettext(
                singular='Check in %(count)d document',
                plural='Check in %(count)d documents',
                number=queryset.count()
            ) % {
                'count': queryset.count(),
            }
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        'Check in document: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_post_object_action_url(self):
        if self.action_count == 1:
            return reverse(
                viewname='checkouts:document_checkout_info',
                kwargs={'pk': self.action_id_list[0]}
            )
        else:
            super(DocumentCheckinView, self).get_post_action_redirect()

    def object_action(self, form, instance):
        DocumentCheckout.objects.check_in_document(
            document=instance, user=self.request.user
        )




"""
class CheckoutDocumentView(SingleObjectCreateView):
    form_class = DocumentCheckoutForm

    def dispatch(self, request, *args, **kwargs):
        self.document = get_object_or_404(klass=Document, pk=self.kwargs['pk'])

        AccessControlList.objects.check_access(
            obj=self.document, permissions=(permission_document_check_out,),
            user=request.user
        )

        return super(
            CheckoutDocumentView, self
        ).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            instance = form.save(commit=False)
            instance.user = self.request.user
            instance.document = self.document
            instance.save()
        except DocumentAlreadyCheckedOut:
            messages.error(
                message=_('Document already checked out.'),
                request=self.request
            )
        else:
            messages.success(
                message=_(
                    'Document "%s" checked out successfully.'
                ) % self.document, request=self.request
            )

        return HttpResponseRedirect(redirect_to=self.get_success_url())

    def get_extra_context(self):
        return {
            'object': self.document,
            'title': _('Check out document: %s') % self.document
        }

    def get_post_action_redirect(self):
        return reverse(
            viewname='checkouts:check_out_info', kwargs={
                'pk': self.document.pk
            }
        )
"""
class DocumentCheckoutView(MultipleObjectFormActionView):
    error_message = 'Unable to checkout document "%(instance)s". %(exception)s'
    form_class = DocumentCheckoutForm
    model = Document
    object_permission = permission_document_check_out
    pk_url_kwarg = 'pk'
    success_message_singular = '%(count)d document checked out.'
    success_message_plural = '%(count)d documents checked out.'

    def get_extra_context(self):
        queryset = self.get_object_list()

        result = {
            'title': ungettext(
                singular='Checkout %(count)d document',
                plural='Checkout %(count)d documents',
                number=queryset.count()
            ) % {
                'count': queryset.count(),
            }
        }

        if queryset.count() == 1:
            result.update(
                {
                    'object': queryset.first(),
                    'title': _(
                        'Check out document: %s'
                    ) % queryset.first()
                }
            )

        return result

    def get_post_object_action_url(self):
        if self.action_count == 1:
            return reverse(
                viewname='checkouts:document_checkout_info',
                kwargs={'pk': self.action_id_list[0]}
            )
        else:
            super(DocumentCheckoutView, self).get_post_action_redirect()

    def object_action(self, form, instance):
        DocumentCheckout.objects.check_out_document(
            block_new_version=form.cleaned_data['block_new_version'],
            document=instance,
            expiration_datetime=form.cleaned_data['expiration_datetime'],
            user=self.request.user,
        )


class DocumentCheckoutDetailView(SingleObjectDetailView):
    form_class = DocumentCheckoutDefailForm
    model = Document
    object_permission = permission_document_check_out_detail_view

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(
                'Check out details for document: %s'
            ) % self.object
        }


class DocumentCheckoutListView(DocumentListView):
    def get_document_queryset(self):
        return AccessControlList.objects.restrict_queryset(
            permission=permission_document_check_out_detail_view,
            queryset=DocumentCheckout.objects.checked_out_documents(),
            user=self.request.user
        )

    def get_extra_context(self):
        context = super(DocumentCheckoutListView, self).get_extra_context()
        context.update(
            {
                'extra_columns': (
                    {
                        'name': _('User'),
                        'attribute': encapsulate(
                            lambda document: document.get_check_out_info().user.get_full_name() or document.get_check_out_info().user
                        )
                    },
                    {
                        'name': _('Checkout time and date'),
                        'attribute': encapsulate(
                            lambda document: document.get_check_out_info().checkout_datetime
                        )
                    },
                    {
                        'name': _('Checkout expiration'),
                        'attribute': encapsulate(
                            lambda document: document.get_check_out_info().expiration_datetime
                        )
                    },
                ),
                'no_results_icon': icon_check_out_info,
                'no_results_text': _(
                    'Checking out a document, blocks certain operations '
                    'for a predetermined amount of time.'
                ),
                'no_results_title': _('No documents have been checked out'),
                'title': _('Checked out documents'),
            }
        )
        return context

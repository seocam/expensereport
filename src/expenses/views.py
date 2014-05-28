# *-* coding: utf-8 *-*

from decimal import Decimal
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.encoding import smart_str

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Expense
from .serializers import ExpenseSerializer

import os, zipfile, tempfile


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = (IsAuthenticated,)


@login_required
def dashboard(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
        qs = Expense.objects.filter(attendee_id=user.id)
    else:
        user = None
        qs = Expense.objects

    n_attendees = User.objects.count()
    total_amount = qs.aggregate(Sum('amount'))

    expenses = []
    for expense in qs.all():
        user_link = reverse('expenses:attendee', kwargs={
            'username': expense.attendee.username,
        })
        user_name = expense.attendee.first_name

        expenses.append((
            u'<a href="{}">{}</a>'.format(user_link, user_name),
            expense.amount,
            expense.date,
            expense.get_category_display(),
            expense.description,
            u'<a href="{}">link</a>'.format(expense.receipt.url),
        ))

    by_category = qs.values('category').annotate(Sum('amount')).order_by()
    by_attendee = qs.values('attendee__first_name').\
                                        annotate(Sum('amount')).order_by()
    context = {
        'headers': (
            'Name',
            'Amount (R$)',
            'Date',
            'Category',
            'Description',
            'Receipt',
        ),
        'data': expenses,
        'n_attendees': n_attendees,
        'attendee': user,
        'expense_by_category': by_category,
        'expense_by_attendee': by_attendee,
        'total_amount': total_amount['amount__sum'],
    }

    return render(request, 'dashboard.html', context)

@login_required
def summary(request):

    qs = Expense.objects.values('attendee__first_name')
    qs = qs.annotate(Sum('amount')).order_by()
    qs = qs.values(
        'attendee__paypalaccount__paypal_account',
        'amount__sum',
        'attendee__first_name',
        'attendee__last_name',
        'attendee__username',
    )

    expenses = []
    for expense in qs:
        user_link = reverse('expenses:attendee', kwargs={
            'username': expense['attendee__username'],
        })
        zip_link = 'receipts/' + expense['attendee__first_name']
        user_name = expense['attendee__first_name']
        amount_usd = (expense['amount__sum'] /
                      settings.BRL_USD_RATE *
                      settings.PAYPAL_RATE).quantize(Decimal('1.00'))
        expenses.append((
            u'<a href="{}">{}</a>'.format(user_link, user_name),
            expense['attendee__paypalaccount__paypal_account'],
            expense['amount__sum'],
            amount_usd,
            u'<a href="{}">link</a>'.format(zip_link),
        ))
    n_attendees = User.objects.count()
    total_amount = Expense.objects.aggregate(Sum('amount'))

    context = {
        'headers': (
            'Name',
            'Paypal',
            'Amount (BRL)',
            'Amount (USD)',
            'Receipts (.zip)',
        ),
        'data': expenses,
        'n_attendees': n_attendees,
        'total_amount': total_amount['amount__sum'],
    }
    return render(request, 'summary.html', context)


@login_required
def receipts(request, username=None):

    if username:
        qs = Expense.objects.values('receipt').filter(attendee__first_name = username)
        filename = '-'.join([username, 'receipts.zip'])
        zf = zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED)
        tempdir  = tempfile.mkdtemp()

        for file in qs:
            dir = settings.MEDIA_ROOT + file['receipt']
            zf.write(dir)
        zf.close()

        response = HttpResponse(mimetype='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(filename)
        response['X-Sendfile'] = smart_str(tempdir+filename)

        return response
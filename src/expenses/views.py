# *-* coding: utf-8 *-*

import os
import zipfile
import tempfile

from decimal import Decimal
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Expense
from .serializers import ExpenseSerializer


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
        'attendee__username',
    )

    expenses = []
    for expense in qs:
        user_link = reverse('expenses:attendee', kwargs={
            'username': expense['attendee__username'],
        })
        zip_link = reverse('expenses:receipts', kwargs={
            'username': expense['attendee__username'],
        })

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

    # Get user
    user = get_object_or_404(User, username=username)

    # Check if the user has expenses
    expenses = Expense.objects.filter(attendee_id=user.id)
    if not expenses:
        raise Http404('No Expenses for user {}'.format(user.username))

    # Create zips folder on MEDIA_ROOT
    zips_path = os.path.join(settings.MEDIA_ROOT, 'zips')
    if not os.path.exists(zips_path):
        os.mkdir(zips_path)

    # Gets the file path for the zip that will be created now
    filename = '-'.join([username, 'receipts.zip'])
    file_path = os.path.join(zips_path, filename)

    # Create the zip
    zf = zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED)
    for expense in expenses:
        zf.write(expense.receipt.path, expense.receipt.name)
    zf.close()

    # Redirect to the place where the zip will be hosted
    return redirect(settings.MEDIA_URL + 'zips/' + filename)

# *-* coding: utf-8 *-*

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

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

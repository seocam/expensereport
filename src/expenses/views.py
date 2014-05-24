
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = (IsAuthenticated,)


@login_required
def dashboard(request):
    n_attendees = User.objects.count()
    total_amount = Expense.objects.aggregate(Sum('amount'))
    expense_query = Expense.objects.all()

    expenses = []
    for expense in expense_query:
        expenses.append((
            expense.attendee.first_name,
            expense.amount,
            expense.date,
            expense.get_category_display(),
            expense.description,
            '<a href="{}">link</a>'.format(expense.receipt.url),
        ))

    expense_by_category = Expense.objects.values('category').\
                                          annotate(Sum('amount')).order_by()
    expense_by_attendee = Expense.objects.values('attendee__first_name').\
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
        'expense_by_category': expense_by_category,
        'expense_by_attendee': expense_by_attendee,
        'total_amount': total_amount['amount__sum'],
    }

    return render(request, 'dashboard.html', context)

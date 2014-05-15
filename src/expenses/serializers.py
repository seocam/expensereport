
from django.contrib.auth.models import User

from .models import Expense

from rest_framework import serializers


class ExpenseSerializer(serializers.ModelSerializer):
    user = serializers.Field(source='attendee.first_name')
    receipt = serializers.Field(source='receipt.url')
    paypal = serializers.Field(source=
                              'attendee.paypalaccount_set.first.paypal_account')

    class Meta:
        model = Expense
        fields = (
            'date',
            'amount',
            'description',
            'category',
            'receipt',
            'user',
            'paypal',
        )

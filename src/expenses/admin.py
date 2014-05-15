from django.contrib import admin

from .models import Expense, PaypalAccount


class ExpenseAdmin(admin.ModelAdmin):
    list_filter = ('category', 'attendee__first_name')
    exclude = ('attendee', )

    def save_model(self, request, obj, form, change):
        obj.attendee = request.user
        obj.save()

class PaypalAccountAdmin(admin.ModelAdmin):
    exclude = ('user', )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

admin.site.register(Expense, ExpenseAdmin)
admin.site.register(PaypalAccount, PaypalAccountAdmin)

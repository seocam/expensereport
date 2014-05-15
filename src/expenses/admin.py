from django.contrib import admin

from .models import Expense


class ExpenseAdmin(admin.ModelAdmin):
    list_filter = ('category', 'attendee__first_name')
    exclude = ('attendee', )

    def save_model(self, request, obj, form, change):
        obj.attendee = request.user
        obj.save()


admin.site.register(Expense, ExpenseAdmin)

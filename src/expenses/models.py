import os

from django.db import models
from django.utils.text import slugify

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


def update_to(instance, filename):
    filename, extension = os.path.splitext(filename) 
    user_slug = slugify(instance.attendee.get_full_name())

    filename = '_'.join([unicode(instance.date), user_slug, instance.category])
    return os.path.join(user_slug, filename) + extension


class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('transport-local', _('Local Transportation (Metro/Bus/Taxi)')),
        ('food', _('Food')),
        ('swag', _('Swag')),
        ('hotel', _('Hotel')),
        ('credentials', _('Event Credentials')),
        ('transport-long', _('Long Transportation (Flight/Train/Bus)')),
    )

    date = models.DateField()
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    # currency = ...
    description = models.CharField(max_length=255)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=80)
    receipt = models.ImageField(upload_to=update_to)

    attendee = models.ForeignKey(User)


    def __unicode__(self):
        amount_formatted = u"{0:.2f}".format(self.amount)
        return u'{} spent R${} on {} in {} ({})'.format(
            self.attendee.get_full_name(),
            amount_formatted,
            self.date,
            self.get_category_display(),
            self.description,
        )


class PaypalAccount(models.Model):
    user = models.ForeignKey(User, unique=True)
    paypal_account = models.EmailField()

    def __unicode__(self):
        return u"{} ({})".format(self.paypal_account, self.user.get_full_name())

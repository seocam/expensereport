
from django.conf.urls import url, patterns, include

from rest_framework import routers

from .views import ExpenseViewSet

router = routers.SimpleRouter()
router.register(r'', ExpenseViewSet)


urlpatterns = patterns('',
    url(r'^$', 'expenses.views.dashboard', name='dashboard'),
    url(r'^(?P<username>[\w_@+.-]+)/$', 'expenses.views.dashboard',
        name='attendee'),
    url(r'^api', include(router.urls)),
)

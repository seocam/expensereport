
from django.conf.urls import url, patterns, include

from rest_framework import routers

from .views import ExpenseViewSet

router = routers.SimpleRouter()
router.register(r'', ExpenseViewSet)


urlpatterns = patterns('expenses.views',
    url(r'^$', 'dashboard', name='dashboard'),
    url(r'^summary/$', 'summary', name='summary'),
    url(r'^attendee/(?P<username>[\w_@+.-]+)/$', 'dashboard', name='attendee'),
)

urlpatterns += patterns('',
    url(r'^api', include(router.urls)),
)

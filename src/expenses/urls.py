
from django.conf.urls import url, patterns, include

from rest_framework import routers

from .views import ExpenseViewSet

router = routers.SimpleRouter()
router.register(r'', ExpenseViewSet)


urlpatterns = patterns('',
    url(r'^api', include(router.urls)),
)

from django.conf.urls import patterns, include, url

from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(pattern_name='expenses:dashboard',
                                    permanent=False)),
    url(r'^expense/', include('expenses.urls', namespace='expenses')),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name="login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        name="logout"),


    # Examples:
    # url(r'^$', 'expensereport.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

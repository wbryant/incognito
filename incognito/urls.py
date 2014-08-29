from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'incognito.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^model/$', 'cogzymes.views.model'),
    url(r'^model/id:(?P<model_specified>[^/]+)$', 'cogzymes.views.model'),
    url(r'^home/', 'cogzymes.views.home'),
    url(r'^admin/', include(admin.site.urls)),
)

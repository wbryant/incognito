from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'incognito.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^model/', 'cogzymes.views.model_contents'),
    url(r'^model/id\:(?P<model_id>[^/]+)', 'cogzymes.views.model'),
    url(r'^admin/', include(admin.site.urls)),
)

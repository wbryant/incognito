from django.conf.urls import patterns, include, url
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
import cogzymes.views as cv

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # 
    # url(r'^blog/', include('blog.urls')),
    
    
    url(r'^model/$', 'cogzymes.views.model'),
#     url(r'^model/id:(?P<model_specified>[^/]+)$', cache_page(60 * 15)(cv.model)),
    url(r'^model/id:(?P<model_specified>[^/]+)$', 'cogzymes.views.model'),
    
    url(r'^cog/$', 'cogzymes.views.cog'),
    url(r'^cog/id:(?P<cog_specified>[^/]+)$', 'cogzymes.views.cog'),
    
    url(r'^cogzyme/$', 'cogzymes.views.cogzyme'),
    url(r'^cogzyme/id:(?P<cogzyme_specified>[^/]+)$', 'cogzymes.views.cogzyme'),
    
    url(r'^home/', 'cogzymes.views.home', name='home'),
    url(r'^$', RedirectView.as_view(pattern_name='home')),
    url(r'^admin/', include(admin.site.urls)),
)

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic import RedirectView
from cryptocurry import settings as mysettings
import cryptocurry.utils as cryptoutils


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'/static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': mysettings.STATIC_ROOT}),

)

urlpatterns += patterns('',
    (r'/media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': mysettings.MEDIA_ROOT}),

)

urlpatterns += patterns('',
    # Examples:
    # url(r'^$', 'cryptocurry.views.home', name='home'),
    # url(r'^cryptocurry/', include('cryptocurry.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'cryptocurry/analyze/visual/dsentryiface/$', 'cryptocurry.analysis.views.datasourceentryiface', name='datasourceentryiface'),
    url(r'cryptocurry/analyze/visual/investdata/currencyprice/$', 'cryptocurry.analysis.views.visualize_investdb_currencyprice', name='visualize_investdb_currencyprice'),
    url(r'cryptocurry/analyze/visual/investdata/marketcap/$', 'cryptocurry.analysis.views.visualize_investdb_marketcap', name='visualize_investdb_marketcap'),
    url(r'cryptocurry/analyze/visual/ohlcv/voltraded/$', 'cryptocurry.analysis.views.visualize_ohlcv_voltraded', name='visualize_ohlcv_voltraded'),
    url(r'cryptocurry/analyze/visual/ohlcv/pricehigh/$', 'cryptocurry.analysis.views.visualize_ohlcv_pricehigh', name='visualize_ohlcv_pricehigh'),
    url(r'cryptocurry/analyze/visual/ohlcv/priceclose/$', 'cryptocurry.analysis.views.visualize_ohlcv_priceclose', name='visualize_ohlcv_priceclose'),
    url(r'cryptocurry/analyze/visual/ohlcv/priceopen/$', 'cryptocurry.analysis.views.visualize_ohlcv_priceopen', name='visualize_ohlcv_priceopen'),
    url(r'cryptocurry/analyze/visual/ohlcv/tradescount/$', 'cryptocurry.analysis.views.visualize_ohlcv_tradescount', name='visualize_ohlcv_tradescount'),
)






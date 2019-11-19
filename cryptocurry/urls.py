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
    url(r'cryptocurry/auth/showlogin/$', 'cryptocurry.auth.views.display_login_screen', name='display_login_screen'),
    url(r'cryptocurry/auth/login/$', 'cryptocurry.auth.views.login', name='login'),
    url(r'cryptocurry/analyze/visual/dsentryiface/$', 'cryptocurry.analysis.views.datasourceentryiface', name='datasourceentryiface'),
    url(r'cryptocurry/analyze/visual/investdata/currency_price/$', 'cryptocurry.analysis.views.visualize_investdb_currencyprice', name='visualize_investdb_currencyprice'),
    url(r'cryptocurry/analyze/visual/investdata/market_cap/$', 'cryptocurry.analysis.views.visualize_investdb_marketcap', name='visualize_investdb_marketcap'),
    url(r'cryptocurry/analyze/visual/investdata/volume_24hrs/$', 'cryptocurry.analysis.views.visualize_investdb_vol24hrs', name='visualize_investdb_vol24hrs'),
    url(r'cryptocurry/analyze/visual/investdata/change_24hrs/$', 'cryptocurry.analysis.views.visualize_investdb_change24hrs', name='visualize_investdb_change24hrs'),
    url(r'cryptocurry/analyze/visual/investdata/change_7days/$', 'cryptocurry.analysis.views.visualize_investdb_change7days', name='visualize_investdb_change7days'),
    url(r'cryptocurry/analyze/visual/investdata/total_volume/$', 'cryptocurry.analysis.views.visualize_investdb_totalvolume', name='visualize_investdb_totalvolume'),
    url(r'cryptocurry/analyze/visual/ohlcvdata/volume_traded/$', 'cryptocurry.analysis.views.visualize_ohlcv_voltraded', name='visualize_ohlcv_voltraded'),
    url(r'cryptocurry/analyze/visual/ohlcvdata/price_high/$', 'cryptocurry.analysis.views.visualize_ohlcv_pricehigh', name='visualize_ohlcv_pricehigh'),
    url(r'cryptocurry/analyze/visual/ohlcvdata/price_low/$', 'cryptocurry.analysis.views.visualize_ohlcv_pricelow', name='visualize_ohlcv_pricelow'),
    url(r'cryptocurry/analyze/visual/ohlcvdata/price_close/$', 'cryptocurry.analysis.views.visualize_ohlcv_priceclose', name='visualize_ohlcv_priceclose'),
    url(r'cryptocurry/analyze/visual/ohlcvdata/price_open/$', 'cryptocurry.analysis.views.visualize_ohlcv_priceopen', name='visualize_ohlcv_priceopen'),
    url(r'cryptocurry/analyze/visual/ohlcvdata/trades_count/$', 'cryptocurry.analysis.views.visualize_ohlcv_tradescount', name='visualize_ohlcv_tradescount'),
)






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
    url(r'cryptocurry/analyze/visual/coinmarketdata/currency_price/$', 'cryptocurry.analysis.views.coinmarket_currency_price', name='visualize_coinmarket_currency_price'),
    url(r'cryptocurry/analyze/visual/coinmarketdata/percent_change_24hr/$', 'cryptocurry.analysis.views.coinmarket_percent_change_24hr', name='visualize_coinmarket_percent_change_24hr'),
    url(r'cryptocurry/analyze/visual/coinmarketdata/percent_change_1hr/$', 'cryptocurry.analysis.views.coinmarket_percent_change_1hr', name='visualize_coinmarket_percent_change_1hr	'),
    url(r'cryptocurry/analyze/visual/coinmarketdata/volume_24hr/$', 'cryptocurry.analysis.views.coinmarket_volume_24hr', name='visualize_coinmarket_volume_24hr'),
    url(r'cryptocurry/analyze/visual/coinmarketdata/last_updated/$', 'cryptocurry.analysis.views.coinmarket_last_updated', name='visualize_coinmarket_last_updated'),
    url(r'cryptocurry/analyze/visual/coinmarketdata/percent_change_7days/$', 'cryptocurry.analysis.views.coinmarket_percent_change_7days', name='visualize_coinmarket_percent_change_7days'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/percent7d/$', 'cryptocurry.analysis.views.cmcd_percent07day', name='cmcd_percent07day'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/percent24hr/$', 'cryptocurry.analysis.views.cmcd_percent24hr', name='cmcd_percent24hr'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/marketcap/$', 'cryptocurry.analysis.views.cmcd_marketcap', name='cmcd_marketcap'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/percent1hr/$', 'cryptocurry.analysis.views.cmcd_percentchange1hr', name='cmcd_percentchange1hr'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/currency_price/$', 'cryptocurry.analysis.views.cmcd_currencyprice', name='cmcd_currencyprice'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/supply/$', 'cryptocurry.analysis.views.cmcd_supply', name='cmcd_supply'),
    url(r'cryptocurry/analyze/visual/coinmarketcapdata/volume/$', 'cryptocurry.analysis.views.cmcd_volume', name='cmcd_volume'),    

)






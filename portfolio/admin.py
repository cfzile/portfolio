from django.contrib import admin

from portfolio.models import Portfolio, Stock


class Portfolios(admin.ModelAdmin):
    list_display = ('name', 'stock_weights', 'stock_tickers', 'stock_exchanges')
    fields = ['name', 'stock_weights', 'stock_tickers', 'stock_exchanges']
    list_display_links = ('name',)
    view_on_site = True


class Stocks(admin.ModelAdmin):
    list_display = ('ticker', 'date', 'close_price', 'currency')
    fields = ['ticker', 'date', 'close_price', 'currency']
    list_display_links = ('ticker',)
    view_on_site = True


admin.site.register(Portfolio, Portfolios)
admin.site.register(Stock, Stocks)

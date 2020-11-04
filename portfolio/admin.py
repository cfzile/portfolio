from django.contrib import admin

from portfolio.models import Portfolio


class Portfolios(admin.ModelAdmin):
    list_display = ('id', 'name', 'stock_weights', 'stock_tickers', 'stock_exchanges')
    fields = ['id', 'name', 'stock_weights', 'stock_tickers', 'stock_exchanges']
    list_display_links = ('name',)
    view_on_site = True


admin.site.register(Portfolio, Portfolios)

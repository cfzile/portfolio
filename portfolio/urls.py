from django.contrib import admin
from django.urls import path

from portfolio import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('p<int:portfolio_id>', views.show_portfolio, name='show_portfolio'),
    path('create_portfolio', views.create_portfolio, name='create_portfolio'),
    path('edit_portfolio', views.edit_portfolio, name='edit_portfolio'),
    path('subscribe_on_portfolio', views.subscribe_on_portfolio, name='subscribe_on_portfolio')
]

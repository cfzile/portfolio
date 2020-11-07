from django.contrib.auth.models import User
from django.contrib.postgres.fields import *
from django.db import models
from django.utils import timezone


class Portfolio(models.Model):
    name = models.CharField(max_length=50, default="Noname")
    stock_tickers = ArrayField(models.CharField(max_length=10), null=True, default=list())
    stock_weights = ArrayField(models.FloatField(0), null=True, default=list())
    stock_exchanges = ArrayField(models.CharField(max_length=50), null=True, default=list())
    telegram_subscribers = ArrayField(models.CharField(max_length=50), null=True, default=list())
    creation_date = models.DateField(default=timezone.now())


class Stock(models.Model):
    ticker = models.CharField(max_length=50, default="none")
    date = models.DateField(default=timezone.now())
    close_price = models.FloatField(default=0)

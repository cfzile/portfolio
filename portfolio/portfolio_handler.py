import math

import numpy as np
import pandas as pd
import yfinanceng as yf
from django.utils import timezone, dateformat

from portfolio.models import Stock, Portfolio

latest_time_of_today_info_update = timezone.now()
latest_date_of_all_info_update = timezone.now()
were_first_info_update = False


def get_all_tickers_from_portfolios(portfolios):
    stocks_set = set()
    for portfolio in portfolios:
        stock_currencies = []
        if len(portfolio.stock_currencies) != len(portfolio.stock_tickers):
            tickers = yf.Tickers(portfolio.stock_tickers)
            for ticker in tickers.tickers:
                try:
                    stock_currencies.append(ticker.info['currency'] + '=X')
                except:
                    stock_currencies.append('USD=X')
            print(stock_currencies)
            Portfolio.objects.filter(id=portfolio.id).update(stock_currencies=stock_currencies)
            portfolio.stock_currencies = stock_currencies
        for i in range(len(portfolio.stock_tickers)):
            stocks_set.add(portfolio.stock_tickers[i])
            stocks_set.add(portfolio.stock_currencies[i])
    return ' '.join(stocks_set)


def get_all_exist_tickets():
    return get_all_tickers_from_portfolios(Portfolio.objects.all())


def get_tickers_info(stocks_string, from_date):
    global latest_time_of_today_info_update, latest_date_of_all_info_update, were_first_info_update

    if (timezone.now() - latest_date_of_all_info_update).seconds > 60 * 60 * 24 or were_first_info_update is False:
        update_data(get_all_exist_tickets(), from_date)

    from_date = dateformat.format(from_date, 'Y-m-d')
    to_date = dateformat.format(timezone.now() + timezone.timedelta(days=1), 'Y-m-d')
    yesterday = dateformat.format(timezone.now() - timezone.timedelta(days=1), 'Y-m-d')
    today = dateformat.format(timezone.now(), 'Y-m-d')
    today_info, stocks = None, {}

    if (timezone.now() - latest_time_of_today_info_update).seconds > 60:
        today_info = yf.download(stocks_string, start=from_date, end=to_date, threads=3)
        latest_time_of_today_info_update = timezone.now()

    for stock in stocks_string.split(' '):
        if today_info is not None:
            for date in [yesterday, today]:
                try:
                    if math.isnan(today_info['Close'][stock].loc[date]):
                        continue
                    if Stock.objects.filter(ticker=stock, date=date).count() != 0:
                        Stock.objects.filter(ticker=stock, date=date).update(
                            close_price=today_info['Close'][stock].loc[date])
                    else:
                        Stock.objects.create(ticker=stock, date=date,
                                             close_price=today_info['Close'][stock].loc[date]).save()
                except Exception as error:
                    print("Can not update", date, error)

        stock_info = Stock.objects.filter(date__gte=from_date, date__lte=to_date, ticker=stock).order_by('date')
        stocks[stock] = pd.DataFrame([s.close_price for s in stock_info], columns=['Close'], index=[
            dateformat.format(timezone.datetime(s.date.year, s.date.month, s.date.day), 'Y-m-d') for s in stock_info])

    return stocks


def update_data(stocks_string, from_date, clear_old_info=True):
    global were_first_info_update, latest_date_of_all_info_update

    if clear_old_info:
        Stock.objects.all().delete()

    from_date = dateformat.format(from_date, 'Y-m-d')
    to_date = dateformat.format(timezone.now() + timezone.timedelta(days=1), 'Y-m-d')
    dates = pd.date_range(from_date, timezone.now().date(), freq='D').tolist()

    stocks = yf.download(stocks_string, start=from_date, end=to_date, threads=3)
    stocks = stocks.reindex(dates, method='ffill')

    prev_date = dateformat.format(dates[0], 'Y-m-d')
    for date in dates:
        date = dateformat.format(date, 'Y-m-d')
        stocks.loc[date] = np.where(stocks.loc[date].isnull(), stocks.loc[prev_date], stocks.loc[date])
        prev_date = date

    for stock in stocks_string.split(' '):
        dates = stocks['Close'][stock].keys()
        values = stocks['Close'][stock].values
        for i in range(len(dates)):
            value = 1
            if not(math.isnan(values[i])):
                value = values[i]
            else:
                print('NaN value for', stock)
            Stock.objects.create(ticker=stock, date=dates[i], close_price=value).save()

    were_first_info_update = True
    latest_date_of_all_info_update = timezone.now()


class PortfolioHandler:

    def get_return(self):
        try:
            returns = 0
            for i in range(len(self.portfolio.stock_tickers)):
                ticker = self.portfolio.stock_tickers[i]
                weight = self.portfolio.stock_weights[i]
                currency = self.portfolio.stock_currencies[i]
                current_date = dateformat.format(timezone.now(), 'Y-m-d')
                creation_date = dateformat.format(self.portfolio.creation_date, 'Y-m-d')
                s = self.stocks[ticker]['Close'].loc[current_date]
                f = self.stocks[ticker]['Close'].loc[creation_date]
                currency_f = self.stocks[currency]['Close'].loc[creation_date]
                currency_s = self.stocks[currency]['Close'].loc[current_date]
                pr = ((s / f * currency_s/currency_f - 1) * 100)
                returns += pr * weight
                self.info[i][2] = np.round((s - f) / f * 100, 2)
                self.info[i][3] = -np.round((currency_s - currency_f)/currency_f * 100, 2)
                self.info[i][4] = np.round(pr, 2)
                self.info[i][5] = np.round(weight * pr, 10)
            return np.round(returns, 2)
        except Exception as error:
            print("Error in getR: ", error)

        return 0

    def __init__(self, portfolio, stocks):
        self.stocks = stocks
        self.portfolio = portfolio
        self.number_stocks = len(portfolio.stock_tickers)
        self.info = [[portfolio.stock_tickers[i], np.round(portfolio.stock_weights[i], 10), 0, 0, 0, 0]
                     for i in range(self.number_stocks)]
        self.R = self.get_return()

    def get_returns_by_dates(self, date_from):
        dates = [dateformat.format(date, 'Y-m-d') for date in
                 pd.date_range(date_from, timezone.now().date(), freq='D').tolist()]
        local_stocks = pd.DataFrame([self.stocks[ticker]['Close'].values for ticker in self.portfolio.stock_tickers]).T
        local_stocks.columns = self.portfolio.stock_tickers
        local_stocks.index = dates
        returns = []
        for i in range(len(dates)):
            s = local_stocks.loc[dates[i]]
            f = local_stocks.loc[dates[0]]
            currency_f = np.array(
                [self.stocks[currency]['Close'].loc[dates[0]] for currency in self.portfolio.stock_currencies])
            currency_s = np.array(
                [self.stocks[currency]['Close'].loc[dates[i]] for currency in self.portfolio.stock_currencies])
            returns.append(np.array(self.portfolio.stock_weights).dot(
                np.array((s - f) / f) + (currency_s - currency_f) / currency_f))
        return [dates, returns]

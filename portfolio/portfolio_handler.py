import numpy as np
import pandas as pd
import yfinanceng as yf
from django.utils import timezone, dateformat

from portfolio.models import Stock, Portfolio

stocks = {}
time_last_update = timezone.now()
update_last_date = timezone.now()
first_download = False


def download_stocks(stocks_list, from_date):
    global stocks, time_last_update, update_last_date, first_download

    if (timezone.now() - update_last_date).seconds > 60 * 60 * 24 or first_download is False:
        lst = [lst for lst in Portfolio.objects.values_list('stock_tickers', flat=True)]
        update_data(' '.join(np.concatenate(lst, axis=0)), from_date)
        update_last_date = timezone.now()

    from_date = dateformat.format(from_date, 'Y-m-d')
    to_date = dateformat.format(timezone.now() + timezone.timedelta(days=1), 'Y-m-d')
    stocks = {}
    data_now = None
    if (timezone.now() - time_last_update).seconds > 60:
        data_now = yf.download(stocks_list, start=from_date, end=to_date, threads=3)
        time_last_update = timezone.now()
    yesterday = dateformat.format(timezone.now() - timezone.timedelta(days=1), 'Y-m-d')
    today = dateformat.format(timezone.now(), 'Y-m-d')

    for stock in stocks_list.split(' '):
        if stock == ' ' or stock == '':
            continue
        if data_now is not None:
            try:
                if Stock.objects.filter(ticker=stock, date=yesterday).count() != 0:
                    Stock.objects.filter(ticker=stock, date=yesterday).update(
                        close_price=data_now['Close'][stock].loc[yesterday])
                else:
                    Stock.objects.create(ticker=stock, date=yesterday,
                                         close_price=data_now['Close'][stock].loc[yesterday]).save()
            except Exception as e:
                print("Can not update", yesterday, e)

            try:
                if Stock.objects.filter(ticker=stock, date=today).count() != 0:
                    Stock.objects.filter(ticker=stock, date=today).update(
                        close_price=data_now['Close'][stock].loc[today])
                else:
                    Stock.objects.create(ticker=stock, date=today,
                                         close_price=data_now['Close'][stock].loc[yesterday]).save()
            except Exception as e:
                print("Can not update", today, e)

        stocks_ = Stock.objects.filter(date__gte=from_date, date__lte=to_date, ticker=stock).order_by('date')
        stocks[stock] = pd.DataFrame([s.close_price for s in stocks_], columns=['Close'], index=[
            dateformat.format(timezone.datetime(s.date.year, s.date.month, s.date.day), 'Y-m-d') for s in stocks_])

    first_download = True


def update_data(stocks_list, from_date, delete_all=True):
    if delete_all:
        Stock.objects.all().delete()
    from_date = dateformat.format(from_date, 'Y-m-d')
    to_date = dateformat.format(timezone.now() + timezone.timedelta(days=1), 'Y-m-d')
    stocks = yf.download(stocks_list, start=from_date, end=to_date, threads=3)
    dates = pd.date_range(from_date, timezone.now().date(), freq='D').tolist()
    stocks = stocks.reindex(dates, method='ffill')
    prev_date = dateformat.format(dates[0], 'Y-m-d')
    for DATE in dates:
        date = dateformat.format(DATE, 'Y-m-d')
        stocks.loc[date] = np.where(stocks.loc[date].isnull(), stocks.loc[prev_date], stocks.loc[date])
        prev_date = date
    S = set()
    for stock in stocks_list.split(' '):
        if stock == ' ' or stock == '':
            continue
        S.add(stock)
    for stock in S:
        dates = stocks['Close'][stock].keys()
        values = stocks['Close'][stock].values
        for i in range(len(dates)):
            Stock.objects.create(ticker=stock, date=dates[i], close_price=values[i]).save()


class PortfolioHandler:

    def getR(self):
        R = 0
        for i in range(len(self.portfolio.stock_tickers)):
            ticker = self.portfolio.stock_tickers[i]
            weight = self.portfolio.stock_weights[i]
            current_date = dateformat.format(timezone.now(), 'Y-m-d')
            creation_date = dateformat.format(self.portfolio.creation_date, 'Y-m-d')
            # print(ticker, stocks)
            s = stocks[ticker]['Close'].loc[current_date]
            f = stocks[ticker]['Close'].loc[creation_date]
            pr = ((s - f) / f * 100)
            R += pr * weight
            self.info[i][2] = np.round(pr, 2)
            self.info[i][3] = np.round(weight * pr, 10)
        return np.round(R, 2)

    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.info = []
        for i in range(len(portfolio.stock_tickers)):
            self.info.append([portfolio.stock_tickers[i], np.round(portfolio.stock_weights[i], 10), 0, 0])
        self.number_stocks = len(portfolio.stock_tickers)
        self.R = 0
        try:
            self.R = self.getR()
        except Exception as e:
            print('Error: ', e)

    def getRByDates(self, date_from):
        dates = [dateformat.format(date, 'Y-m-d') for date in
                 pd.date_range(date_from, timezone.now().date(), freq='D').tolist()]
        local_stocks = pd.DataFrame([stocks[ticker]['Close'].values for ticker in self.portfolio.stock_tickers]).T
        local_stocks.columns = self.portfolio.stock_tickers
        local_stocks.index = dates
        columns = list(local_stocks.columns)
        W = {self.portfolio.stock_tickers[i]: self.portfolio.stock_weights[i] for i in range(self.number_stocks)}
        weights = [W[key] for key in columns]
        R = []
        for i in range(len(dates)):
            s = local_stocks.loc[dates[i]]
            f = local_stocks.loc[dates[0]]
            R.append(np.array(weights).dot(np.array((s - f) / f)))
        return [dates, R]

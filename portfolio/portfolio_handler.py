import math

import numpy as np
import yfinanceng as yf
import pandas as pd
from django.utils import timezone, dateformat

stocks = {}


def download_stocks(stocks_list, from_date):
    global stocks
    from_date = dateformat.format(from_date, 'Y-m-d')
    to_date = dateformat.format(timezone.now() + timezone.timedelta(days=1), 'Y-m-d')
    stocks = yf.download(stocks_list, start=from_date, end=to_date)
    dates = pd.date_range(from_date, stocks.index[-1], freq='D').tolist()
    print(dates, stocks)
    stocks = stocks.reindex(dates, method='ffill')
    prev_date = dateformat.format(dates[0], 'Y-m-d')
    for DATE in dates:
        date = dateformat.format(DATE, 'Y-m-d')
        stocks.loc[date] = np.where(stocks.loc[date].isnull(), stocks.loc[prev_date], stocks.loc[date])
        prev_date = date


class PortfolioHandler:

    def getR(self):
        R = 0
        for i in range(len(self.portfolio.stock_tickers)):
            ticker = self.portfolio.stock_tickers[i]
            weight = self.portfolio.stock_weights[i]
            current_date = dateformat.format(timezone.now(), 'Y-m-d')
            creation_date = dateformat.format(self.portfolio.creation_date, 'Y-m-d')
            s = stocks['Close'][ticker].loc[current_date]
            f = stocks['Close'][ticker].loc[creation_date]
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
            print(e)

    def getRByDates(self, date_from):
        dates = pd.date_range(date_from, timezone.now().date(), freq='D').tolist()
        local_stocks = stocks['Close'][self.portfolio.stock_tickers]
        columns = list(local_stocks.columns)
        W = {self.portfolio.stock_tickers[i]: self.portfolio.stock_weights[i] for i in range(self.number_stocks)}
        weights = [W[key] for key in columns]
        R = []
        for i in range(len(dates)):
            s = local_stocks.loc[dates[i]]
            f = local_stocks.loc[dates[0]]
            R.append(np.array(weights).dot(np.array((s - f) / f)))
        return [dates, R]

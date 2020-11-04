import numpy as np
import yfinanceng as yf
from django.utils import timezone, dateformat


class PortfolioHandler:

    def getR(self):
        from_date = dateformat.format(self.portfolio.creation_date + timezone.timedelta(days=1), 'Y-m-d')
        to_date = dateformat.format(timezone.now(), 'Y-m-d')
        stocks_list = ' '.join(self.portfolio.stock_tickers)
        stocks = yf.download(stocks_list, start=from_date, end=to_date)

        R = 0
        for i in range(len(self.portfolio.stock_tickers)):
            ticker = self.portfolio.stock_tickers[i]
            weight = self.portfolio.stock_weights[i]
            closes = list(stocks['Close'][ticker])
            f = closes[0]
            s = closes[-1]
            pr = ((s - f) / f * 100)
            R += pr * weight
            self.info[i][2] = np.round(pr, 2)
        return np.round(R, 2)

    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.info = []
        for i in range(len(portfolio.stock_tickers)):
            self.info.append([portfolio.stock_tickers[i], np.round(portfolio.stock_weights[i], 5), 0])
        self.number_stocks = len(portfolio.stock_tickers)
        try:
            self.R = self.getR()
        except Exception as e:
            print(e)
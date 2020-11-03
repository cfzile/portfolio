import investpy
import pandas as pd
from django.utils import timezone, dateformat
import numpy as np

class PortfolioHandler:

    def getR(self):
        stocks_lists = {}
        for i in range(len(self.portfolio.stock_tickers)):
            exchange = self.portfolio.stock_exchanges[i]
            if exchange not in stocks_lists:
                stocks_lists[exchange] = []
            stocks_lists[exchange].append(self.portfolio.stock_tickers[i])

        stocks = {}

        for key, stocks_list in stocks_lists.items():
            for i in range(0, len(stocks_list)):  # ticker_names
                try:
                    stocks[stocks_list[i]] = investpy.get_stock_historical_data(stock=stocks_list[i],
                                                                                country=key,
                                                                                from_date=dateformat.format(self.portfolio.creation_date,'d/m/Y'),
                                                                                to_date=dateformat.format(timezone.now(), 'd/m/Y'),
                                                                                order='ascending', )
                except IndexError:
                    stocks[stocks_list[i]] = pd.DataFrame(
                        columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Currency'])
        KEY = ''
        for key, value in stocks.items():
            if KEY == '' or len(stocks[KEY]) < len(value):
                KEY = key
        main_index = stocks[KEY].index.copy()
        for key, value in stocks.items():
            stocks[key] = stocks[key].reindex(main_index)
            stocks[key]['Close'].interpolate(method='linear', inplace=True, limit=21, limit_direction='both')
            stocks[key]['Volume'].interpolate(method='linear', inplace=True, limit=21, limit_direction='both')
        R = 0
        for i in range(len(self.portfolio.stock_tickers)):
            ticker = self.portfolio.stock_tickers[i]
            weight = self.portfolio.stock_weights[i]
            closes = list(stocks[ticker]['Close'])
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
        except:
            print("Error")

    def updateR(self):
        self.R = self.getR()
import plotly.graph_objs as go
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from plotly.graph_objs.scatter import Marker
from plotly.offline import *

from portfolio import events, constance
from portfolio.constance import *
from portfolio.models import Portfolio
from portfolio.portfolio_handler import PortfolioHandler


def get_full_context(request, context):
    general_context = {"events": events.get(request), "constance": constance}
    return {**context, **general_context}


def home(request):
    portfolios = [PortfolioHandler(portfolio) for portfolio in Portfolio.objects.all()]
    return render(request, 'pages/all_portfolios.html',
                  get_full_context(request, {'page': MAIN_PAGE_NAME, 'portfolios': portfolios}))


def show_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    return render(request, 'pages/show_portfolio.html',
                  get_full_context(request,
                                   {'page': SHOW_PORTFOLIO_PAGE_NAME % portfolio.name,
                                    'portfolio': PortfolioHandler(portfolio)}))


def isEmptyField(field):
    if field is None or field == "":
        return True
    return False


def create_portfolio(request):
    if request.method == "POST":
        portfolio_name = request.POST.get("portfolio_name")
        current_stock_exchange = request.POST.get("stock_exchange_1")
        current_stocks = request.POST.get("stocks_1")
        creation_date = request.POST.get("creation_date")
        if not (isEmptyField(portfolio_name)) and not (isEmptyField(current_stock_exchange)) and not (
                isEmptyField(current_stocks)) and not (isEmptyField(creation_date)):
            stock_tickers = []
            stock_weights = []
            stock_exchanges = []
            i = 1
            while request.POST.get("stocks_%d" % i) is not None and request.POST.get(
                    "stock_exchange_%d" % i) is not None:
                current_stock_exchange = request.POST.get("stock_exchange_%d" % i)
                current_stocks = request.POST.get("stocks_%d" % i)
                stocks = current_stocks.rstrip().replace('\r', '').replace('\n', '').split(",")
                for stock in stocks:
                    key, weight = stock.rstrip().replace('\r', '').replace('\n', '').split(":")
                    stock_tickers.append(key)
                    stock_weights.append(float(weight))
                    stock_exchanges.append(current_stock_exchange)
                i += 1

            if (sum(stock_weights) - 1.) > 0.000001:
                events.add_event(request, {EVENT_ERROR: [NON_CORRECT_DATA]})
            else:
                Portfolio.objects.create(name=portfolio_name, stock_weights=stock_weights,
                                         stock_exchanges=stock_exchanges,
                                         stock_tickers=stock_tickers, creation_date=creation_date).save()
                events.add_event(request, {EVENT_INFO: [SUCCESSFUL]})
                return redirect('/')
        else:
            events.add_event(request, {EVENT_ERROR: [NON_CORRECT_DATA]})
    return render(request, 'pages/create_portfolio.html',
                  get_full_context(request, {'page': CREATE_PORTFOLIO_PAGE_NAME}))


def edit_portfolio(request):
    return render(request, 'index.html', get_full_context(request, {'page': SHOW_PORTFOLIO_PAGE_NAME}))


def subscribe_on_portfolio(request):
    return render(request, 'index.html', get_full_context(request, {'page': SHOW_PORTFOLIO_PAGE_NAME}))


def compare_portfolios(request):

    if request.method == "POST":
        portfolios = []
        date_from = timezone.datetime(1999, 1, 1).date()
        for portfolio in Portfolio.objects.all():
            if request.POST.get(str(portfolio.id)) is not None:
                portfolios.append(PortfolioHandler(portfolio))
                delta = date_from - portfolio.creation_date
                if delta.days < 0:
                    date_from = portfolio.creation_date

        R = [[portfolio.portfolio.name, portfolio.getRByDates(date_from)] for portfolio in portfolios]

        fig = go.Figure()

        for name, r in R:
            scatter = go.Scatter(x=r[0], y=r[1],
                                 mode='markers+lines',
                                 marker=Marker(symbol='0'),
                                 opacity=0.8, name=name)
            fig.add_trace(scatter)
        plt_div = plot(fig, output_type='div')

        return render(request, 'pages/compare.html', get_full_context(request, {'page': COMPARE_PORTFOLIOS_PAGE_NAME,
                                                                                'portfolios': Portfolio.objects.all(),
                                                                                'html': plt_div
                                                                                }))
    return render(request, 'pages/compare.html', get_full_context(request, {'page': COMPARE_PORTFOLIOS_PAGE_NAME,
                                                                            'portfolios': Portfolio.objects.all(),
                                                                            }))

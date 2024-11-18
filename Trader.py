import datetime
# for de-serializing etc (writing object to file)
import pickle

from yfinance import Ticker

from Stock import Stock
import yfinance as yf


class Trader:
    def __init__(self, username, fee: float = 0, initial_balance: float = 0):
        self.username=username
        self.trades = []
        self.owned = dict()
        self.fee = fee
        self.balance = initial_balance

    def set_fee(self, fee: float):
        assert 1 >= fee >= 0 # fee is a fractional percentage
        self.fee = fee

    def add_money(self, money: float):
        self.balance += money

    def remove_money(self, money: float):
        self.balance -= money

    def buy(self, stock_name: str, cost: float):  # still gotta find out if one can buy half a stock lol
        assert cost <= self.balance, f"Can't buy more than you got. " \
                                     f"Offer: {cost}, Total balance {self.balance}"
        # check if stock name exists
        try:
            # if it is, get share price
            share_price = float(yf.Ticker(stock_name).get_info()['currentPrice'])
            # check how much the money I spent can get me
            current_purchase_total = cost / share_price
            trade = Stock(stock_name, current_purchase_total, share_price, datetime.datetime.now())
            # add current trade to my stocks dickt
            curr = self.owned.setdefault(stock_name, 0)
            self.owned[stock_name] = curr + current_purchase_total
            # subtract cost from balance
            self.remove_money(cost)
            self.trades.append(trade)

            # subtract trade fee
            self.balance -= cost * self.fee
        except KeyError:
            raise ValueError(f"{stock_name} is not a valid stock name for Yahoo's API")

    def buy_shares(self,stock_name, amount):
        # check if stock name exists
        try:
            # if it is, get share price
            share_price = float(yf.Ticker(stock_name).get_info()['currentPrice'])
            # how much will it cost?
            cost = amount * share_price
            assert cost <= self.balance, f"Can't buy more than you got. " \
                                         f"Offer: {cost}, Total balance {self.balance}"

            trade = Stock(stock_name, amount, share_price, datetime.datetime.now())
            # add current trade to my stocks dickt
            curr = self.owned.setdefault(stock_name, 0)
            self.owned[stock_name] = curr + amount
            # subtract cost from balance
            self.remove_money(cost)
            self.trades.append(trade)

            # subtract trade fee
            self.balance -= cost * self.fee
        except KeyError:
            raise ValueError(f"{stock_name} is not a valid stock name for Yahoo's API")

    def sell(self, stock_name, amount=None, value=None):
        assert (amount is None) ^ (value is None), "You must sell using value or amount as argument!"
        if amount is not None:
            self.sell_by_amount(amount, stock_name)
        elif value is not None:
            self.sell_by_value(value, stock_name)
            # subtract trade fee
            self.balance -= value * self.fee

        else:
            raise Exception(f"Invalid arguments passed to self.sell(). {amount=}, {value=}")

    def sell_by_amount(self, amount, stock_name):
        # sell the amount specified
        try:
            share_price = float(yf.Ticker(stock_name).get_info()['currentPrice'])
            assert stock_name in self.owned.keys() and amount <= self.owned[stock_name], \
                f"Insufficient stock volume ({self.owned.get(stock_name) or 0})!"
            # add sell and subtract amount and add balance accordion-ly
            trade = Stock(stock_name, -amount, share_price, datetime.datetime.now())
            self.trades.append(trade)
            self.owned[stock_name] -= amount
            revenue = amount * share_price
            # add balance
            self.add_money(revenue)
            # subtract trade fee
            self.balance -= revenue * self.fee
        except KeyError:
            raise ValueError(f"{stock_name} is not a valid stock name for Yahoo's API")

    def sell_by_value(self, value, stock_name):
        # assume I got 5,000 dollars of stock A
        # I want to sell 500$
        # share is 100$, so I sell 5 shares
        # sell the amount specified
        try:
            share_price = float(yf.Ticker(stock_name).get_info()['currentPrice'])
            amount = value / share_price
            assert stock_name in self.owned.keys() and amount <= self.owned[stock_name], \
                f"Insufficient stock volume ({self.owned.get(stock_name) or 0})!"
            # add sell and subtract amount and add balance accordion-ly
            trade = Stock(stock_name, -amount, share_price, datetime.datetime.now())
            self.trades.append(trade)
            self.owned[stock_name] -= amount
            # add balance
            self.add_money(amount * share_price)
        except KeyError:
            raise ValueError(f"{stock_name} is not a valid stock name for Yahoo's API")

    def get_revenue_from(self, from_date=None):
        sorted_trades = sorted(self.trades, key=lambda x: x.purchase_time)
        if from_date is None:
            return sum(s.amount*s.share_value for s in sorted_trades)
        else:
            assert isinstance(from_date, datetime.datetime)
            return sum(s.amount*s.share_value for s in sorted_trades if s.puchase_time >= from_date)


def load_trader_from_file(file):
    # load it
    with open(file, 'rb') as file2:
        s1_new = pickle.load(file2)
        return s1_new


def store_trader_in_file(trader, file):
    # save it
    with open(file, 'wb') as file:
        pickle.dump(trader, file)


if __name__ == "__main__":
    t = Trader("Rotem", 0, 10000)
    t.buy("AMD", cost=100)
    t.buy("INTC", cost=100)
    t.get_revenue_from()



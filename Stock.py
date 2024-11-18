# import StockAPI
import datetime


class Stock:
    def __init__(self, name, amount, share_value, purchase_time=None):
        self.name = name
        self.amount = amount
        self.share_value=share_value
        self.purchase_time = purchase_time or datetime.datetime.now()

    def __repr__(self):
        return f"{self.name=}, {self.amount=}, {self.share_value=}, {self.purchase_time=}"


if __name__ == '__main__':
    s = Stock("AMD", 10, 150)
    q = Stock("AMD", 20, 150)
    print(s)
    print(q)

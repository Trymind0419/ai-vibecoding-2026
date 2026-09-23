# -*- coding: utf-8 -*-
"""모의투자(Paper Trading) 시뮬레이터"""
class PaperTrader:
    def __init__(self, initial_capital=10000000):
        self.capital = initial_capital
        self.positions = {}

    def get_balance(self):
        return self.capital

    def order_buy(self, symbol, price, qty):
        cost = price * qty
        if self.capital >= cost:
            self.capital -= cost
            self.positions[symbol] = self.positions.get(symbol, 0) + qty
            return True
        return False

    def order_sell(self, symbol, price, qty):
        if self.positions.get(symbol, 0) >= qty:
            self.capital += price * qty
            self.positions[symbol] -= qty
            return True
        return False

import sys
from functools import wraps

import yfinance
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTabWidget, QLineEdit, QLabel, \
    QGridLayout, QMessageBox, QFileDialog, QInputDialog, QTableWidget, QTableWidgetItem, QHBoxLayout, QCompleter

from Trader import Trader, load_trader_from_file, store_trader_in_file

WIDTH = 800
HEIGHT = 340


# TODO:
# - add revenue in main page (V)
# - add "net worth" in main page (V)
# - conduct tests for edge cases
# - automate save-file name generation according to username.
# - create settings for user to allow overwriting current profile on exit (etc)


def update_gui_info(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.update_finance()
        self.update_trades()
        self.update_available_stocks()
        return result

    return wrapper


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # load ticker list
        from concur import get_tickers_from_csv
        self.stored_tickers = get_tickers_from_csv(False)

        self.stock_name_input = None
        self.trader = None
        self.initUI()
        self.select_profile()

    def initUI(self):
        self.setGeometry(100, 100, WIDTH, HEIGHT)
        self.setWindowTitle('Stock Trader')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QWidget {
                background-color: white;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 15px;
                font-size: 12pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QLabel {
                font-size: 12pt;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        self.profile_tab = self.create_profile_tab()
        tab_widget.addTab(self.profile_tab, "Profile")

        self.buy_tab = self.create_buy_tab()
        tab_widget.addTab(self.buy_tab, "Buy")

        self.sell_tab = self.create_sell_tab()
        tab_widget.addTab(self.sell_tab, "Sell")

        self.account_tab = self.create_account_tab()
        tab_widget.addTab(self.account_tab, "Account")

        self.history_tab = self.create_history_tab()
        tab_widget.addTab(self.history_tab, "History")

        status_bar = self.statusBar()
        status_bar.showMessage("Welcome to Stock Trader!")

        self.center_window()

    def select_profile(self):
        choice, ok = QInputDialog.getItem(self, "Select Action", "What would you like to do?",
                                          ["Load Existing Profile", "Create New Profile"], editable=False)

        if ok:
            if choice == "Load Existing Profile":
                self.load_profile()
            elif choice == "Create New Profile":
                self.new_profile()
        else:
            sys.exit()  # Exit the application if no choice is made

    def center_window(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        if self.trader:
            save_choice = QMessageBox.question(self, "Save Profile?",
                                               "Do you want to save your profile before closing?")
            if save_choice == QMessageBox.Yes:
                self.save_profile()

        event.accept()

    def create_profile_tab(self):
        profile_tab = QWidget()
        profile_layout = QVBoxLayout()
        profile_tab.setLayout(profile_layout)

        load_button = QPushButton("Load Profile")
        load_button.clicked.connect(self.load_profile)
        profile_layout.addWidget(load_button)

        new_button = QPushButton("New Profile")
        new_button.clicked.connect(self.new_profile)
        profile_layout.addWidget(new_button)

        save_button = QPushButton("Save Profile")
        save_button.clicked.connect(self.save_profile)
        profile_layout.addWidget(save_button)

        self.balance_label = QLabel("Balance: $0.00")
        profile_layout.addWidget(self.balance_label)

        self.revenue_label = QLabel("Revenue: $0.00")
        profile_layout.addWidget(self.revenue_label)

        self.net_worth_label = QLabel("Net worth: $0.00")
        profile_layout.addWidget(self.net_worth_label)

        return profile_tab

    def create_buy_tab(self):
        buy_tab = QWidget()
        buy_layout = QGridLayout()
        buy_tab.setLayout(buy_layout)

        buy_label = QLabel("Buy Stocks:")
        buy_label.setStyleSheet("""
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        buy_layout.addWidget(buy_label, 0, 0, 1, 2)

        stock_name_label = QLabel("Stock Name:")
        buy_layout.addWidget(stock_name_label, 1, 0)
        self.stock_name_input = QLineEdit()
        self.stock_name_input.setPlaceholderText("Enter stock symbol or select from list")
        self.stock_name_input.setCompleter(QCompleter(self.fetch_stocks()))
        buy_layout.addWidget(self.stock_name_input, 1, 1)

        amount_label = QLabel("Amount:")
        buy_layout.addWidget(amount_label, 2, 0)
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QRegExpValidator(QRegExp("[0-9]+.?[0-9]{,9}")))
        buy_layout.addWidget(self.amount_input, 2, 1)

        cost_label = QLabel("Cost:")
        buy_layout.addWidget(cost_label, 3, 0)
        self.cost_input = QLineEdit()
        self.cost_input.setValidator(QRegExpValidator(QRegExp("[0-9]+.?[0-9]{,9}")))
        buy_layout.addWidget(self.cost_input, 3, 1)

        button_layout = QHBoxLayout()
        buy_by_amount_button = QPushButton("Buy by Amount")
        buy_by_amount_button.clicked.connect(lambda: self.buy_stock(False))
        buy_by_cost_button = QPushButton("Buy by Cost")
        buy_by_cost_button.clicked.connect(lambda: self.buy_stock(True))

        button_layout.addWidget(buy_by_amount_button)
        button_layout.addWidget(buy_by_cost_button)

        buy_layout.addLayout(button_layout, 4, 0, 1, 2)

        return buy_tab

    def create_sell_tab(self):
        sell_tab = QWidget()
        sell_layout = QGridLayout()
        sell_tab.setLayout(sell_layout)

        sell_label = QLabel("Sell Stocks:")
        sell_label.setStyleSheet("""
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        sell_layout.addWidget(sell_label, 0, 0, 1, 2)

        stock_name_label = QLabel("Stock Name:")
        sell_layout.addWidget(stock_name_label, 1, 0)
        self.sell_stock_name_input = QLineEdit()
        self.sell_stock_name_input.setPlaceholderText("Enter stock symbol or select from list")
        self.sell_stock_name_input.setCompleter(QCompleter(self.fetch_owned_stocks()))

        sell_layout.addWidget(self.sell_stock_name_input, 1, 1)

        amount_label = QLabel("Amount:")
        sell_layout.addWidget(amount_label, 2, 0)
        self.sell_amount_input = QLineEdit()
        self.sell_amount_input.setValidator(QRegExpValidator(QRegExp("[0-9]+.?[0-9]{,9}")))
        sell_layout.addWidget(self.sell_amount_input, 2, 1)

        cost_label = QLabel("Cost:")
        sell_layout.addWidget(cost_label, 3, 0)
        self.sell_cost_input = QLineEdit()
        self.sell_cost_input.setValidator(QRegExpValidator(QRegExp("[0-9]+.?[0-9]{,9}")))
        sell_layout.addWidget(self.sell_cost_input, 3, 1)

        button_layout = QHBoxLayout()
        sell_by_amount_button = QPushButton("Sell by Amount")
        sell_by_amount_button.clicked.connect(lambda: self.sell_stock(False))
        sell_by_cost_button = QPushButton("Sell by Cost")
        sell_by_cost_button.clicked.connect(lambda: self.sell_stock(True))

        button_layout.addWidget(sell_by_amount_button)
        button_layout.addWidget(sell_by_cost_button)

        sell_layout.addLayout(button_layout, 4, 0, 1, 2)

        return sell_tab

    def create_account_tab(self):
        account_tab = QWidget()
        account_layout = QVBoxLayout()
        account_tab.setLayout(account_layout)

        # Add Money Section
        add_money_header = QLabel("Add Money")
        add_money_header.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        account_layout.addWidget(add_money_header)

        add_money_input = QLineEdit()
        add_money_button = QPushButton("Add Money")
        add_money_button.clicked.connect(lambda: self.add_money(float(add_money_input.text())))
        add_money_layout = QHBoxLayout()
        add_money_layout.addWidget(add_money_input)
        add_money_layout.addWidget(add_money_button)
        account_layout.addLayout(add_money_layout)

        # Set Trading Fee Section
        set_fee_header = QLabel("Set Trading Fee (%)")
        set_fee_header.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 5px;
        """)
        account_layout.addWidget(set_fee_header)

        set_fee_input = QLineEdit()
        set_fee_button = QPushButton("Set Trading Fee")
        set_fee_button.clicked.connect(lambda: self.set_trading_fee(float(set_fee_input.text())))
        set_fee_layout = QHBoxLayout()
        set_fee_layout.addWidget(set_fee_input)
        set_fee_layout.addWidget(set_fee_button)
        account_layout.addLayout(set_fee_layout)

        return account_tab

    def create_history_tab(self):
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_tab.setLayout(history_layout)

        self.trade_history = QTableWidget()
        self.trade_history.setColumnCount(4)

        self.trade_history.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.trade_history.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        self.trade_history.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        self.trade_history.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        history_layout.addWidget(self.trade_history)

        return history_tab

    # ... (rest of the methods remain the same)
    @update_gui_info
    def load_profile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "Pickle Files (*.pickle)")
        if filename:
            try:
                old = self.trader
                self.trader = load_trader_from_file(filename)
                self.statusBar().showMessage(f"Loaded profile from {filename}")
                if old is None:
                    self.showNormal()
                    self.activateWindow()

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                self.select_profile()

    def new_profile(self):
        username, ok = QInputDialog.getText(self, "New Profile", "Enter username:")
        if ok:
            old = self.trader
            self.trader = Trader(username)
            self.statusBar().showMessage(f"Created new profile for {username}")
            if old is None:
                self.showNormal()  # Ensure the main window is shown
                self.activateWindow()

        else:
            self.select_profile()

    def save_profile(self):
        if self.trader:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "Pickle Files (*.pickle)")
            if filename:
                try:
                    store_trader_in_file(self.trader, filename)
                    self.statusBar().showMessage(f"Saved profile to {filename}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "No active profile to save.")

    @update_gui_info
    def buy_stock(self, by_cost):
        if self.trader:
            stock_name = self.stock_name_input.text()
            try:
                if by_cost:
                    cost = float(self.cost_input.text())
                    self.trader.buy(stock_name, cost)
                else:
                    amount = float(self.amount_input.text())
                    self.trader.buy_shares(stock_name, amount)
                self.statusBar().showMessage(f"Bought {stock_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "No active profile.")

    @update_gui_info
    def sell_stock(self, by_cost):
        if self.trader:
            stock_name = self.sell_stock_name_input.text()
            try:
                if by_cost:
                    value = float(self.sell_cost_input.text())
                    self.trader.sell(stock_name, value=value)
                else:
                    amount = float(self.sell_amount_input.text())
                    self.trader.sell(stock_name, amount=amount)
                self.statusBar().showMessage(f"Sold {stock_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "No active profile.")

    @update_gui_info
    def add_money(self, amount):
        if self.trader:
            try:
                self.trader.add_money(amount)
                self.statusBar().showMessage(f"Added ${amount:.2f} to account.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "No active profile.")

    def set_trading_fee(self, fee_percent):
        if self.trader:
            try:
                self.trader.set_fee(fee_percent / 100)  # Convert percentage to decimal
                self.statusBar().showMessage(f"Set trading fee to {fee_percent}%")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "No active profile.")

    def update_finance(self):
        if self.trader:
            try:
                balance = self.trader.balance
                self.balance_label.setText(f"Balance: ${balance:.2f}")
                stock_value = 0
                for stock_name, amount in self.trader.owned.items():
                    price = float(yfinance.Ticker(stock_name).get_info()['currentPrice'])
                    stock_value += price * amount
                revenue = 0
                for trade in self.trader.trades:
                    if trade.amount < 0:
                        revenue -= trade.amount * trade.share_value
                net_worth = balance + stock_value
                self.net_worth_label.setText(f"Net worth: ${net_worth:.2f}")
                self.revenue_label.setText(f"Revenue : ${revenue:.2f}")

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def update_trades(self):
        self.trade_history.clear()
        self.trade_history.setHorizontalHeaderItem(0, QTableWidgetItem("Stock name"))
        self.trade_history.setHorizontalHeaderItem(1, QTableWidgetItem("Amount"))
        self.trade_history.setHorizontalHeaderItem(2, QTableWidgetItem("Share value"))
        self.trade_history.setHorizontalHeaderItem(3, QTableWidgetItem("Purchase time"))
        if self.trader:
            try:
                trades = self.trader.trades
                self.trade_history.setRowCount(len(trades))
                for idx, elem in enumerate(trades):
                    self.trade_history.setItem(idx, 0, QTableWidgetItem(elem.name))
                    self.trade_history.setItem(idx, 1, QTableWidgetItem(f"{elem.amount:g}"))
                    self.trade_history.setItem(idx, 2, QTableWidgetItem(f"{elem.share_value:g}"))
                    self.trade_history.setItem(idx, 3, QTableWidgetItem(f"{elem.purchase_time}"))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def update_available_stocks(self):
        self.sell_stock_name_input.setCompleter(QCompleter(self.fetch_owned_stocks()))

    def fetch_stocks(self):
        return self.stored_tickers

    def fetch_owned_stocks(self):
        if self.trader:
            return self.trader.owned.keys()
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

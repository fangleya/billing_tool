# windows/chart_window.py
import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QLineEdit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime


class ChartWindow(QWidget):
    def __init__(self, transactions):
        super().__init__()
        self.setWindowTitle("📊 图表分析")
        self.setStyleSheet("background-color: #fff; font-family: 微软雅黑; font-size: 14px;")
        self.setMinimumSize(800, 500)
        self.transactions = transactions

        layout = QVBoxLayout(self)

        self.label = QLabel("分类支出饼图 + 月度收支柱状图")
        layout.addWidget(self.label)

        # ✅ 筛选器布局
        self.cmb_account = QComboBox()
        self.cmb_account.addItem("全部账户")
        for acc in sorted(set(t.account for t in transactions)):
            self.cmb_account.addItem(acc)
        self.cmb_account.currentIndexChanged.connect(self.plot)

        self.txt_tag_filter = QLineEdit()
        self.txt_tag_filter.setPlaceholderText("标签包含关键字")
        self.txt_tag_filter.textChanged.connect(self.plot)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("账户筛选："))
        filter_layout.addWidget(self.cmb_account)
        filter_layout.addWidget(QLabel("标签关键词："))
        filter_layout.addWidget(self.txt_tag_filter)
        layout.addLayout(filter_layout)

        self.canvas = FigureCanvas(Figure(figsize=(10, 5)))
        layout.addWidget(self.canvas)

        self.plot()

    def plot(self):
        account_filter = self.cmb_account.currentText()
        tag_keyword = self.txt_tag_filter.text().strip().lower()

        filtered = []
        for t in self.transactions:
            if account_filter != "全部账户" and t.account != account_filter:
                continue
            if tag_keyword and tag_keyword not in t.tags.lower():
                continue
            filtered.append(t)

        self.canvas.figure.clear()
        ax1 = self.canvas.figure.add_subplot(121)
        ax2 = self.canvas.figure.add_subplot(122)

        categories = {}
        for t in filtered:
            if t.type == "支出":
                key = t.category
                categories[key] = categories.get(key, 0) + t.amount
        if categories:
            ax1.pie(categories.values(), labels=categories.keys(), autopct="%.1f%%", startangle=140)
            ax1.set_title("分类支出比例")
        else:
            ax1.text(0.5, 0.5, "无支出数据", ha="center", va="center", fontsize=12)

        monthly_income = [0] * 12
        monthly_expense = [0] * 12
        for t in filtered:
            try:
                month = datetime.strptime(t.date, "%Y-%m-%d").month - 1
                if t.type == "收入":
                    monthly_income[month] += t.amount
                else:
                    monthly_expense[month] += t.amount
            except:
                continue

        x = range(1, 13)
        ax2.bar(x, monthly_income, width=0.4, label="收入", align="center", color="#4CAF50")
        ax2.bar([i + 0.4 for i in x], monthly_expense, width=0.4, label="支出", align="center", color="#F44336")
        ax2.set_xticks([i + 0.2 for i in x])
        ax2.set_xticklabels([f"{i}月" for i in x])
        ax2.legend()
        ax2.set_title("月度收支")

        self.canvas.draw()

# windows/chart_window.py
import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QLineEdit,
)
from PyQt5.QtCore import QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
from matplotlib.figure import Figure
from datetime import datetime
from widgets.year_month_picker import YearMonthPicker
from widgets.styled_combo import StyledComboBox


class ChartWindow(QWidget):
    def __init__(self, transactions):
        super().__init__()
        self.setWindowTitle("📊 图表分析")
        self.setStyleSheet("""
            QWidget {
                background-color: #fff;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding-left: 5px;
                background-color: #fff;
                color: #333;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                outline: 0px;
                border: 1px solid #ccc;
                selection-background-color: #4CAF50;
                selection-color: white;
                color: #333;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QComboBox QAbstractItemView::item {
                height: 28px;
                padding-left: 8px;
                color: #333;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #81c784;
                color: black;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding-left: 5px;
                background-color: #fff;
                color: #333;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QDateEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding-left: 5px;
                background-color: #fff;
                color: #333;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QCalendarWidget {
                background-color: white;
                color: #333;
            }
            QCalendarWidget QToolButton {
                color: #333;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px 6px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e8f5e9;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #333;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                color: #333;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #333;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #ccc;
            }
        """)
        self.setMinimumSize(900, 550)
        self.transactions = transactions

        # 获取所有年份
        years = set()
        for t in transactions:
            try:
                years.add(datetime.strptime(t.date, "%Y-%m-%d").year)
            except:
                pass
        if not years:
            years = {QDate.currentDate().year()}
        self.available_years = sorted(years, reverse=True)

        layout = QVBoxLayout(self)

        self.label = QLabel("分类支出饼图 + 月度收支柱状图")
        layout.addWidget(self.label)

        # 第一行：年份选择 + 日期筛选
        row1 = QHBoxLayout()

        row1.addWidget(QLabel("日期筛选:"))
        self.date_picker = YearMonthPicker(years=self.available_years)
        self.date_picker.selectionChanged.connect(self.plot)
        self.date_picker.select_current()
        row1.addWidget(self.date_picker)

        row1.addWidget(QLabel("收支年份:"))
        self.year_combo = StyledComboBox()
        self.year_combo.addItems([str(y) for y in self.available_years])
        self.year_combo.setFixedHeight(32)
        self.year_combo.currentIndexChanged.connect(self.plot)
        row1.addWidget(self.year_combo)

        row1.addStretch()
        layout.addLayout(row1)

        # 第二行：账户 + 标签
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("账户筛选："))
        self.cmb_account = StyledComboBox()
        self.cmb_account.addItem("全部账户")
        for acc in sorted(set(t.account for t in transactions)):
            self.cmb_account.addItem(acc)
        self.cmb_account.currentIndexChanged.connect(self.plot)
        filter_layout.addWidget(QLabel("标签关键词："))
        self.txt_tag_filter = QLineEdit()
        self.txt_tag_filter.setPlaceholderText("标签包含关键字")
        self.txt_tag_filter.textChanged.connect(self.plot)

        filter_layout.addWidget(self.cmb_account)
        filter_layout.addWidget(self.txt_tag_filter)
        layout.addLayout(filter_layout)

        self.canvas = FigureCanvas(Figure(figsize=(10, 5)))
        layout.addWidget(self.canvas)

        self.plot()

    def plot(self, _=None):
        account_filter = self.cmb_account.currentText()
        tag_keyword = self.txt_tag_filter.text().strip().lower()
        selected_year = int(self.year_combo.currentText())

        # 饼图数据：根据日期选择器筛选
        pie_filtered = []
        for t in self.transactions:
            if account_filter != "全部账户" and t.account != account_filter:
                continue
            if tag_keyword and tag_keyword not in t.tags.lower():
                continue
            if not self.date_picker.matches_date_filter(t.date):
                continue
            pie_filtered.append(t)

        # 柱状图数据：使用选定年份，不受日期筛选影响
        bar_filtered = []
        for t in self.transactions:
            try:
                year = datetime.strptime(t.date, "%Y-%m-%d").year
            except:
                continue
            if year != selected_year:
                continue
            if account_filter != "全部账户" and t.account != account_filter:
                continue
            if tag_keyword and tag_keyword not in t.tags.lower():
                continue
            bar_filtered.append(t)

        self.canvas.figure.clear()
        ax1 = self.canvas.figure.add_subplot(121)
        ax2 = self.canvas.figure.add_subplot(122)

        # 分类支出饼图
        categories = {}
        for t in pie_filtered:
            if t.type == "支出":
                key = t.category
                categories[key] = categories.get(key, 0) + t.amount

        if categories:
            total = sum(categories.values())
            # 将比例小于 1% 的分类合并，标签显示为分类名称拼接
            main_categories = {}
            other_amount = 0.0
            other_names = []
            for name, amount in categories.items():
                pct = amount / total * 100 if total > 0 else 0
                if pct < 1.0:
                    other_amount += amount
                    other_names.append(name)
                else:
                    main_categories[name] = amount
            if other_amount > 0:
                main_categories["+".join(other_names)] = other_amount

            labels = list(main_categories.keys())
            values = list(main_categories.values())
            ax1.pie(values, labels=labels, autopct="%.1f%%", startangle=140)  # type: ignore
            ax1.set_title("分类支出比例")
        else:
            ax1.text(0.5, 0.5, "无支出数据", ha="center", va="center", fontsize=12)

        # 月度收支柱状图（使用选定年份的数据）
        monthly_income = [0] * 12
        monthly_expense = [0] * 12
        for t in bar_filtered:
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
        ax2.set_title(f"{selected_year}年 月度收支")

        self.canvas.draw()

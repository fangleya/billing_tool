import sys, os, json, csv
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QMessageBox,
    QMenu,
    QFileDialog,
    QApplication,
    QStyleFactory,
)
from PyQt5.QtCore import Qt, QDate, QPoint, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from models.transaction import Transaction
from windows.chart_window import ChartWindow
from windows.category_window import CategoryWindow
from windows.account_window import AccountWindow
from windows.edit_window import EditWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # ✅ 强制 Qt 样式 + 设置选中颜色
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        palette = QPalette()
        palette.setColor(QPalette.Highlight, QColor("#4CAF50"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        QApplication.setPalette(palette)

        self.setWindowTitle(" 本地记账工具v1.0")
        self.setWindowIcon(QIcon(os.path.join("resources", "appicon.ico")))

        self.setStyleSheet("""
            QWidget {
                background-color: #fefefe;
                font-family: '微软雅黑';
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding-left: 5px;
                background-color: #fff;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                outline: 0px;
                border: 1px solid #ccc;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QComboBox QAbstractItemView::item {
                height: 28px;
                padding-left: 8px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #81c784;
                color: black;
            }
        """)
        self.resize(900, 700)

        self.transactions = []
        self.categories = ["餐饮", "购物", "交通", "工资", "娱乐", "其他"]
        self.accounts = ["银行卡", "微信", "支付宝", "现金"]
        self.default_col_ratios = [0.10, 0.08, 0.08, 0.10, 0.10, 0.10, 0.16, 0.28]
        self.col_ratios = list(self.default_col_ratios)
        self._load_col_ratios()
        self.load_data()

        layout = QVBoxLayout(self)

        # ✅ 顶部按钮区域（含“关于”）
        top_buttons = QHBoxLayout()
        for name, handler in [
            ("📊 图表分析", self.open_chart),
            ("📁 分类管理", self.open_category),
            ("💳 账户管理", self.open_account),
            ("📤 导出 CSV", self.export_csv),
            ("❓ 关于", self.show_about),
        ]:
            btn = QPushButton(name)
            btn.setFixedHeight(32)
            btn.clicked.connect(handler)
            top_buttons.addWidget(btn)
        layout.addLayout(top_buttons)

        # 输入区域
        input_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["收入", "支出"])
        self.cmb_category = QComboBox()
        self.update_categories()
        self.cmb_account = QComboBox()
        self.cmb_account.addItems(self.accounts)
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("描述")
        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("金额")
        self.txt_tags = QLineEdit()
        self.txt_tags.setPlaceholderText("标签（逗号分隔）")
        self.txt_note = QLineEdit()
        self.txt_note.setPlaceholderText("备注")
        self.btn_add = QPushButton("➕ 添加")
        self.btn_add.clicked.connect(self.add_transaction)

        for w in [
            self.date_edit,
            self.cmb_type,
            self.cmb_category,
            self.cmb_account,
            self.txt_desc,
            self.txt_amount,
            self.txt_tags,
            self.txt_note,
            self.btn_add,
        ]:
            w.setFixedHeight(32)
            input_layout.addWidget(w)
        layout.addLayout(input_layout)

        # 表格区域
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["日期", "类型", "分类", "描述", "金额", "账户", "标签", "备注"])
        self.table.horizontalHeader().setStretchLastSection(False)  # type: ignore
        self.table.horizontalHeader().sectionResized.connect(self.on_column_resized)  # type: ignore
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.table)

        # 汇总信息
        self.lbl_summary = QLabel()
        self.lbl_summary.setFont(QFont("微软雅黑", 12, QFont.Bold))
        layout.addWidget(self.lbl_summary)

        self.refresh_table()
        self.restore_window_state()

        # ⏱ 自动检查提醒事项
        self.check_reminders()

    def _load_col_ratios(self):
        try:
            with open("data/window_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
            self.col_ratios = state.get("col_ratios")
            # saved = state.get("col_ratios")
            # if saved and len(saved) == 8:
            #     self.col_ratios = [round(r, 3) for r in saved]
        except Exception:
            pass

    def restore_window_state(self):
        try:
            with open("data/window_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

        if state.get("maximized", True):
            self.showMaximized()
        else:
            geo = state.get("geometry")
            if geo and len(geo) == 4:
                self.setGeometry(*geo)
            else:
                self.resize(900, 700)
            self.show()
        QTimer.singleShot(0, self.adjust_column_widths)

    def closeEvent(self, event):
        total_width = self.table.viewport().width()  # type: ignore
        print(f"[closeEvent1] total_width={total_width}, col_ratios={self.col_ratios}")
        # if total_width > 0:
        #     self.col_ratios = [self.table.columnWidth(i) / total_width for i in range(8)]
        # self.col_ratios = [round(r, 3) for r in saved]
        os.makedirs("data", exist_ok=True)
        total_width = self.table.viewport().width()  # type: ignore
        print(f"[closeEvent2] total_width={total_width}, col_ratios={self.col_ratios}")
        rect = self.geometry().getRect()
        state = {
            "maximized": self.isMaximized(),
            "geometry": [rect[0], rect[1], rect[2], rect[3]],
            # "col_ratios": [round(r, 3) for r in self.col_ratios],
            "col_ratios": self.col_ratios,
        }
        with open("data/window_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f)
        event.accept()

    def check_reminders(self):
        try:
            with open("data/reminder.json", "r", encoding="utf-8") as f:
                reminders = json.load(f)
        except:
            return
        today = QDate.currentDate().toString("yyyy-MM-dd")
        messages = [
            f"{r['date']} - {r['title']}：¥{r['amount']}\n备注：{r['note']}" for r in reminders if r["date"] == today
        ]
        if messages:
            QMessageBox.information(self, "📅 今日提醒", "\n\n".join(messages))

    def show_about(self):
        QMessageBox.information(
            self,
            "关于 💰 记账工具",
            "软件名称：本地记账工具\n"
            "功能简介：记录每日收支，支持图表分析、分类与账户管理、导出 CSV。\n"
            "版本号：v1.0\n"
            "作者：Thebzk  吾爱破解\n"
            "日期：2025年5月26日",
        )

    def add_transaction(self):
        try:
            t = Transaction(
                date=self.date_edit.date().toString("yyyy-MM-dd"),
                type=self.cmb_type.currentText(),
                category=self.cmb_category.currentText(),
                description=self.txt_desc.text(),
                amount=float(self.txt_amount.text()),
                account=self.cmb_account.currentText(),
                tags=self.txt_tags.text(),
                note=self.txt_note.text(),
            )
            self.transactions.append(t)
            self.save_data()
            self.refresh_table()
            for w in [self.txt_desc, self.txt_amount, self.txt_tags, self.txt_note]:
                w.clear()
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入合法的金额")

    def refresh_table(self):
        self.table.setRowCount(0)
        income = expense = 0
        for t in self.transactions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [t.date, t.type, t.category, t.description, f"{t.amount:.2f}", t.account, t.tags, t.note]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
            income += t.amount if t.type == "收入" else 0
            expense += t.amount if t.type == "支出" else 0
        self.lbl_summary.setText(f"总收入：¥{income:.2f}，总支出：¥{expense:.2f}，余额：¥{income - expense:.2f}")

    def adjust_column_widths(self):
        total_width = self.table.viewport().width()  # type: ignore
        for i, ratio in enumerate(self.col_ratios):
            self.table.setColumnWidth(i, int(total_width * ratio))

    def on_column_resized(self, index, old_size, new_size):
        headers = ["日期", "类型", "分类", "描述", "金额", "账户", "标签", "备注"]
        name = headers[index] if index < len(headers) else f"col{index}"
        total = self.table.viewport().width()  # type: ignore
        pct = new_size / total * 100 if total > 0 else 0
        self.col_ratios = [round(self.table.columnWidth(i) / total, 3) for i in range(8)]
        # total_width = self.table.viewport().width()  # type: ignore
        # if total_width > 0:
        #     self.col_ratios = [self.table.columnWidth(i) / total_width for i in range(8)]
        # self.col_ratios = [round(r, 3) for r in saved]
        print(f"[columnResized] {name}[{index}]: {old_size} -> {new_size} ({pct:.1f}% of {total})")
        print(f"  updated col_ratios: {self.col_ratios}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()

    def open_context_menu(self, pos: QPoint):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        menu = QMenu()
        act_edit = menu.addAction("✏️ 编辑")
        act_del = menu.addAction("🗑 删除")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))  # type: ignore
        if action == act_edit:
            self.edit_transaction(row)
        elif action == act_del:
            del self.transactions[row]
            self.save_data()
            self.refresh_table()

    def edit_transaction(self, row):
        old = self.transactions[row]

        def save_callback(updated):
            self.transactions[row] = updated
            self.save_data()
            self.refresh_table()

        self.edit_win = EditWindow(old, self.categories, self.accounts, save_callback)
        self.edit_win.show()

    def save_data(self):
        os.makedirs("data", exist_ok=True)
        with open("data/transactions.json", "w", encoding="utf-8") as f:
            json.dump([t.__dict__ for t in self.transactions], f, indent=2, ensure_ascii=False)

    def load_data(self):
        try:
            with open("data/transactions.json", "r", encoding="utf-8") as f:
                self.transactions = [Transaction(**d) for d in json.load(f)]
        except:
            pass

    def open_chart(self):
        self.chart_win = ChartWindow(self.transactions)
        self.chart_win.show()

    def open_category(self):
        self.cat_win = CategoryWindow(self.categories, self.update_categories)
        self.cat_win.show()

    def open_account(self):
        self.acc_win = AccountWindow(self.accounts, self.update_accounts)
        self.acc_win.show()

    def update_categories(self):
        self.cmb_category.clear()
        for cat in self.categories:
            icon_path = os.path.join("resources", "icons", f"{cat}.png")
            if os.path.exists(icon_path):
                self.cmb_category.addItem(QIcon(icon_path), cat)
            else:
                self.cmb_category.addItem(cat)

    def update_accounts(self):
        self.cmb_account.clear()
        self.cmb_account.addItems(self.accounts)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出为 CSV 文件", "账本.csv", "CSV 文件 (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["日期", "类型", "分类", "描述", "金额", "账户", "标签", "备注"])
            for t in self.transactions:
                writer.writerow([t.date, t.type, t.category, t.description, t.amount, t.account, t.tags, t.note])
        QMessageBox.information(self, "导出成功", f"数据已导出到：\n{path}")

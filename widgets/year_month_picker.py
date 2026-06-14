# widgets/year_month_picker.py
"""年月选择组件：点击弹出选择框，选择后显示选中内容，支持清除"""

import calendar
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QDialog,
    QLabel,
    QComboBox,
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt
from PyQt5.QtGui import QFont


class YearMonthPicker(QWidget):
    """年月选择器

    默认不显示任何年月（表示不筛选）。
    点击按钮弹出对话框选择年份和月份。
    - 只选年份：筛选该年全部记录
    - 只选月份：默认当前年份 + 该月份
    - 都选：筛选指定年月
    - 都不选：不筛选
    """

    selectionChanged = pyqtSignal()

    def __init__(self, years=None, parent=None):
        super().__init__(parent)
        self.selected_year = None  # None 表示未选择
        self.selected_month = None  # None 表示未选择

        if years:
            self.years = list(years)
        else:
            current = QDate.currentDate().year()
            self.years = list(range(current, current - 10, -1))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.btn_display = QPushButton("选择年月")
        self.btn_display.setFixedHeight(32)
        self.btn_display.setMinimumWidth(100)
        self.btn_display.clicked.connect(self.open_dialog)
        layout.addWidget(self.btn_display)

        self.btn_clear = QPushButton("✕")
        self.btn_clear.setFixedSize(24, 32)
        self.btn_clear.clicked.connect(self.clear_selection)
        self.btn_clear.setVisible(False)
        self.btn_clear.setToolTip("清除日期筛选")
        layout.addWidget(self.btn_clear)

    def open_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("选择年月")
        dialog.setFixedSize(280, 160)
        dialog.setStyleSheet(
            "QDialog { background-color: #fff; }"
            "QLabel { font-family: '微软雅黑'; font-size: 14px; color: #333; }"
            "QComboBox { border: 1px solid #ccc; border-radius: 4px; padding-left: 5px;"
            "  background-color: #fff; color: #333; font-family: '微软雅黑'; font-size: 14px; }"
            "QComboBox QAbstractItemView { background-color: white; color: #333;"
            "  font-family: '微软雅黑'; font-size: 14px; selection-background-color: #4CAF50; }"
            "QPushButton { background-color: #4CAF50; color: white; border: none;"
            "  border-radius: 4px; padding: 5px 16px; font-family: '微软雅黑'; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        dlg_layout = QVBoxLayout(dialog)

        # 年份行
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("年份:"))
        year_combo = QComboBox()
        year_combo.addItem("全部")
        for y in self.years:
            year_combo.addItem(str(y))
        if self.selected_year is not None:
            idx = year_combo.findText(str(self.selected_year))
            if idx >= 0:
                year_combo.setCurrentIndex(idx)
        year_layout.addWidget(year_combo)
        dlg_layout.addLayout(year_layout)

        # 月份行
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("月份:"))
        month_combo = QComboBox()
        month_combo.addItem("全部")
        for m in range(1, 13):
            month_combo.addItem(f"{m}月")
        if self.selected_month is not None:
            idx = month_combo.findText(f"{self.selected_month}月")
            if idx >= 0:
                month_combo.setCurrentIndex(idx)
        month_layout.addWidget(month_combo)
        dlg_layout.addLayout(month_layout)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)
        dlg_layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            year_text = year_combo.currentText()
            month_text = month_combo.currentText()
            current_year = QDate.currentDate().year()

            # 都没选 → 清除
            if year_text == "全部" and month_text == "全部":
                self.clear_selection()
                return

            # 只选了月份 → 默认当前年份
            if year_text == "全部":
                self.selected_year = current_year
            else:
                self.selected_year = int(year_text)

            # 月份选了"全部" → 只按年筛选
            if month_text == "全部":
                self.selected_month = None
            else:
                self.selected_month = int(month_text.replace("月", ""))

            self.update_display()
            self.selectionChanged.emit()

    def clear_selection(self):
        self.selected_year = None
        self.selected_month = None
        self.update_display()
        self.selectionChanged.emit()

    def update_display(self):
        if self.selected_year is None:
            self.btn_display.setText("选择年月")
            self.btn_clear.setVisible(False)
        elif self.selected_month is None:
            self.btn_display.setText(f"{self.selected_year}年")
            self.btn_clear.setVisible(True)
        else:
            self.btn_display.setText(f"{self.selected_year}年{self.selected_month}月")
            self.btn_clear.setVisible(True)

    def has_filter(self):
        """是否有有效的日期筛选"""
        return self.selected_year is not None

    def get_filter_start_date(self):
        """返回筛选开始日期 yyyy-MM-dd，无筛选返回 None"""
        if self.selected_year is None:
            return None
        if self.selected_month is None:
            return f"{self.selected_year}-01-01"
        return f"{self.selected_year}-{self.selected_month:02d}-01"

    def get_filter_end_date(self):
        """返回筛选结束日期 yyyy-MM-dd，无筛选返回 None"""
        if self.selected_year is None:
            return None
        if self.selected_month is None:
            return f"{self.selected_year}-12-31"
        last_day = calendar.monthrange(self.selected_year, self.selected_month)[1]
        return f"{self.selected_year}-{self.selected_month:02d}-{last_day:02d}"

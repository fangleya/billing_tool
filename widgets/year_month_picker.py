# widgets/year_month_picker.py
"""年月选择组件：两个下拉框直接选择年份和月份，无需弹窗"""

import calendar
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox
from PyQt5.QtCore import QDate, pyqtSignal
from PyQt5.QtGui import QFont


class YearMonthPicker(QWidget):
    """年月选择器

    两个下拉框直接选择年份和月份，无需弹窗。
    - 都选"全部"：不筛选
    - 只选年份：筛选该年全部记录
    - 只选月份：默认当前年份 + 该月份
    - 都选：筛选指定年月
    """

    selectionChanged = pyqtSignal()

    def __init__(self, years=None, parent=None):
        super().__init__(parent)

        if years:
            self.years = list(years)
        else:
            current = QDate.currentDate().year()
            self.years = list(range(current, current - 10, -1))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 年份下拉
        self.year_combo = QComboBox()
        self.year_combo.addItem("全部")
        for y in self.years:
            self.year_combo.addItem(str(y))
        self.year_combo.setFixedHeight(32)
        self.year_combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.year_combo)

        # 月份下拉
        self.month_combo = QComboBox()
        self.month_combo.addItem("全部")
        for m in range(1, 13):
            self.month_combo.addItem(f"{m}月")
        self.month_combo.setFixedHeight(32)
        self.month_combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.month_combo)

        # 清除按钮
        self.btn_clear = QPushButton("✕")
        self.btn_clear.setFixedSize(24, 32)
        self.btn_clear.clicked.connect(self.clear_selection)
        self.btn_clear.setToolTip("清除日期筛选")
        layout.addWidget(self.btn_clear)

        self._apply_combo_fonts()

    def _apply_combo_fonts(self):
        """统一设置下拉框字体"""
        font = QFont("微软雅黑", 10)
        for combo in (self.year_combo, self.month_combo):
            combo.setFont(font)
            view = combo.view()
            if view:
                view.setFont(font)

    def _on_selection_changed(self):
        """下拉选择变化时发出信号"""
        self.selectionChanged.emit()

    def clear_selection(self):
        """重置为'全部'"""
        self.year_combo.blockSignals(True)
        self.year_combo.setCurrentIndex(0)
        self.year_combo.blockSignals(False)

        self.month_combo.blockSignals(True)
        self.month_combo.setCurrentIndex(0)
        self.month_combo.blockSignals(False)

        self.selectionChanged.emit()

    def _get_selected_year(self):
        """返回选中的年份，'全部'返回 None"""
        text = self.year_combo.currentText()
        return None if text == "全部" else int(text)

    def _get_selected_month(self):
        """返回选中的月份，'全部'返回 None"""
        text = self.month_combo.currentText()
        return None if text == "全部" else int(text.replace("月", ""))

    def has_filter(self):
        """是否有有效的日期筛选"""
        return self._get_selected_year() is not None

    def get_filter_start_date(self):
        """返回筛选开始日期 yyyy-MM-dd，无筛选返回 None"""
        year = self._get_selected_year()
        month = self._get_selected_month()

        if year is None and month is None:
            return None

        # 只选了月份 → 默认当前年份
        if year is None:
            year = QDate.currentDate().year()

        if month is None:
            return f"{year}-01-01"
        return f"{year}-{month:02d}-01"

    def get_filter_end_date(self):
        """返回筛选结束日期 yyyy-MM-dd，无筛选返回 None"""
        year = self._get_selected_year()
        month = self._get_selected_month()

        if year is None and month is None:
            return None

        # 只选了月份 → 默认当前年份
        if year is None:
            year = QDate.currentDate().year()

        if month is None:
            return f"{year}-12-31"
        last_day = calendar.monthrange(year, month)[1]
        return f"{year}-{month:02d}-{last_day:02d}"

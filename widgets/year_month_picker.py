# widgets/year_month_picker.py
"""年月选择组件：两个下拉框直接选择年份和月份，无需弹窗"""

import calendar
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import QDate, pyqtSignal
from widgets.styled_combo import StyledComboBox


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
        self.year_combo = StyledComboBox()
        self.year_combo.addItem("全部")
        for y in self.years:
            self.year_combo.addItem(str(y))
        self.year_combo.setFixedHeight(32)
        self.year_combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.year_combo)

        # 月份下拉
        self.month_combo = StyledComboBox()
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

    def select_current(self):
        """选中当前年份和月份（不触发信号）"""
        current_year = QDate.currentDate().year()
        current_month = QDate.currentDate().month()

        self.year_combo.blockSignals(True)
        idx = self.year_combo.findText(str(current_year))
        if idx >= 0:
            self.year_combo.setCurrentIndex(idx)
        self.year_combo.blockSignals(False)

        self.month_combo.blockSignals(True)
        idx = self.month_combo.findText(f"{current_month}月")
        if idx >= 0:
            self.month_combo.setCurrentIndex(idx)
        self.month_combo.blockSignals(False)

    def _on_selection_changed(self, _=None):
        """下拉选择变化时发出信号"""
        self.selectionChanged.emit()

    def set_years(self, years):
        """动态更新年份选项（保留当前选中状态）"""
        if not years:
            return
        new_years = sorted(years, reverse=True)
        if new_years == self.years:
            return
        self.years = new_years
        current = self.year_combo.currentText()
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        self.year_combo.addItem("全部")
        for y in self.years:
            self.year_combo.addItem(str(y))
        # 恢复之前选中的年份
        idx = self.year_combo.findText(current)
        if idx >= 0:
            self.year_combo.setCurrentIndex(idx)
        self.year_combo.blockSignals(False)

    def clear_selection(self, _=None):
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
        return self._get_selected_year() is not None or self._get_selected_month() is not None

    def matches_date_filter(self, date_str):
        """判断给定日期 yyyy-MM-dd 是否匹配当前筛选条件

        - 都未选：匹配所有
        - 只选年份：匹配该年
        - 只选月份：匹配所有年份的该月份
        - 都选：匹配指定年月
        """
        year = self._get_selected_year()
        month = self._get_selected_month()

        if year is None and month is None:
            return True
        if year is not None and month is None:
            return date_str[:4] == str(year)
        if year is None and month is not None:
            return date_str[5:7] == f"{month:02d}"
        return date_str[:7] == f"{year}-{month:02d}"

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

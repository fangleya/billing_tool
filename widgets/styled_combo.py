# widgets/styled_combo.py
"""统一样式的 QComboBox 子类，自动处理字体和下拉列表样式"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class StyledComboBox(QComboBox):
    """统一样式的下拉框

    自动设置自身及下拉列表的字体，确保下拉选项字体与整体 UI 一致。
    替代 QComboBox 使用，无需手动调用 _set_combo_item_fonts 等方法。

    Parameters
    ----------
    font_size : int
        字体大小，默认 14。
    font_family : str
        字体名称，默认 "微软雅黑"。
    """

    _DEFAULT_FONT_FAMILY = "微软雅黑"
    _DEFAULT_FONT_SIZE = 10

    def __init__(self, parent=None, *, font_size=None, font_family=None):
        super().__init__(parent)
        self._font_family = font_family or self._DEFAULT_FONT_FAMILY
        self._font_size = font_size or self._DEFAULT_FONT_SIZE
        self._styled_font = QFont(self._font_family, self._font_size)
        self.setFont(self._styled_font)
        self._apply_view_font()

    def _apply_view_font(self):
        """设置下拉列表视图的字体"""
        view = self.view()
        if view:
            view.setFont(self._styled_font)

    def showPopup(self):
        """弹出下拉列表前确保所有条目字体正确"""
        self._apply_view_font()
        model = self.model()
        if model:
            for i in range(self.count()):
                model.setData(model.index(i, 0), self._styled_font, Qt.ItemDataRole.FontRole)
        super().showPopup()

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from windows.main_window import MainWindow  # ✅ 修正路径

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setFont(QFont("微软雅黑", 12))
    app.setStyle("Fusion")  # ✅ 强制 Qt 样式以让样式表生效
    # app.setStyleSheet("""
    #     QComboBox QAbstractItemView {
    #         font-family: '微软雅黑';
    #         font-size: 12px;
    #     }
    #     QComboBox QAbstractItemView::item {
    #         font-family: '微软雅黑';
    #         font-size: 12px;
    #     }
    # """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

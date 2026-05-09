import sys
from PyQt5.QtWidgets import QApplication
from windows.main_window import MainWindow  # ✅ 修正路径

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # ✅ 强制 Qt 样式以让样式表生效
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

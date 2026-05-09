from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox

class CategoryWindow(QWidget):
    def __init__(self, categories: list, update_callback):
        super().__init__()
        self.setWindowTitle("📁 分类管理")
        self.setFixedSize(300, 400)
        self.setStyleSheet("background-color: #fff; font-family: 微软雅黑; font-size: 14px;")
        self.categories = categories
        self.update_callback = update_callback

        layout = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("新分类名称")
        self.btn_add = QPushButton("添加分类")
        self.btn_add.clicked.connect(self.add_category)

        self.list_widget = QListWidget()
        self.refresh_list()

        self.btn_delete = QPushButton("删除选中分类")
        self.btn_delete.clicked.connect(self.delete_category)

        layout.addWidget(self.input)
        layout.addWidget(self.btn_add)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.btn_delete)

    def refresh_list(self):
        self.list_widget.clear()
        for c in self.categories:
            self.list_widget.addItem(QListWidgetItem(c))

    def add_category(self, checked=False):
        name = self.input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入分类名称")
        elif name in self.categories:
            QMessageBox.information(self, "提示", "分类已存在")
        else:
            self.categories.append(name)
            self.refresh_list()
            self.input.clear()
            self.update_callback()

    def delete_category(self, checked=False):
        item = self.list_widget.currentItem()
        if item:
            name = item.text()
            if name in self.categories:
                self.categories.remove(name)
                self.refresh_list()
                self.update_callback()

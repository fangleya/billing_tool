# windows/account_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox

class AccountWindow(QWidget):
    def __init__(self, accounts: list, update_callback):
        super().__init__()
        self.setWindowTitle("💳 账户管理")
        self.setFixedSize(300, 400)
        self.setStyleSheet("background-color: #fff; font-family: 微软雅黑; font-size: 14px;")
        self.accounts = accounts
        self.update_callback = update_callback

        layout = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("新账户名称")
        self.btn_add = QPushButton("添加账户")
        self.btn_add.clicked.connect(self.add_account)

        self.list_widget = QListWidget()
        self.refresh_list()

        self.btn_delete = QPushButton("删除选中账户")
        self.btn_delete.clicked.connect(self.delete_account)

        layout.addWidget(self.input)
        layout.addWidget(self.btn_add)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.btn_delete)

    def refresh_list(self):
        self.list_widget.clear()
        for a in self.accounts:
            self.list_widget.addItem(QListWidgetItem(a))

    def add_account(self, checked=False):
        name = self.input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入账户名称")
        elif name in self.accounts:
            QMessageBox.information(self, "提示", "账户已存在")
        else:
            self.accounts.append(name)
            self.refresh_list()
            self.input.clear()
            self.update_callback()

    def delete_account(self, checked=False):
        item = self.list_widget.currentItem()
        if item:
            name = item.text()
            if name in self.accounts:
                self.accounts.remove(name)
                self.refresh_list()
                self.update_callback()

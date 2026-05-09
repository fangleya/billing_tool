# windows/edit_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QDateEdit, QMessageBox
from PyQt5.QtCore import QDate
from models.transaction import Transaction

class EditWindow(QWidget):
    def __init__(self, transaction, categories, accounts, save_callback):
        super().__init__()
        self.setWindowTitle("✏️ 编辑交易")
        self.setFixedSize(400, 300)
        self.transaction = transaction
        self.save_callback = save_callback

        layout = QVBoxLayout(self)

        self.date_edit = QDateEdit(QDate.fromString(transaction.date, "yyyy-MM-dd"))
        self.cmb_type = QComboBox(); self.cmb_type.addItems(["收入", "支出"])
        self.cmb_type.setCurrentText(transaction.type)
        self.cmb_cat = QComboBox(); self.cmb_cat.addItems(categories)
        self.cmb_cat.setCurrentText(transaction.category)
        self.cmb_acc = QComboBox(); self.cmb_acc.addItems(accounts)
        self.cmb_acc.setCurrentText(transaction.account)
        self.txt_desc = QLineEdit(transaction.description)
        self.txt_amount = QLineEdit(str(transaction.amount))
        self.txt_tags = QLineEdit(transaction.tags)
        self.txt_note = QLineEdit(transaction.note)

        for w in [self.date_edit, self.cmb_type, self.cmb_cat, self.cmb_acc,
                  self.txt_desc, self.txt_amount, self.txt_tags, self.txt_note]:
            layout.addWidget(w)

        btn = QPushButton("保存")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        try:
            t = Transaction(
                date=self.date_edit.date().toString("yyyy-MM-dd"),
                type=self.cmb_type.currentText(),
                category=self.cmb_cat.currentText(),
                description=self.txt_desc.text(),
                amount=float(self.txt_amount.text()),
                account=self.cmb_acc.currentText(),
                tags=self.txt_tags.text(),
                note=self.txt_note.text()
            )
            self.save_callback(t)
            self.close()
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入合法金额")

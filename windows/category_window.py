from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QInputDialog,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt


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
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)  # type: ignore
        self.list_widget.itemDoubleClicked.connect(self.edit_category)
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
            item = QListWidgetItem(c)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.list_widget.addItem(item)

    def on_rows_moved(self, _parent, _start, _end, _dest_parent, _dest_row):
        """拖拽排序后同步更新 categories 列表"""
        new_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                new_order.append(item.text())
        self.categories[:] = new_order
        self.update_callback()

    def edit_category(self, item):
        """双击编辑分类名称"""
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self, "编辑分类", "请输入新的分类名称：", QLineEdit.Normal, old_name
        )
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name == old_name:
                return
            if new_name in self.categories:
                QMessageBox.information(self, "提示", "分类已存在")
                return
            idx = self.categories.index(old_name)
            self.categories[idx] = new_name
            self.refresh_list()
            self.update_callback()

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

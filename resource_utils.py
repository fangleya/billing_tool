# resource_utils.py
"""PyInstaller 打包路径工具

- get_resource_path(): 用于只读资源（图片、图标等），打包后从临时目录读取
- get_data_path(): 用于可读写数据文件，打包后从 exe 同级目录读取
"""

import sys
import os


def get_base_path():
    """获取运行时的根目录

    开发环境：当前工作目录
    PyInstaller 打包（单文件）：sys._MEIPASS（临时解压目录）
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore
    return os.getcwd()


def get_resource_path(relative_path):
    """获取只读资源文件的绝对路径（图片、图标等）

    开发环境：相对于当前工作目录
    打包后：相对于 sys._MEIPASS 临时目录
    """
    return os.path.join(get_base_path(), relative_path)


def get_data_path(relative_path):
    """获取可读写数据文件的绝对路径

    开发环境：相对于当前工作目录
    打包后：相对于 exe 所在目录（确保数据持久化）
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.getcwd()
    full = os.path.join(base, relative_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full

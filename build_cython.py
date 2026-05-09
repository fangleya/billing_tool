"""Cython 加密编译 & 清理脚本"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    py_files = []
    for f in ROOT.rglob("*.py"):
        if f.name in ("build_cython.py", "main.py", "__init__.py"):
            continue
        if "__pycache__" in str(f):
            continue
        py_files.append(str(f.relative_to(ROOT)).replace("\\", "/"))

    if not py_files:
        print("[build_cython] 没有找到需要编译的 .py 文件")
        return 1

    print(f"[build_cython] 编译 {len(py_files)} 个文件: {py_files}")

    setup_code = f"""import sys
from setuptools import setup
from Cython.Build import cythonize

sys.argv = ["setup.py", "build_ext", "--inplace"]

setup(
    ext_modules=cythonize({py_files!r}, language_level=3),
    script_args=["build_ext", "--inplace"],
)
"""
    setup_path = ROOT / "_cython_setup.py"
    setup_path.write_text(setup_code, encoding="utf-8")

    try:
        result = subprocess.run(
            [sys.executable, str(setup_path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[build_cython] 编译失败:\n{result.stdout}\n{result.stderr}")
            return 1

        print("[build_cython] 编译完成，清理文件...")

        # 删除 .pyd
        for f in ROOT.rglob("*.pyd"):
            if f.name.startswith("_cython_setup"):
                continue
            f.unlink()
            print(f"  删除: {f.relative_to(ROOT)}")

        # 删除 .c 中间文件
        for f in ROOT.rglob("*.c"):
            if "_cython_setup" in f.name:
                continue
            f.unlink()
            print(f"  删除: {f.relative_to(ROOT)}")

        # 删除 __pycache__
        for d in ROOT.rglob("__pycache__"):
            shutil.rmtree(d)
            print(f"  删除: {d.relative_to(ROOT)}/")

        # 删除 build / dist 目录
        for d in ("build", "dist"):
            p = ROOT / d
            if p.exists():
                shutil.rmtree(p)
                print(f"  删除: {d}/")

        print("[build_cython] 清理完成！")

    finally:
        if setup_path.exists():
            setup_path.unlink()
        egg_info = ROOT / "_cython_setup.egg-info"
        if egg_info.exists():
            shutil.rmtree(egg_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
一键 CPython 加密打包脚本
自动检测环境 → 扫描代码依赖 → 安装缺失项 → Cython 编译 .pyd → PyInstaller 打包 .exe
用法：python build.py
"""

import os, sys, shutil, subprocess, site, glob, platform, ast

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(ROOT, "build_temp")
DIST_DIR = os.path.join(ROOT, "dist")
EXE_NAME = "本地记账工具.exe"

# ── 需要编译的子模块（不包含入口 main.py） ──
PY_MODULES = [
    "models/transaction.py",
    "windows/main_window.py",
    "windows/chart_window.py",
    "windows/category_window.py",
    "windows/account_window.py",
    "windows/edit_window.py",
]

# ── 构建工具（代码里不会 import，打包流程本身需要） ──
BUILD_TOOLS = {
    "Cython": "cython",
    "PyInstaller": "pyinstaller",
    "setuptools": "setuptools",
}

# ── import 名 → pip 包名 映射（仅收录无法自动推断的） ──
IMPORT_TO_PIP = {
    "PyQt5": "PyQt5",
    "PyQt5.QtCore": "PyQt5",
    "PyQt5.QtGui": "PyQt5",
    "PyQt5.QtWidgets": "PyQt5",
    "matplotlib": "matplotlib",
    "matplotlib.pyplot": "matplotlib",
    "matplotlib.backends.backend_qt5agg": "matplotlib",
    "matplotlib.figure": "matplotlib",
    "Cython": "Cython",
    "PyInstaller": "pyinstaller",
}


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def run(cmd, **kw):
    """执行命令并实时输出"""
    print(f"  -> {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    return subprocess.run(cmd, check=True, cwd=ROOT, **kw)


# ═══════════════════════════════════════════════════════════════
# 辅助：提取指定模块属于哪个顶层包
# ═══════════════════════════════════════════════════════════════
_STDLIB = None


def _get_stdlib_names():
    """惰性获取当前 Python 版本的标准库名称集合"""
    global _STDLIB
    if _STDLIB is not None:
        return _STDLIB
    _STDLIB = set()
    stdlib_path = os.path.dirname(os.__file__)
    try:
        for name in os.listdir(stdlib_path):
            if name.endswith(".py"):
                _STDLIB.add(name[:-3])
            elif os.path.isdir(os.path.join(stdlib_path, name)) and not name.startswith("_"):
                _STDLIB.add(name)
    except Exception:
        pass
    # 内置异常/类型模块
    _STDLIB |= {
        "sys",
        "os",
        "io",
        "re",
        "json",
        "csv",
        "math",
        "time",
        "datetime",
        "collections",
        "itertools",
        "functools",
        "operator",
        "typing",
        "subprocess",
        "argparse",
        "logging",
        "hashlib",
        "base64",
        "uuid",
        "pathlib",
        "tempfile",
        "shutil",
        "glob",
        "fnmatch",
        "stat",
        "threading",
        "multiprocessing",
        "queue",
        "asyncio",
        "concurrent",
        "socket",
        "ssl",
        "email",
        "http",
        "urllib",
        "xml",
        "html",
        "unittest",
        "doctest",
        "pdb",
        "profile",
        "traceback",
        "warnings",
        "copy",
        "pickle",
        "shelve",
        "marshal",
        "struct",
        "string",
        "textwrap",
        "numbers",
        "decimal",
        "fractions",
        "random",
        "statistics",
        "abc",
        "atexit",
        "codecs",
        "contextlib",
        "dataclasses",
        "enum",
        "gc",
        "inspect",
        "importlib",
        "pkgutil",
        "pydoc",
        "runpy",
        "tokenize",
        "ast",
        "symtable",
        "dis",
        "opcode",
        "ctypes",
        "curses",
        "readline",
        "tkinter",
        "turtle",
        "venv",
        "zipfile",
        "tarfile",
        "gzip",
        "bz2",
        "lzma",
        "platform",
        "locale",
        "gettext",
        "getopt",
        "getpass",
        "signal",
        "mmap",
        "fcntl",
        "termios",
        "tty",
        "pwd",
        "grp",
        "resource",
        "sysconfig",
        "distutils",
        "ensurepip",
        "antigravity",
        "this",
        "__future__",
    }
    return _STDLIB


def _scan_imports(py_file):
    """用 AST 提取单个 .py 文件中所有顶层 import 的包名"""
    imports = set()
    try:
        with open(py_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=py_file)
    except Exception:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def scan_project_dependencies():
    """扫描项目所有 .py，返回需要安装的 pip 包名集合"""
    needed = set()
    for py_file in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True):
        # 跳过构建脚本
        if os.path.basename(py_file) in ("build.py", "build_cython.py"):
            continue
        for imp in _scan_imports(py_file):
            if imp not in _get_stdlib_names():
                # 跳过项目本地模块（ROOT 下存在同名目录或 .py 文件）
                if os.path.isdir(os.path.join(ROOT, imp)) or os.path.isfile(
                    os.path.join(ROOT, imp + ".py")
                ):
                    continue
                needed.add(imp)
    return needed


# ═══════════════════════════════════════════════════════════════
# 辅助：定位 Visual Studio 及 MSVC 编译器
# ═══════════════════════════════════════════════════════════════
_VS_VARS = None  # (cl_path, vcvars_path) 缓存


def _find_vs() -> "tuple[str|None, str|None]":
    """搜索最新 VS 安装，返回 (cl.exe路径, vcvarsall.bat路径)。已缓存。"""
    global _VS_VARS
    if _VS_VARS is not None:
        return _VS_VARS

    # 1) PATH 中已有
    try:
        r = subprocess.run(["where", "cl.exe"], capture_output=True, text=True)
        if r.returncode == 0:
            _VS_VARS = (r.stdout.strip().split("\n")[0], None)
            return _VS_VARS
    except Exception:
        pass

    # 2) 通过 vswhere.exe 定位
    for prog in filter(
        None,
        [
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("ProgramFiles"),
            "C:\\Program Files (x86)",
            "C:\\Program Files",
        ],
    ):
        vswhere = os.path.join(prog, "Microsoft Visual Studio", "Installer", "vswhere.exe")
        if os.path.exists(vswhere):
            try:
                r = subprocess.run(
                    [
                        vswhere,
                        "-latest",
                        "-products",
                        "*",
                        "-requires",
                        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                        "-property",
                        "installationPath",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if r.returncode == 0 and r.stdout.strip():
                    vs_root = r.stdout.strip()
                    vcvars = os.path.join(vs_root, "VC", "Auxiliary", "Build", "vcvarsall.bat")
                    # 搜 cl.exe 以确认
                    msvc = os.path.join(vs_root, "VC", "Tools", "MSVC")
                    for dirpath, _, files in os.walk(msvc):
                        if "cl.exe" in files and "Host" in dirpath:
                            _VS_VARS = (os.path.join(dirpath, "cl.exe"), vcvars)
                            return _VS_VARS
            except Exception:
                pass

    # 3) 遍历常见安装目录，直接搜 cl.exe
    drives = [d for d in ["C:\\", "D:\\", "E:\\"] if os.path.exists(d)]
    for drive in drives:
        for base in [
            "Program Files\\Microsoft Visual Studio",
            "Program Files (x86)\\Microsoft Visual Studio",
        ]:
            root = drive + base
            if not os.path.exists(root):
                continue
            # 只搜两层的 MSVC 目录结构
            for ver_dir in os.listdir(root):
                msvc = os.path.join(root, ver_dir, "BuildTools", "VC", "Tools", "MSVC")
                if not os.path.exists(msvc):
                    msvc = os.path.join(root, ver_dir, "Community", "VC", "Tools", "MSVC")
                if not os.path.exists(msvc):
                    msvc = os.path.join(root, ver_dir, "Professional", "VC", "Tools", "MSVC")
                if not os.path.exists(msvc):
                    msvc = os.path.join(root, ver_dir, "Enterprise", "VC", "Tools", "MSVC")
                if not os.path.exists(msvc):
                    continue
                for dirpath, _, files in os.walk(msvc):
                    if "cl.exe" in files and "Host" in dirpath:
                        # 反推 vcvarsall.bat
                        # VS 2022+: VC\Auxiliary\Build\vcvarsall.bat
                        # older:    VC\vcvarsall.bat
                        for vc_base in [
                            os.path.join(root, ver_dir, "BuildTools", "VC"),
                            os.path.join(root, ver_dir, "Community", "VC"),
                            os.path.join(root, ver_dir, "Professional", "VC"),
                            os.path.join(root, ver_dir, "Enterprise", "VC"),
                        ]:
                            for candidate in [
                                os.path.join(vc_base, "Auxiliary", "Build", "vcvarsall.bat"),
                                os.path.join(vc_base, "vcvarsall.bat"),
                            ]:
                                if os.path.exists(candidate):
                                    _VS_VARS = (os.path.join(dirpath, "cl.exe"), candidate)
                                    return _VS_VARS
                        # 找不到 vcvars，也返回 cl.exe
                        _VS_VARS = (os.path.join(dirpath, "cl.exe"), None)
                        return _VS_VARS

    _VS_VARS = (None, None)
    return _VS_VARS


def _setup_vs_env(vcvars_path: str, arch: str = "amd64"):
    """调用 vcvarsall.bat 并将返回的环境变量写入 os.environ"""
    if not vcvars_path or not os.path.exists(vcvars_path):
        return False
    try:
        # 在 cmd 中 call vcvarsall.bat 后打印全部环境变量
        cmd = f'call "{vcvars_path}" {arch} >NUL && set'
        r = subprocess.run(["cmd", "/c", cmd], capture_output=True, text=True, timeout=30)
        for line in r.stdout.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                if key and not key.startswith("_"):
                    os.environ[key] = value.strip()
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# 1. 环境检测
# ═══════════════════════════════════════════════════════════════
def detect_environment():
    section("1. 环境检测")

    info = {
        "python_version": sys.version.split()[0],
        "python_exe": sys.executable,
        "arch": platform.architecture()[0],
        "platform": platform.platform(),
    }
    for k, v in info.items():
        print(f"  {k}: {v}")

    # 版本兼容性检查
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 8):
        print(f"  ❌ Python {major}.{minor} 版本过低，需要 >= 3.8")
        sys.exit(1)
    if (major, minor) > (3, 11):
        print(f"  ⚠️  Python {major}.{minor} 可能不兼容 PyQt5，建议使用 3.8~3.11")

    # 检查是否在虚拟环境中
    if hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
        print(f"  venv: ✅ 已激活 ({sys.prefix})")
    elif "CONDA_PREFIX" in os.environ:
        print(f"  conda: ✅ 已激活 ({os.environ['CONDA_PREFIX']})")
    else:
        print(f"  ⚠️  未激活虚拟环境，将使用全局 Python ({sys.prefix})")

    # 检查 MSVC 编译器
    cl_path, vcvars_path = _find_vs()

    if cl_path and vcvars_path:
        print(f"  MSVC: ✅ cl.exe 已找到 ({cl_path})")
        print(f"  vcvars: {vcvars_path}")
        # 自动注入 VS 环境变量，确保 setuptools 能调用编译器
        _setup_vs_env(vcvars_path, "amd64" if platform.architecture()[0] == "64bit" else "x86")
        return True

    if cl_path:
        # 找到 cl.exe 但没有 vcvarsall.bat，把 cl.exe 目录加入 PATH
        cl_dir = os.path.dirname(cl_path)
        os.environ["PATH"] = cl_dir + os.pathsep + os.environ.get("PATH", "")
        print(f"  MSVC: ✅ cl.exe 已找到 ({cl_path})")
        return True

    print("  MSVC: ❌ 未找到 cl.exe")
    print("        如果你已安装 Visual Studio Build Tools，请从")
    print('        "开始菜单 → Visual Studio 2026 → Developer Command Prompt"')
    print("        启动终端后重新执行 build.py，或检查安装时是否勾选了：")
    print('        "MSVC v143 C++ 生成工具" (或 "C++ 生成工具")')
    print("        下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    ans = input("\n  是否跳过 Cython 加密，仅做 PyInstaller 打包？[y/N] ")
    if ans.lower() != "y":
        sys.exit(1)
    return False


# ═══════════════════════════════════════════════════════════════
# 2. 扫描代码 + 安装缺失依赖
# ═══════════════════════════════════════════════════════════════
def install_dependencies():
    section("2. 代码依赖扫描与安装")

    # ── 扫描项目代码中 import 的第三方包 ──
    code_deps = scan_project_dependencies()
    print(f"  扫描到 {len(code_deps)} 个第三方 import: {', '.join(sorted(code_deps)) if code_deps else '(无)'}")

    # ── 加上构建工具 ──
    all_needed = code_deps | set(BUILD_TOOLS.keys())
    # 统一转 pip 包名（优先查映射表，否则用小写）
    pip_names = []
    for name in sorted(all_needed):
        pkg = IMPORT_TO_PIP.get(name, name.lower())
        if pkg not in pip_names:
            pip_names.append(pkg)

    # ── 逐个检查是否已安装，并获取版本 ──
    installed = {}
    missing = []
    for pkg_name, import_name in sorted(set((IMPORT_TO_PIP.get(n, n.lower()), n) for n in all_needed)):
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "ok")
            installed[pkg_name] = ver
        except (ImportError, ModuleNotFoundError):
            missing.append(pkg_name)
        except Exception:
            installed[pkg_name] = "?"

    # 去重 missing
    missing = sorted(set(missing))

    # ── 打印状态 ──
    for pkg in pip_names:
        if pkg in installed:
            print(f"  {pkg}: ✅ {installed[pkg]}")
        else:
            print(f"  {pkg}: ❌ 未安装")

    if missing:
        print(f"\n  正在安装: {' '.join(missing)}")
        run([sys.executable, "-m", "pip", "install", "--quiet"] + missing)
        print("  ✅ 依赖安装完成")
    else:
        print("  ✅ 所有依赖已就绪")


# ═══════════════════════════════════════════════════════════════
# 3. Cython 编译 .py → .pyd（加密）
# ═══════════════════════════════════════════════════════════════
def cython_compile():
    section("3. Cython 加密编译 (.py → .pyd)")

    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    # 复制源码树到构建目录
    for p in PY_MODULES + ["main.py"]:
        dst = os.path.join(BUILD_DIR, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, p), dst)

    # 复制资源
    for folder in ["resources", "data"]:
        src = os.path.join(ROOT, folder)
        if os.path.exists(src):
            shutil.copytree(src, os.path.join(BUILD_DIR, folder), dirs_exist_ok=True)

    # 从 Cython 导入
    from Cython.Build import cythonize
    from setuptools import setup, Extension

    # 为每个模块生成 Extension
    ext_modules = []
    for mod_path in PY_MODULES:
        # models/transaction.py → models.transaction
        name = mod_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        ext_modules.append(Extension(name, [os.path.join(BUILD_DIR, mod_path)]))

    # 保存原始 argv/CWD 并伪造（setuptools 需要）
    old_argv = sys.argv
    old_cwd = os.getcwd()
    sys.argv = ["setup.py", "build_ext", "--inplace"]

    # 切换到 build_temp，让 --inplace 的 .pyd/.c 都落在 build_temp 内
    os.chdir(BUILD_DIR)
    try:
        print(f"  正在编译 {len(ext_modules)} 个模块...")
        setup(
            name="billing_app",
            ext_modules=cythonize(
                ext_modules,
                compiler_directives={
                    "language_level": "3",  # Python 3 语义
                    "boundscheck": False,  # 关闭边界检查（更快）
                    "wraparound": False,  # 关闭负索引检查
                },
                nthreads=os.cpu_count(),  # 并行编译 # type: ignore
            ),
            script_args=["build_ext", "--inplace"],
        )
    except Exception as e:
        print(f"  ❌ Cython 编译失败: {e}")
        ans = input("\n  是否跳过加密，仅用 PyInstaller 打包？[y/N] ")
        if ans.lower() != "y":
            sys.exit(1)
        return False
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv

    # 编译产物 .pyd 在 build_temp 下；替换掉同目录的 .py
    replaced = 0
    for mod_path in PY_MODULES:
        pattern = os.path.join(BUILD_DIR, os.path.splitext(mod_path)[0]) + ".*.pyd"
        matches = glob.glob(pattern)
        if matches:
            py_path = os.path.join(BUILD_DIR, mod_path)
            if os.path.exists(py_path):
                os.remove(py_path)  # 删除原始 .py
                replaced += 1
            print(f"  🔒 {mod_path} → {os.path.basename(matches[0])}")
        else:
            # Cython 可能输出到不同位置，搜索 .pyd
            pyd = os.path.join(BUILD_DIR, os.path.splitext(mod_path)[0].replace("/", os.sep) + ".cp*")
            found = glob.glob(pyd.replace(".cp*", ".cp*") + ".pyd")
            if not found:
                found = glob.glob(
                    os.path.join(BUILD_DIR, "**", os.path.basename(mod_path).replace(".py", "*.pyd")), recursive=True
                )
            if found:
                # 移动 .pyd 到正确位置
                target_dir = os.path.dirname(os.path.join(BUILD_DIR, mod_path))
                for f in found:
                    shutil.copy2(f, target_dir)
                os.remove(os.path.join(BUILD_DIR, mod_path))
                replaced += 1
                print(f"  🔒 {mod_path} → {os.path.basename(found[0])}")

    # 清理 C 源码和编译中间文件
    for c_file in glob.glob(os.path.join(BUILD_DIR, "**", "*.c"), recursive=True):
        os.remove(c_file)
    for pattern in ["build", "__pycache__", "*.egg-info"]:
        for p in glob.glob(os.path.join(BUILD_DIR, pattern)):
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)

    print(f"  ✅ 加密完成，{replaced}/{len(PY_MODULES)} 个模块已编译为 .pyd")
    return True


# ═══════════════════════════════════════════════════════════════
# 4. PyInstaller 打包（精简优化）
# ═══════════════════════════════════════════════════════════════
def _find_upx():
    """查找 UPX 压缩工具，返回 --upx-dir 参数或空列表"""
    candidates = [
        os.path.join(ROOT, "upx", "upx.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "upx", "upx.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "upx", "upx.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return ["--upx-dir", os.path.dirname(p)]
    try:
        r = subprocess.run(["where", "upx.exe"], capture_output=True, text=True)
        if r.returncode == 0:
            d = os.path.dirname(r.stdout.strip().split("\n")[0])
            return ["--upx-dir", d]
    except Exception:
        pass
    return []


def pyinstaller_package():
    section("4. PyInstaller 打包")

    icon_path = os.path.join(BUILD_DIR, "resources", "appicon.ico")
    icon_arg = ["--icon", icon_path] if os.path.exists(icon_path) else []
    upx_flags = _find_upx()
    if upx_flags:
        print(f"  UPX: ✅ 已启用压缩")
    else:
        print("  UPX: 未检测到，跳过 (下载 upx.exe 放到项目 upx/ 可减小 ~40% 体积)")

    # 排除本项目肯定不用的 Qt 子模块（QtWebEngine 一个就 ~80MB）
    exclude_qt = [
        # Web 引擎 — 最大头，记账工具完全用不到
        "PyQt5.QtWebEngine",
        "PyQt5.QtWebEngineCore",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebChannel",
        "PyQt5.QtWebKit",
        "PyQt5.QtWebKitWidgets",
        # 3D
        "PyQt5.Qt3DAnimation",
        "PyQt5.Qt3DCore",
        "PyQt5.Qt3DExtras",
        "PyQt5.Qt3DInput",
        "PyQt5.Qt3DLogic",
        "PyQt5.Qt3DRender",
        # 无线
        "PyQt5.QtBluetooth",
        "PyQt5.QtNfc",
        "PyQt5.QtPositioning",
        "PyQt5.QtLocation",
        # QML
        "PyQt5.QtQml",
        "PyQt5.QtQuick",
        "PyQt5.QtQuickWidgets",
        # 传感器、串口
        "PyQt5.QtSensors",
        "PyQt5.QtSerialPort",
        # 数据库（项目用 JSON 文件存储，不用 SQL）
        "PyQt5.QtSql",
        # 其他工具
        "PyQt5.QtTest",
        "PyQt5.QtDesigner",
        "PyQt5.QtHelp",
        "PyQt5.QtXml",
        "PyQt5.QtXmlPatterns",
        "PyQt5.QtMultimedia",
        "PyQt5.QtMultimediaWidgets",
        "PyQt5.QtDBus",
    ]

    # 排除不用的 matplotlib 后端（只保留 qt5agg）
    exclude_mpl = [
        "matplotlib.backends.backend_pdf",
        "matplotlib.backends.backend_svg",
        "matplotlib.backends.backend_ps",
        "matplotlib.backends.backend_webagg",
        "matplotlib.backends.backend_webagg_core",
        "matplotlib.backends.backend_wx",
        "matplotlib.backends.backend_wxagg",
        "matplotlib.backends.backend_gtk3agg",
        "matplotlib.backends.backend_gtk3cairo",
        "matplotlib.backends.backend_gtk4agg",
        "matplotlib.backends.backend_gtk4cairo",
        "matplotlib.backends.backend_tkagg",
        "matplotlib.backends.backend_tkcairo",
        "matplotlib.backends.backend_macosx",
        "matplotlib.backends.backend_cairo",
        "matplotlib.backends.backend_pgf",
        "matplotlib.backends.backend_nbagg",
        "matplotlib.backends.backend_template",
        "matplotlib.backends.backend_mixed",
    ]

    # 构建 exclude 参数
    exclude_args = []
    for m in exclude_qt + exclude_mpl:
        exclude_args += ["--exclude-module", m]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--paths",
        BUILD_DIR,
        "--name",
        "记账工具",
        "--onefile",
        "--windowed",
        "--console",
        "--clean",
        "--noconfirm",
        *icon_arg,
        *upx_flags,
        *exclude_args,
        "--add-data",
        f"resources{os.pathsep}resources",
        "--add-data",
        f"data{os.pathsep}data",
        *[h for m in PY_MODULES for h in ("--hidden-import", m.replace("/", ".").replace("\\", ".").replace(".py", ""))],
        "--hidden-import",
        "matplotlib.backends.backend_qt5agg",
        os.path.join(BUILD_DIR, "main.py"),
    ]

    print("  正在打包...")
    run(cmd)

    # 移动输出
    src = os.path.join(ROOT, "dist", "记账工具.exe")
    if os.path.exists(src):
        shutil.move(src, os.path.join(ROOT, f"{EXE_NAME}"))
        print(f"\n  ✅ 打包完成: {os.path.join(ROOT, EXE_NAME)}")

    # 清理 PyInstaller 生成文件
    for d in ["dist", "build"]:
        p = os.path.join(ROOT, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    for spec in glob.glob(os.path.join(ROOT, "*.spec")):
        os.remove(spec)

    # 清理编译临时目录
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
  ╔══════════════════════════════════════╗
  ║   本地记账工具 - 一键加密打包        ║
  ║   CPython 加密 + PyInstaller 打包     ║
  ╚══════════════════════════════════════╝
    """)

    has_msvc = detect_environment()
    install_dependencies()

    if has_msvc:
        encrypted = cython_compile()
        if not encrypted:
            # 回退：直接用原始 .py 打包
            shutil.rmtree(BUILD_DIR, ignore_errors=True)
            os.makedirs(BUILD_DIR)
            for p in PY_MODULES + ["main.py"]:
                dst = os.path.join(BUILD_DIR, p)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(ROOT, p), dst)
            for folder in ["resources", "data"]:
                src = os.path.join(ROOT, folder)
                if os.path.exists(src):
                    shutil.copytree(src, os.path.join(BUILD_DIR, folder), dirs_exist_ok=True)

    pyinstaller_package()

    section("完成")
    size_mb = os.path.getsize(os.path.join(ROOT, EXE_NAME)) / (1024 * 1024)
    print(f"  输出文件: {os.path.join(ROOT, EXE_NAME)}")
    print(f"  文件大小: {size_mb:.1f} MB")
    print(f"  双击即可运行，无需安装 Python 环境")

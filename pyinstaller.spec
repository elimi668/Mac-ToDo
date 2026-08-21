# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — TodoMate。

构建方式：
    pyinstaller pyinstaller.spec          # 目录模式（推荐，兼容性好）
    pyinstaller --onefile pyinstaller.spec  # 单文件模式

资源说明：
    - app/resources/icons/   → 图标资源
    - app/styles/            → light.qss / dark.qss
    - alembic.ini + alembic/ → 数据库迁移
    - app/main.py            → 入口
"""

from pathlib import Path

# 项目根目录（spec 文件所在处）
ROOT = Path("/root/deepseek/Mac-ToDo")
APP_ROOT = ROOT / "app"

# ── 分析 ──────────────────────────────────────────────────────────────────────
a = Analysis(
    ["app/main.py"],
    pathex=[],
    binaries=[],
    datas=[
        # 图标资源
        ("app/resources/icons", "app/resources/icons"),
        # QSS 样式
        ("app/styles/light.qss", "app/styles"),
        ("app/styles/dark.qss", "app/styles"),
        # Alembic 迁移配置
        ("alembic.ini", "."),
        ("alembic", "alembic"),
    ],
    hiddenimports=[
        "PySide6.QtSql",
        "sqlalchemy.dialects.sqlite",
        "alembic",
        "alembic.script",
        "alembic.runtime",
        "alembic.operations",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "setuptools",
    ],
    noarchive=False,
)

# ── 可执行文件 ────────────────────────────────────────────────────────────────
exe = EXE(
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="TodoMate",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,       # GUI 应用，不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="app/resources/icons/app_icon.ico",
)

# Mac 风格桌面 Todo 助手

一个常驻桌面的个人任务管理工具，采用 macOS 风格设计。支持任务管理、截止提醒、自动备份、主题切换等功能。

## 功能特性

- ✨ **Mac 简约风格**：无边框圆角窗口、阴影效果、交通灯按钮
- 📝 **任务管理**：创建、编辑、删除、完成任务
- 🏷️ **分类筛选**：工作/学习/生活分类，高/中/低优先级
- 📅 **日期管理**：截止日期设置、按日期分桶展示（已过期/今天/明天/未来/无日期）
- 🔍 **搜索过滤**：关键词搜索 + 三列组合筛选（类型/等级/日期）
- 🔔 **截止提醒**：系统托盘通知，动态调度（非固定轮询）
- 💾 **自动备份**：启动时备份，24 小时间隔，保留最近 10 份
- 🌗 **主题切换**：亮色/暗色主题，持久化保存
- 📊 **日报生成**：Markdown 格式，支持复制导出
- 🚀 **开机自启**：跨平台支持（Windows 注册表 / Linux desktop / macOS plist）
- 🔒 **单实例运行**：防止重复启动多进程/多窗口
- ⌨️ **键盘导航**：↑↓ 切换焦点、Enter 完成、Delete 删除、Ctrl+C 复制
- 📦 **批量操作**：多选任务批量完成/取消/删除

## 技术栈

- Python 3.11+
- PySide6 (Qt6) 6.11.1
- SQLAlchemy 2.0.51
- SQLite（WAL 模式）
- Alembic（数据库迁移）

## 安装

### 环境要求

- Python 3.11 或更高版本
- Windows 10+ / macOS 10.15+ / Linux（带 X11/Wayland）

### 安装步骤

```powershell
# 1. 克隆仓库
git clone <repository-url>
cd Mac-ToDo

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

### 开发依赖（可选）

```powershell
pip install -r dev-requirements.txt
```

## 运行

```powershell
python -m app.main
```

或从项目根目录运行：

```powershell
cd Mac-ToDo
python -m app.main
```

首次运行会自动创建 SQLite 数据库和配置文件。

## 打包为 exe

```powershell
# 安装 PyInstaller
pip install pyinstaller

# 使用 spec 文件打包
pyinstaller MacTodo.spec

# 或使用构建脚本（Windows）
scripts\build.bat

# 或使用构建脚本（Linux/macOS）
chmod +x scripts/build.sh
./scripts/build.sh
```

打包完成后，可执行文件位于 `dist/` 目录。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` / `Ctrl+L` | 聚焦输入框 |
| `↑` / `↓` | 切换焦点卡片 |
| `Enter` | 完成/取消完成选中任务 |
| `Delete` | 删除选中任务 |
| `Ctrl+C` | 复制任务标题 |
| `Ctrl+Q` | 退出程序 |
| `Shift+Click` | 扩展多选范围 |

## 配置

应用配置文件位于 `app/data/` 目录：

- `todo.db` — SQLite 数据库
- `theme.json` — 主题偏好（亮色/暗色）
- `backup/` — 自动备份目录

可通过托盘菜单 → 设置 调整备份间隔、提醒提前量等参数。

## 测试

```powershell
# 运行单元测试
python -m unittest discover -s app/tests -v

# 或使用 pytest
python -m pytest app/tests/ -v
```

## 项目结构

```
Mac-ToDo/
├── app/
│   ├── main.py                  # 程序入口
│   ├── config.py                # 全局配置常量
│   ├── ui/                      # 界面层
│   │   ├── main_window.py
│   │   ├── task_card.py
│   │   ├── tray.py
│   │   └── components/          # UI 组件
│   ├── models/                  # 数据模型
│   ├── database/                # 数据库访问
│   ├── services/                # 业务逻辑
│   ├── utils/                   # 工具函数
│   ├── styles/                  # 主题样式表
│   └── tests/                   # 单元测试
├── portable/                    # 便携版（含 Python 运行时）
├── scripts/                     # 构建脚本
├── .github/workflows/           # CI/CD 配置
├── requirements.txt             # 运行依赖
├── dev-requirements.txt         # 开发依赖
└── pyinstaller.spec             # PyInstaller 配置
```

## 已知问题

- 部分 UI 组件测试存在 Mock 兼容性问题（Phase 4 修复中）
- ruff 代码规范检查需安装后执行（Phase 4 进行中）

## License

MIT License

# 项目交接摘要 · Mac Todo 桌面助手

## 项目概述

常驻桌面的个人待办事项管理工具，macOS 简约风格 UI，支持托盘常驻、截止提醒与自动备份。

| 维度 | 说明 |
|------|------|
| **项目名称** | Mac Todo |
| **版本** | 0.1.0 |
| **开发阶段** | MVP / 早期产品阶段（单 initial commit，功能完整可用） |
| **目标用户** | Windows 桌面端单用户 |
| **核心价值** | 轻量、美观、本地优先的个人任务管理 |
| **解决什么问题** | 替代系统原生提醒或第三方在线服务，提供常驻托盘的本地任务管理体验 |

### 核心功能

- 任务创建 / 编辑 / 删除 / 完成
- 分类（工作 / 学习 / 生活）、优先级（高 / 中 / 低）、截止日期
- 按日期分桶展示（已过期 / 今天 / 明天 / 未来 / 无日期）
- 类型、等级、日期三列筛选 + 关键词搜索
- 系统托盘常驻、双击显隐、图标闪烁提醒
- 截止前 15 分钟提醒（60 秒轮询）
- 启动自动备份（24 小时间隔，保留最近 10 份）
- 开机自启（Windows 注册表）
- 亮 / 暗主题切换（持久化到 data/theme.json）
- 日报生成（Markdown，支持复制和导出）

---

## 技术栈

| 技术 | 版本 | 职责 |
|------|------|------|
| Python | 3.14 | 主编程语言 |
| PySide6 | 6.11.1 | GUI 框架（Qt6），UI 渲染、事件处理、系统托盘 |
| SQLAlchemy | 2.0.51 | ORM，封装 SQLite 操作 |
| SQLite | 随环境 | 单机本地数据库 |
| winreg | 标准库 | Windows 注册表读写（开机自启、主题检测） |
| shutil | 标准库 | 数据库文件备份 |

外部依赖极简，[requirements.txt](/D:/Codex/requirements.txt) 只有两个包。无 Web 框架、无消息队列、无缓存、无 AI 框架、无 Docker、无 CI/CD。

所有修改文件必须保持 UTF-8 编码，不允许改变文件编码。

---

## 文件结构

```
app/
├── main.py                    # 入口：异常钩子、延迟导入 UI、托盘初始化、启动备份
├── config.py                  # 全局配置常量（应用名、路径、样式表、颜色、快捷键、窗口约束）
├── __init__.py                # 声明版本号 0.1.0
│
├── ui/                        # 视图层
│   ├── main_window.py         # 主窗口：无边框圆角 + 阴影 + 可拖拽 + 交通灯 + 三节布局
│   ├── task_card.py           # 任务卡片（复选框 + 标题 + 优先级色点 + 右键菜单）
│   ├── tray.py                # 系统托盘（自定义 T 图标、双击显隐、右键菜单）
│   ├── styles.qss             # 亮色 QSS 基础样式（main.py 启动时加载）
│   └── components/
│       ├── task_input_bar.py      # 两行输入栏：标题+添加 / 类型+等级+截止
│       ├── filter_row.py          # 三列下拉筛选：类型/等级/日期
│       ├── date_section.py        # 日期分组头（如 "2026-07-20 今天"）
│       ├── section_header.py      # 通用分区标题（当前未被引用，待清理）
│       ├── confirm_dialog.py      # 二次确认对话框
│       ├── search_bar.py          # 搜索输入框（实时搜索）
│       ├── task_dialog.py         # 任务编辑弹窗
│       └── report_dialog.py       # 日报预览弹窗（Markdown → HTML）
│
├── models/
│   └── task.py                # Task ORM：id, title, category, priority, deadline,
│                              # created_time, completed, reminded, completed_time
│
├── database/
│   ├── database.py            # Engine / SessionLocal / init_db / dispose_db
│   └── repository.py          # TaskRepository：CRUD + 组合筛选 + 提醒查询 + 日期范围 + 迁移
│
├── services/
│   ├── task_service.py        # 业务逻辑：创建/更新/完成/删除 + 按日期分桶 + 组合筛选
│   ├── reminder_service.py    # QTimer 轮询截止提醒（15 分钟提前量，60 秒间隔）
│   └── daily_report_service.py # 日报生成：当天创建/完成任务 → Markdown
│
├── utils/
│   ├── autostart.py           # Windows 注册表开机自启（HKCU\...\Run）
│   ├── backup.py              # 启动自动备份 + 24h 间隔 + 保留最近 10 份
│   ├── exceptions.py          # 自定义异常类（AppError / DatabaseError / TaskNotFoundError）
│   └── theme_manager.py       # 系统亮/暗色检测 + QSS 加载（读 app/styles/）
│
├── styles/
│   ├── light.qss              # 亮色主题样式表
│   └── dark.qss               # 暗色主题样式表
│
├── data/                      # 运行时数据（已 .gitignore）
│   ├── todo.db                # SQLite 数据库
│   ├── backup/                # 自动备份目录
│   └── theme.json             # 主题偏好持久化
│
└── tests/                     # 单元测试（unittest）
    ├── test_task_service.py
    ├── test_repository.py
    ├── test_reminder_service.py
    └── test_daily_report_service.py

resources/
└── styles/
    ├── light.qss              # 与 app/styles/ 内容相同，未被代码引用，待清理
    └── dark.qss
```

---

## 系统架构

### 整体架构

单进程桌面 GUI 应用，采用 MVC 变体：

- **Model**：`models/task.py` + `database/repository.py`
- **View**：`ui/` 下所有组件
- **Controller**：`services/` 层 + `main_window.py` 中的事件处理函数

### 调用关系

```
main.py
  ├── config.py                    # 全局常量
  ├── database/database.py         # init_db()
  ├── utils/backup.py              # backup_on_startup()
  ├── ui/main_window.py            # MainWindow（延迟导入）
  │     ├── ui/components/*        # 输入栏、筛选、搜索、卡片、弹窗
  │     └── services/task_service.py
  ├── ui/tray.py                   # TrayManager（延迟导入）
  │     ├── utils/autostart.py
  │     ├── utils/backup.py
  │     ├── services/daily_report_service.py
  │     └── ui/components/report_dialog.py
  └── services/reminder_service.py # ReminderService（延迟导入）

database/repository.py
  ├── models/task.py               # ORM 实体
  └── database/database.py         # Session / Engine
```

### 请求流程

```
用户操作（点击/输入）
  → MainWindow 信号槽处理
  → TaskService.create_task() / update_task() / set_completed() / delete_task()
  → TaskRepository.create() / update() / set_completed() / delete()
  → SQLAlchemy Session → SQLite
  → MainWindow._refresh_tasks() 重新查询并渲染
```

### 生命周期

1. `main.py` 注册全局异常钩子 `_global_excepthook`
2. `init_db()` 创建 Engine、SessionLocal、建表、幂等迁移
3. `backup_on_startup()` 检查是否需要备份
4. `QApplication` 创建，加载 [ui/styles.qss](/D:/Codex/app/ui/styles.qss)
5. 延迟导入 `MainWindow`、`TrayManager`、`ReminderService`
6. 创建窗口 → 显示 → 创建托盘 → 创建提醒定时器
7. 进入 `app.exec()` 事件循环
8. 关闭窗口时仅隐藏（`closeEvent` ignore），程序通过托盘退出

---

## 核心约定

### 架构原则

1. **分层清晰**：ui/ 视图层、models/ 模型层、database/ 数据访问层、services/ 业务逻辑层。禁止跨层调用。
2. **仓储模式**：所有数据库操作必须通过 `TaskRepository`，禁止在 service 或 ui 中直接使用 SQLAlchemy session。
3. **延迟导入**：`main.py` 中 UI 模块必须延迟导入，避免启动慢。
4. **薄 Service 层**：Service 封装 Repository 并提供业务规则（日期分桶、组合筛选），UI 只调用 Service 不直接访问 Repository。
5. **依赖注入**：`TaskRepository` 和 `TaskService` 均支持传入依赖实例，方便测试。

### UI 规范

1. **Mac 简约风格**：禁止使用传统 Windows 控件风格；所有新增功能必须保持 Mac 设计语言。
2. **优先级**：稳定性 > 用户体验 > 简洁 UI > 功能扩展。
3. **禁止随意增删按钮**：不破坏已有 UI 布局，新增交互组件需复用 `components/` 下的已有组件。
4. **主题切换**：已实现（主窗口左上角按钮，持久化到 `data/theme.json`），使用 `theme_manager.py` 的 `load_theme_qss()`。
5. **动态绘制图标**：托盘图标用 QPainter 绘制，不依赖外部图片资源。
6. **无分页列表**：当前任务量较小，全量加载渲染；若任务超过数百条需改为增量更新或虚拟列表。

### 数据持久化

1. **SQLite 单机**：数据库路径 `app/data/todo.db`，由 `config.py` 统一管理，禁止硬编码路径。
2. **自动备份**：`backup_on_startup()` 在每次启动时执行，距上次备份超 24 小时则备份；托盘菜单支持"立即备份"。
3. **.gitignore 排除 app/data/*.db**：新开发者需运行 `python -m app.main` 后自动生成数据库文件。
4. **备份安全**：当前使用 `shutil.copy2` 直接复制，可能在写入中途复制不完整数据。后续应改用事务快照或先关闭写入再复制。

### 代码规范

1. **Python 3.14 类型注解**：所有函数签名必须包含 `->` 返回类型标注，参数使用 `from __future__ import annotations`。
2. **异常处理**：`main.py` 已注册全局异常钩子 `_global_excepthook`，新增模块无需重复捕获。
3. **日志输出**：调试信息打印到 `sys.stderr`，生产环境不输出敏感数据。
4. **禁止跨层调用**：UI 不碰数据库，Service 不直接操作 Qt 控件。
5. **统一使用 Path 对象**：路径常量在 `config.py` 中定义为 `Path`，禁止字符串拼接路径。

### 测试要求

1. **当前覆盖范围**：`services/` 和 `database/` 层有单元测试（unittest）。
2. **新增测试**：为 `ui/` 和 `utils/` 编写测试时，遵循已有测试文件的 mock 模式。
3. **禁止修改 todo.db 种子文件**：测试使用独立临时数据库（`init_db` 接受 `db_url` 参数）。
4. **测试隔离**：每个 TestCase 在 setUp 中创建临时目录和数据库，tearDown 中 dispose_db 并清理。

---

## 数据模型

### tasks 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| title | VARCHAR(200) | NOT NULL | 任务标题 |
| category | VARCHAR(32) | NOT NULL, DEFAULT '生活' | 分类：工作 / 学习 / 生活 |
| priority | INTEGER | NOT NULL, DEFAULT 2 | 优先级：1=高 2=中 3=低 |
| deadline | DATETIME | NULLABLE | 截止时间 |
| created_time | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| completed | BOOLEAN | NOT NULL, DEFAULT 0 | 是否完成 |
| reminded | BOOLEAN | NOT NULL, DEFAULT 0 | 是否已发送截止提醒 |
| completed_time | DATETIME | NULLABLE | 完成时间 |

### 索引

- `idx_deadline` on `deadline`
- `idx_completed` on `completed`
- `idx_category` on `category`

### 排序规则

默认列表排序：`completed ASC, deadline ASC NULLS LAST, created_time DESC`（未完成在前，同状态内按截止日期升序、创建时间降序）。

### 日期分桶

`TaskService.group_by_date()` 将任务分为五组：已过期、今天、明天、未来、无日期。

---

## 配置系统

| 维度 | 现状 |
|------|------|
| 环境变量 | 无 |
| Config 类 | 无，使用 [config.py](/D:/Codex/app/config.py) 模块级常量 |
| Secrets | 无（无需） |
| 多环境支持 | 无（仅本地单机） |
| Feature Flag | 无 |
| 持久化配置 | `app/data/theme.json` 存储主题偏好 |
| 数据库路径 | 由 `config.APP_ROOT / "data" / "todo.db"` 计算 |

---

## 依赖关系

### 外部依赖

| 包 | 版本 | 用途 |
|----|------|------|
| PySide6 | 6.11.1 | GUI 框架 |
| SQLAlchemy | 2.0.51 | ORM |

### 内部依赖

```
main.py → config.py, database.py, backup.py, ui/*, services/*
ui/main_window.py → services/task_service.py, ui/components/*
ui/tray.py → utils/autostart.py, utils/backup.py, services/daily_report_service.py, ui/components/report_dialog.py
services/* → database/repository.py
database/repository.py → models/task.py, database/database.py
```

- **无循环依赖**。所有 import 方向单向：ui → services → database → models。
- **主要耦合点**：`main_window.py` 直接处理 date_filter 条件分支，筛选逻辑应在 Service 层。

---

## 已知问题与 Bug

### P0 — 已修复

### P0 — 已修复

1. ~~**[task_service.py](/D:/Codex/app/services/task_service.py:67) `update_task` deadline 语义陷阱**~~ ✅ 已修复

   ~~`deadline=None` 默认值被转换为 `NO_CHANGE`，导致用户在编辑任务时选择"无日期"不会清除原有截止日期。~~

   **修复方案**：`TaskService.update_task()` 默认值改为 `NO_CHANGE`，`TaskDialog` 使用 `_deadline_was_touched` 标志位区分"未修改"和"清除"，`main_window.py` 直接透传。现在支持三种状态：不修改 deadline、清除 deadline、设置新 deadline。

2. ~~**[backup.py](/D:/Codex/app/utils/backup.py) 备份可能复制不完整数据**~~ ✅ 已修复

   ~~`shutil.copy2` 直接复制正在使用的 SQLite 文件，写入中途可能导致备份损坏。应改用 WAL 模式或先获取共享锁再复制。~~

   **修复方案**：`backup_db()` 改用 `sqlite3.backup()` 在线备份 API 替代 `shutil.copy2`，在 WAL 模式下获取一致性快照。`database.py` 启用 `PRAGMA journal_mode=WAL` 保障并发读与备份一致性。新增 `test_backup.py` 覆盖备份创建、有效性校验、清理策略、启动时跳过等场景。

3. **[task_card.py](/D:/Codex/app/ui/task_card.py:34) 构造函数缺少类型注解**

   ```python
   def __init__(self, task, parent=None):
   ```
   违反项目代码规范，需补充 `Task` 和 `QWidget | None` 类型标注。

### P1 — 建议修复

4. **筛选逻辑耦合在 UI 层**：`main_window._refresh_tasks()` 中包含 date_filter 条件分支，应下沉到 `TaskService`。
5. **提醒策略低效**：固定 60 秒轮询，最坏情况到期前需等待 60 秒。应按最近未提醒任务的 deadline 动态计算间隔。
6. **`_refresh_tasks()` 全量重建**：每次筛选变化都 deleteLater 所有子控件再重建，大数据量时闪烁明显。应维护 TaskCard 实例字典做增量更新。
7. **死代码清理**：
   - `app/ui/components/section_header.py` 定义了 `SectionHeader` 但从未引用
   - `resources/styles/` 是 `app/styles/` 的重复副本，未被代码加载
   - `app/utils/exceptions.py` 定义了异常类但全项目无 import
8. ~~**SQLite 未启用 WAL 模式**：[database.py](/D:/Codex/app/database/database.py) 创建 Engine 时未设置 WAL 配置，影响并发和备份安全性。~~ ✅ 已修复
9. **`search_bar.py` 使用 emoji "🔍"**：不同系统渲染不一致，应使用图标或纯文本。

### P2 — 长期优化

10. **数据库迁移**：`migrate()` 使用原始 ALTER TABLE SQL，应改为 Alembic 或 SQLAlchemy Migrate。
11. **分类和优先级硬编码**：[config.py](/D:/Codex/app/config.py) 中的 CATEGORIES / PRIORITY_FILTERS 应可配置。
12. **主题持久化逻辑在 MainWindow 中**：`_load_theme` / `_save_theme` 应抽取到独立服务。
13. **`theme_manager.load_theme_qss()` 参数类型不明**：`app` 实际接收 QWidget 而非 QApplication。
14. **UI 层和 utils 层零测试**：需补充集成测试。（backup.py 已有测试覆盖，UI 层和 autostart.py 仍需补充。）
15. **无 CI/CD 和打包发布**：缺少 PyInstaller/Nuitka 配置和自动化流水线。

---

## 改进路线图

### P0 必须修改

| 问题 | 原因 |
|------|------|
| 备份时使用事务快照或 WAL | 防止复制不完整数据库文件 |
| 给 `task_card.py` 加类型注解 | 符合代码规范 |

### P1 建议修改

| 问题 | 原因 |
|------|------|
| 筛选逻辑下沉到 TaskService | 消除 UI 与业务边界模糊 |
| 提醒服务动态调度 | 减少轮询间隔，提高及时性 |
| `_refresh_tasks()` 改为增量更新 | 避免全量重建闪烁 |
| 清理死代码 | 减少维护负担 |
| 补充 autostart.py 测试 | 关键基础设施缺乏覆盖 |

### P2 长期优化

| 问题 | 原因 |
|------|------|
| PyInstaller 打包为 exe | 方便分发 |
| 分类/优先级改为配置表 | 支持用户自定义 |
| 键盘导航 | 提升无鼠标体验 |
| Alembic 迁移 | 可追溯的数据库版本管理 |
| CI/CD 流水线 | 自动测试和风格检查 |
| 图标库替代 emoji | 跨平台一致性 |

---

## 项目成熟度

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构成熟度 | 6/10 | 分层清晰，仓储模式正确，但 UI 承担部分业务逻辑 |
| 工程化程度 | 4/10 | 有 requirements.txt 和 .gitignore，无 CI/CD、无打包、无 lint |
| 可维护性 | 7/10 | 结构清晰、命名规范、类型注解基本到位，有死代码需清理 |
| 可扩展性 | 6/10 | 依赖注入良好，但分类/优先级硬编码、单表限制扩展 |
| 代码规范 | 7/10 | 大部分函数有类型注解，存在个别遗漏 |
| 测试覆盖 | 5/10 | service/repository 有覆盖，UI 和 utils 缺失 |

**综合成熟度：5.7/10** — 功能完整的 MVP，工程化和测试方面仍有差距。

---

## 快速上手

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

运行测试：

```powershell
python -m unittest discover -s app\tests
```

---

## 推荐阅读顺序（新成员第一天）

1. [README.md](/D:/Codex/README.md) — 项目定位和运行方式
2. 本文档 — 架构、规范、已知问题
3. [app/main.py](/D:/Codex/app/main.py) — 启动流程和模块初始化
4. [app/config.py](/D:/Codex/app/config.py) — 全局常量
5. [app/models/task.py](/D:/Codex/app/models/task.py) — 核心数据实体
6. [app/database/repository.py](/D:/Codex/app/database/repository.py) — 数据访问 API
7. [app/services/task_service.py](/D:/Codex/app/services/task_service.py) — 业务逻辑
8. [app/ui/main_window.py](/D:/Codex/app/ui/main_window.py) — 主界面和事件处理
9. [app/tests/test_repository.py](/D:/Codex/app/tests/test_repository.py) — 通过测试反推 Repository 完整 API

---

## 禁止事项

- 禁止直接修改 database/ 中的 SQL 语句，必须通过 SQLAlchemy ORM
- 禁止在主窗口中添加非必要按钮或复杂交互
- 禁止修改数据库表结构除非用户明确要求
- 禁止引入新的第三方 GUI 库（保持 PySide6 单一依赖）
- 禁止在 service 或 ui 中直接使用 SQLAlchemy Session
- 禁止忽略类型注解要求（所有函数签名必须标注返回类型）
- 禁止修改 app/data/todo.db 的种子数据

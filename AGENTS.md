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
- 截止前 15 分钟提醒（动态调度，非固定 60 秒轮询）
- 启动自动备份（24 小时间隔，保留最近 10 份）
- 开机自启（Windows 注册表）
- 亮 / 暗主题切换（持久化到 data/theme.json，由 ThemeService 管理）
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

外部依赖极简，requirements.txt 只有两个包。无 Web 框架、无消息队列、无缓存、无 AI 框架、无 Docker、无 CI/CD。

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
│   ├── task_card.py           # 任务卡片（复选框 + 标题 + 优先级色点 + 右键菜单，含增量更新支持）
│   ├── tray.py                # 系统托盘（自定义 T 图标、双击显隐、右键菜单）
│   ├── styles.qss             # 亮色 QSS 基础样式（main.py 启动时加载）
│   └── components/
│       ├── task_input_bar.py      # 两行输入栏：标题+添加 / 类型+等级+截止
│       ├── filter_row.py          # 三列下拉筛选：类型/等级/日期
│       ├── date_section.py        # 日期分组头（如 "2026-07-20 今天"）
│       ├── confirm_dialog.py      # 二次确认对话框
│       ├── search_bar.py          # 搜索输入框（实时搜索，纯文本替代 emoji）
│       ├── task_dialog.py         # 任务编辑弹窗
│       └── report_dialog.py       # 日报预览弹窗（Markdown → HTML）
│
├── models/
│   └── task.py                # Task ORM：id, title, category, priority, deadline,
│                              # created_time, completed, reminded, completed_time
│
├── database/
│   ├── database.py            # Engine / SessionLocal / init_db / dispose_db（WAL 模式）
│   └── repository.py          # TaskRepository：CRUD + 组合筛选 + 提醒查询 + 日期范围 + 迁移
│
├── services/
│   ├── task_service.py        # 业务逻辑：创建/更新/完成/删除 + 按日期分桶 + 组合筛选（含 date_filter）
│   ├── reminder_service.py    # 动态调度截止提醒（按最近 deadline 计算间隔）
│   ├── daily_report_service.py # 日报生成：当天创建/完成任务 → Markdown
│   └── theme_service.py       # 主题服务：检测/持久化/切换亮暗主题
│
├── utils/
│   ├── autostart.py           # Windows 注册表开机自启（HKCU\...\Run）
│   └── backup.py              # 启动自动备份 + 24h 间隔 + 保留最近 10 份（sqlite3.backup）
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
    ├── test_backup.py
    ├── test_daily_report_service.py
    ├── test_autostart.py        # 新增：autostart 模块测试
    ├── test_reminder_service.py
    └── test_task_dialog.py
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
4. `QApplication` 创建，加载 `app/ui/styles.qss`
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
4. **主题切换**：已实现（主窗口左上角按钮，持久化到 `data/theme.json`），由 `ThemeService` 统一管理检测与持久化逻辑。
5. **应用图标**：托盘图标和窗口图标使用 `app/resources/icons/app_icon.png`，不再动态绘制。
6. **无分页列表**：当前任务量较小，全量加载渲染；若任务超过数百条需改为增量更新或虚拟列表。

### 数据持久化

1. **SQLite 单机**：数据库路径 `app/data/todo.db`，由 `config.py` 统一管理，禁止硬编码路径。
2. **自动备份**：`backup_on_startup()` 在每次启动时执行，距上次备份超 24 小时则备份；托盘菜单支持"立即备份"。
3. **.gitignore 排除 app/data/*.db**：新开发者需运行 `python -m app.main` 后自动生成数据库文件。
4. **备份安全**：已改用 `sqlite3.backup()` 在线备份 API（见 `app/utils/backup.py`），WAL 模式下获取一致性快照，不再使用 `shutil.copy2`。

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
| Config 类 | 无，使用 `config.py` 模块级常量 |
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
- `TaskService.get_grouped_filtered(date_filter=...)` 已承载全部筛选逻辑，UI 层不再持有业务分支。

---
## 已知问题与 Bug

### P0 — 已全部修复 ✅

1. ~~**`update_task` deadline 语义陷阱**~~ ✅ 已修复
   ~~`deadline=None` 默认值被转换为 `NO_CHANGE`，导致用户在编辑任务时选择"无日期"不会清除原有截止日期。~~
   **修复方案**：`TaskService.update_task()` 默认值改为 `NO_CHANGE`，`TaskDialog` 使用 `_deadline_was_touched` 标志位区分"未修改"和"清除"，`main_window.py` 直接透传。

2. ~~**备份可能复制不完整数据（shutil.copy2）**~~ ✅ 已修复
   **修复方案**：`backup_db()` 改用 `sqlite3.backup()` 在线备份 API 替代 `shutil.copy2`，在 WAL 模式下获取一致性快照。新增 `test_backup.py` 覆盖备份创建、有效性校验、清理策略、启动时跳过等场景。

3. ~~**`task_card.py` 构造函数缺少类型注解**~~ ✅ 已修复
   ~~`def __init__(self, task, parent=None)`~~ → `def __init__(self, task: Task, parent: QWidget | None = None) -> None`

### P1 — 已全部修复 ✅

4. ~~**筛选逻辑耦合在 UI 层**~~ ✅ 已修复 — 下沉至 `TaskService.get_grouped_filtered(date_filter=...)`
5. ~~**提醒策略低效（固定 60s 轮询）**~~ ✅ 已修复 — 改为动态调度，按最近未提醒 deadline 计算间隔
6. ~~**`_refresh_tasks()` 全量重建**~~ ✅ 已修复 — 维护 `TaskCard` 实例字典做增量更新
7. ~~**死代码**~~ ✅ 已修复 — 删除 `section_header.py`、`exceptions.py`、`resources/styles/`
8. ~~**SQLite 未启用 WAL 模式**~~ ✅ 已修复
9. ~~**`search_bar.py` 使用 emoji**~~ ✅ 已修复 — 替换为纯文本 `"搜索"`
10. ~~**右键菜单无响应**~~ ✅ 已修复 — `main_window.py` 中创建 TaskCard 后连接 toggled/edit_requested/delete_requested 信号
11. ~~**对话框样式不统一**~~ ✅ 已修复 — TaskDialog 和 ConfirmDialog 添加 FramelessWindowHint，统一圆角无边框风格
12. ~~**托盘图标固定绘制**~~ ✅ 已修复 — 支持自定义图标（app/resources/icons/app_icon.png）

### P2 — 长期优化

13. **数据库迁移**：`migrate()` 使用原始 ALTER TABLE SQL，应改为 Alembic 或 SQLAlchemy Migrate。
14. **分类和优先级硬编码**：`config.py` 中的 CATEGORIES / PRIORITY_FILTERS 应可配置。
15. ~~**主题持久化逻辑耦合在 MainWindow**~~ ✅ 已修复 — 已抽取到独立 `ThemeService`
16. **UI 层测试覆盖**：TaskCard、FilterRow 等核心组件尚无单测，建议补充。
17. **无 CI/CD 和打包发布**：PyInstaller spec 已就绪，尚无自动化流水线。
18. **日期选择器高度微调**：QDateTimeEdit 高度与 QComboBox 存在细微差异，需进一步调优。

---

## 改进路线图

### P0 必须修改 ✅ 全部完成

- [x] 备份使用 `sqlite3.backup()` 在线备份，替代 `shutil.copy2`
- [x] `task_card.py` 构造函数添加类型注解
- [x] `search_bar.py` emoji 替换为纯文本 `"搜索"`

### P1 建议修改 ✅ 全部完成

- [x] 日期筛选逻辑下沉至 `TaskService.get_grouped_filtered(date_filter=...)`
- [x] 提醒服务改为动态调度（按最近未提醒 deadline 计算间隔）
- [x] `_refresh_tasks()` 改为增量更新（维护 TaskCard 实例字典）
- [x] 清理死代码（`section_header.py`、`exceptions.py`、`resources/styles/`）
- [x] 补充 `test_autostart.py`（6 个测试用例覆盖 enable/disable/toggle/注册表路径）
- [x] 主题逻辑抽取为独立 `ThemeService`
- [x] 修复右键菜单信号连接（toggled/edit_requested/delete_requested）
- [x] 统一对话框样式（TaskDialog/ConfirmDialog 无边框圆角）
- [x] 支持自定义托盘图标

### P2 长期优化

| 问题 | 原因 |
|------|------|
| PyInstaller 打包为 exe | Linux 版已生成，Windows exe 需在 Windows 环境构建 |
| 分类/优先级改为配置表 | 支持用户自定义 |
| 键盘导航 | 提升无鼠标体验 |
| Alembic 迁移 | 可追溯的数据库版本管理 |
| CI/CD 流水线 | 自动测试和风格检查 |
| UI 层单元测试 | TaskCard、FilterRow 等核心组件补充测试 |
| 日期选择器高度微调 | QDateTimeEdit 与 QComboBox 高度需进一步对齐 |

---

## 项目成熟度

| 维度 | 评分 | 依据 |
|------|------|------|
| 架构成熟度 | 8/10 | 分层清晰，仓储模式正确，P0/P1 架构问题已全部修复 |
| 工程化程度 | 6/10 | 有 requirements.txt 和 .gitignore，PyInstaller spec 已就绪，无 CI/CD |
| 可维护性 | 8/10 | 结构清晰、命名规范、类型注解完整，死代码已清理 |
| 可扩展性 | 6/10 | 依赖注入良好，但分类/优先级硬编码、单表限制扩展 |
| 代码规范 | 8/10 | 所有函数签名均有类型注解，无违规项 |
| 测试覆盖 | 6/10 | services/database/utils 层有覆盖，UI 组件层仍缺失 |

**综合成熟度：7.5/10** — 从 7.0 提升至 7.5，P0/P1 全部修复完毕，右键菜单、对话框样式、图标支持已完善，单元测试和工程化仍有提升空间。

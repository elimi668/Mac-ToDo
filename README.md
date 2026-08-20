# Mac 风格桌面 Todo 助手

一个常驻桌面的个人任务管理工具，采用 macOS 风格设计。

## 功能特性

- ✨ **Mac 简约风格**：无边框圆角窗口、阴影效果、交通灯按钮
- 📝 **任务管理**：创建、编辑、删除、完成任务
- 🏷️ **分类筛选**：工作/学习/生活分类，高/中/低优先级
- 📅 **日期管理**：截止日期设置、按日期分桶展示
- 🔍 **搜索过滤**：关键词搜索 + 三列组合筛选
- 🔔 **截止提醒**：系统托盘通知，动态调度
- 💾 **自动备份**：启动时备份，24 小时间隔
- 🌗 **主题切换**：亮色/暗色主题，持久化保存
- 📊 **日报生成**：Markdown 格式，支持复制导出
- 🚀 **开机自启**：Windows 注册表实现

## 技术栈

- Python 3.14
- PySide6 (Qt6)
- SQLAlchemy
- SQLite

## 安装

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 运行

```powershell
python -m app.main
```

## 打包为 exe

```powershell
pip install pyinstaller
pyinstaller MacTodo.spec
```

## 项目结构

```
app/
├── main.py                 程序入口
├── config.py               全局配置常量
├── ui/                     界面层
│   ├── main_window.py
│   ├── task_card.py
│   ├── tray.py
│   ├── styles.qss          亮色主题样式
│   └── components/
│       ├── task_input_bar.py
│       ├── filter_row.py
│       ├── date_section.py
│       ├── confirm_dialog.py
│       ├── search_bar.py
│       ├── task_dialog.py
│       └── report_dialog.py
├── models/                 数据模型
├── database/               数据库
├── services/               业务逻辑
├── utils/                  工具函数
├── styles/                 主题样式表
│   ├── light.qss
│   └── dark.qss
├── resources/
│   └── icons/              图标资源
└── tests/                  单元测试
```

## 快捷键

- `Ctrl+N` - 聚焦输入框
- `Ctrl+L` - 聚焦输入框（备选）
- `Ctrl+Q` - 退出程序

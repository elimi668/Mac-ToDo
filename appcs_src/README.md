# Mac 风格桌面 Todo 助手

一个常驻桌面的个人任务管理工具，采用 macOS 风格设计。

## 技术栈

- Python 3.14
- PySide6
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

## 项目结构

```
app/
├── main.py                 程序入口
├── config.py               全局配置常量
├── ui/                     界面层
│   ├── main_window.py
│   ├── task_card.py
│   ├── components/
│   └── styles.qss
├── models/                 数据模型
├── database/               数据库
├── services/               业务逻辑
├── resources/icons/        图标资源
└── tests/                  单元测试
```

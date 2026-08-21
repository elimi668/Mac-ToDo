@echo off
REM TodoMate Windows 构建脚本
REM 用法: scripts\build.bat
REM 要求：Python 3.11+、PyInstaller 已安装

setlocal enabledelayedexpansion

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保 Python 3.11+ 已安装并在 PATH 中。
    exit /b 1
)

REM 安装依赖（如尚未安装）
echo [信息] 检查依赖...
pip install -q PyInstaller

REM 清理旧构建产物
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TodoMate.spec rmdir /s /q TodoMate.spec

REM 执行 PyInstaller 打包（目录模式，兼容性好）
echo [信息] 开始打包 TodoMate ...
pyinstaller pyinstaller.spec

if errorlevel 1 (
    echo [错误] 打包失败。
    exit /b 1
)

echo.
echo ========================================
echo  打包成功！输出目录: dist\TodoMate\
echo ========================================
echo.
echo 运行方式:
echo   dist\TodoMate\TodoMate.exe
echo.
pause

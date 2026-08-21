#!/usr/bin/env bash
# TodoMate Linux/macOS 构建脚本
# 用法: scripts/build.sh
# 要求：Python 3.11+、PyInstaller 已安装

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未找到 python3，请确保 Python 3.11+ 已安装。" >&2
    exit 1
fi

python3 --version

# 安装依赖
echo "[信息] 检查依赖..."
pip3 install -q PyInstaller

# 清理旧构建产物
rm -rf build dist TodoMate.spec

# 执行 PyInstaller 打包
echo "[信息] 开始打包 TodoMate ..."
pyinstaller pyinstaller.spec

echo ""
echo "========================================"
echo "  打包成功！输出目录: dist/TodoMate/"
echo "========================================"
echo ""
echo "运行方式:"
echo "  dist/TodoMate/TodoMate"
echo ""

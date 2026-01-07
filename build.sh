#!/bin/bash
# SimpleNES-py 构建脚本
# 支持在 Windows (通过 WSL 或 Git Bash)、macOS 和 Linux 上构建可执行文件

set -e  # 遇到错误时退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "SimpleNES-py 跨平台构建工具"
echo "=============================="

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3。请先安装 Python 3。" >&2
    exit 1
fi

# 检查是否需要安装依赖
if [ ! -f "requirements.txt" ] || [ ! "$(pip list | grep pyinstaller)" ]; then
    echo "安装构建依赖..."
    pip3 install -r requirements.txt
    pip3 install pyinstaller
fi

# 执行构建
echo "开始构建可执行文件..."
python3 build.py

echo "构建完成！"
echo "可执行文件位于 dist/ 目录中"
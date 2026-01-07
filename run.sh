#!/bin/bash
# SimpleNES-py 启动脚本

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "激活虚拟环境..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "错误: 找不到虚拟环境 'venv'。请先运行: python3 -m venv venv"
        exit 1
    fi
fi

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <rom_file> [options]"
    echo "示例: $0 SuperMarioBros.nes -s 3"
    echo ""
    echo "选项:"
    echo "  -s, --scale SCALE    设置显示比例 (默认: 3)"
    echo "  -w, --width WIDTH    设置窗口宽度"
    echo "  -H, --height HEIGHT  设置窗口高度"
    echo "  -h, --help          显示帮助"
    exit 1
fi

# 运行模拟器
python main.py "$@"
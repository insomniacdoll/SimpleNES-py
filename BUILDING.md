# SimpleNES-py 打包指南

## 概述
本项目提供了一套跨平台的构建脚本，可以将 SimpleNES-py 打包成 Windows、macOS 和 Linux 上的独立可执行文件。

## 构建脚本说明

### build.py
- 主构建脚本，使用 PyInstaller 将项目打包成可执行文件
- 适用于所有平台
- 生成单一可执行文件，包含所有依赖

### build_executable.py
- 备用构建脚本，提供简化的构建流程
- 同样使用 PyInstaller 进行打包

### build.sh
- 适用于 Unix 系统 (macOS/Linux) 的便捷构建脚本
- 自动安装依赖并运行构建

## 构建步骤

### 通用构建方法 (推荐)
1. 确保已安装 Python 3.7+
2. 激活项目虚拟环境（如果存在）:
   ```bash
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```
3. 运行构建: `python build.py`

### 平台特定方法

#### Windows
```cmd
# 激活虚拟环境
venv\Scripts\activate

# 运行构建
python build.py
```

#### macOS/Linux
```bash
# 激活虚拟环境
source venv/bin/activate

# 使用便捷脚本
chmod +x build.sh
./build.sh

# 或直接运行构建脚本
python build.py
```

## 输出文件
构建完成后，可执行文件将位于 `dist/` 目录中：
- Windows: `dist/SimpleNES.exe`
- macOS: `dist/SimpleNES`
- Linux: `dist/SimpleNES`

## 使用方法
构建完成的可执行文件可以：
1. 直接双击运行
2. 拖拽 ROM 文件到可执行文件上运行
3. 在命令行中使用: `./SimpleNES <rom_file.nes> [options]`

支持的命令行选项：
- `-s, --scale`: 设置显示缩放比例 (默认: 3.0)
- `-w, --width`: 设置显示宽度
- `-H, --height`: 设置显示高度

## 跨平台构建说明

### Windows
- 需要 Windows 系统来构建 Windows 版本 (.exe)
- 可以安装 Python 和 Git Bash 来运行 shell 脚本

### macOS
- 需要 macOS 系统来构建 macOS 版本
- 推荐使用 Homebrew 安装 Python

### Linux
- 需要 Linux 系统来构建 Linux 版本
- 可能需要安装额外的系统依赖，如 SDL 库

## 注意事项
1. 构建过程可能需要几分钟时间，具体取决于系统性能
2. 生成的可执行文件包含了 Python 解释器和所有依赖，因此文件较大
3. 首次运行时可能被安全软件误报，请添加信任
4. 为获得最佳性能和兼容性，建议在与目标平台相同的系统上进行构建
5. 构建后的可执行文件是独立的，无需安装 Python 或其他依赖

## 高级配置
如果需要自定义构建选项（如图标、版本信息等），可以：
1. 修改 `build.py` 中的 spec 文件内容
2. 在项目根目录创建 `SimpleNES.spec` 文件进行高级配置
3. 使用 PyInstaller 的命令行参数进行自定义

## 故障排除
- 如果遇到依赖问题，请确保使用项目提供的虚拟环境
- 构建失败时，请检查 `build/` 目录中的 PyInstaller 日志
- 对于 macOS 上的代码签名问题，可能需要临时禁用以测试可执行文件
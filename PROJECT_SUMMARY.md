# SimpleNES-py 项目总结

## 项目概述

SimpleNES-py 是一个用 Python 实现的 NES（任天堂娱乐系统）模拟器，基于原始的 SimpleNES C++ 项目。该项目旨在提供一个功能完整的 NES 模拟器，能够运行经典的 NES 游戏。

## 架构设计

### 核心组件

1. **CPU 模块 (src/cpu/cpu.py)**
   - 实现了 Ricoh 2A03 CPU（基于 6502 处理器）
   - 支持完整的 6502 指令集
   - 包含寄存器、标志位和中断处理

2. **PPU 模块 (src/ppu/ppu.py)**
   - 实现了 NES 的 PPU（图像处理单元，RP2C02）
   - 处理图形渲染、扫描线和帧同步
   - 支持精灵和背景渲染

3. **内存总线系统 (src/bus/mainbus.py)**
   - 实现了 CPU 内存映射
   - 处理内存读写和 I/O 操作
   - 管理内存镜像和外部设备通信

4. **卡带和映射器系统 (src/cartridge/)**
   - 支持 iNES 格式 ROM 加载
   - 实现多种常见映射器（NROM, UxROM, CNROM, MMC3, AxROM, ColorDreams, GxROM, SxROM）
   - 处理 PRG/CHR ROM 映射和银行切换

5. **控制器系统 (src/controller/controller.py)**
   - 实现 NES 控制器输入
   - 支持键盘映射和手柄输入
   - 处理控制器状态和序列读取

6. **音频系统 (src/emulator/apu.py)**
   - 实现 NES APU（音频处理单元）
   - 包含两个脉冲通道、三角波通道、噪声通道和 DMC 通道
   - 支持音效和音乐回放

7. **渲染系统 (src/ppu/renderer.py)**
   - 使用 Pygame 进行图形渲染
   - 处理 PPU 输出到屏幕的转换
   - 支持可调节的显示比例

### 依赖库

- **Pygame**: 用于图形渲染、音频和输入处理
- **NumPy**: 用于数值计算和缓冲区处理
- **Pillow**: 用于图像处理（可选）

## 文件结构

```
SimpleNES-py/
├── main.py                 # 主程序入口
├── requirements.txt        # Python 依赖
├── README.md              # 项目说明
├── test_components.py     # 组件测试
├── src/
│   ├── __init__.py
│   ├── cpu/
│   │   ├── __init__.py
│   │   └── cpu.py         # CPU 模拟器
│   ├── ppu/
│   │   ├── __init__.py
│   │   ├── ppu.py         # PPU 模拟器
│   │   └── renderer.py    # 渲染系统
│   ├── bus/
│   │   ├── __init__.py
│   │   └── mainbus.py     # 内存总线系统
│   ├── cartridge/
│   │   ├── __init__.py
│   │   ├── cartridge.py   # 卡带加载
│   │   └── mapper.py      # 映射器实现
│   ├── controller/
│   │   ├── __init__.py
│   │   └── controller.py  # 控制器系统
│   └── emulator/
│       ├── __init__.py
│       ├── emulator.py    # 主模拟器循环
│       └── apu.py         # 音频处理单元
├── venv/                  # Python 虚拟环境
└── __init__.py
```

## 使用方法

### 安装依赖

```bash
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行模拟器

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行模拟器
python main.py [options] <rom_path>

# 示例
python main.py -s 3 SuperMarioBros.nes
```

### 命令行选项

- `-h, --help`: 显示帮助信息
- `-s, --scale`: 设置显示比例（默认：3）
- `-w, --width`: 设置窗口宽度
- `-H, --height`: 设置窗口高度

### 默认控制键

**玩家 1**
- A: J
- B: K
- Select: 右 Shift
- Start: 回车
- 上: W
- 下: S
- 左: A
- 右: D

**玩家 2**
- A: 小键盘 5
- B: 小键盘 6
- Select: 小键盘 8
- Start: 小键盘 9
- 上: 上箭头
- 下: 下箭头
- 左: 左箭头
- 右: 右箭头

## 实现特性

- **CPU 模拟**: 支持 6502 指令集的大部分指令
- **图形渲染**: 基本的 PPU 功能，支持背景和精灵渲染
- **音频处理**: 实现完整的 APU，包括所有声音通道
- **ROM 支持**: 支持 iNES 格式 ROM，兼容多种映射器
- **输入处理**: 键盘控制，支持双玩家
- **可扩展性**: 模块化设计，易于添加新功能

## 当前状态

SimpleNES-py 已经实现了 NES 模拟器的核心功能，包括 CPU、PPU、内存系统、卡带映射器、控制器和音频系统。虽然还不能运行所有 NES 游戏（因为一些高级功能仍在开发中），但已构建了一个完整的框架，可以继续扩展和完善。

## 后续开发建议

1. **完善 CPU 指令**: 实现所有 6502 指令及精确的时序
2. **增强 PPU**: 实现完整的精灵 0 碰撞检测、掩码控制等
3. **优化性能**: 使用 NumPy 优化渲染和音频处理
4. **添加调试工具**: 内存查看器、CPU 跟踪等功能
5. **支持更多映射器**: 实现更复杂的映射器类型
6. **保存状态**: 实现游戏存档和回放功能

## 许可证

该项目基于原始 SimpleNES 项目的许可证，具体请查看 LICENSE 文件。
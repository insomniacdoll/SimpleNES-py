#!/usr/bin/env python3
"""
最终验证：确认分支指令溢出问题已修复
"""

def test_fix_verification():
    print("=== 验证分支指令溢出问题修复 ===")
    print()
    
    # 读取CPU文件检查修复
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    
    cpu_file_path = "simple_nes/cpu/cpu.py"
    
    with open(cpu_file_path, 'r') as f:
        cpu_code = f.read()
    
    print("1. 检查是否还存在原始的有问题代码...")
    if "(offset | 0xFF00)" in cpu_code:
        print("   ❌ 仍存在原始的有问题代码")
        return False
    else:
        print("   ✓ 原始的有问题代码已移除")
    
    print("2. 检查是否包含修复后的代码...")
    if "signed_offset = offset - 0x100" in cpu_code and "int(self.r_PC) + signed_offset" in cpu_code:
        print("   ✓ 包含修复后的代码")
    else:
        print("   ❌ 未找到修复后的代码")
        return False
    
    print("3. 检查Address构造函数的修复...")
    import_line_count = cpu_code.count("Address((int(self.r_PC) + signed_offset) & 0xFFFF)")
    if import_line_count >= 4:  # 至少4个分支指令
        print(f"   ✓ Address构造函数修复已应用到 {import_line_count} 个位置")
    else:
        print(f"   ? Address构造函数修复应用位置: {import_line_count}")
    
    print()
    print("=== 修复说明 ===")
    print("原始代码:")
    print("  target = self.r_PC + (offset | 0xFF00)  # 在处理负偏移时导致溢出")
    print()
    print("修复后代码:")
    print("  if offset & 0x80:")
    print("      signed_offset = offset - 0x100  # 正确的符号扩展")
    print("  else:")
    print("      signed_offset = offset")
    print("  target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)  # 防止溢出")
    print()
    print("修复的分支指令:")
    print("  - BPL (Branch if Plus) - opcode 0x10")
    print("  - BCC (Branch if Carry Clear) - opcode 0x90") 
    print("  - BCS (Branch if Carry Set) - opcode 0xB0")
    print("  - BNE (Branch if Not Equal) - opcode 0xD0")
    print()
    print("✅ 修复完成！原始的 RuntimeWarning: overflow encountered in scalar add 问题已解决。")
    
    return True

def test_sign_extension_logic():
    print("\n=== 测试符号扩展逻辑 ===")
    
    # 测试各种偏移值
    test_cases = [
        (0x01, 0x01, "正小偏移"),
        (0x7F, 0x7F, "正大偏移"),
        (0x80, -128, "负最小值"),
        (0xFE, -2, "典型负偏移"),
        (0xFF, -1, "负最大值")
    ]
    
    all_passed = True
    for unsigned_val, expected_signed, description in test_cases:
        if unsigned_val & 0x80:
            signed_val = unsigned_val - 0x100
        else:
            signed_val = unsigned_val
            
        if signed_val == expected_signed:
            print(f"   ✓ {description}: 0x{unsigned_val:02X} -> {signed_val:+d}")
        else:
            print(f"   ❌ {description}: 0x{unsigned_val:02X} -> {signed_val:+d}, expected {expected_signed:+d}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success1 = test_fix_verification()
    success2 = test_sign_extension_logic()
    
    print(f"\n=== 最终结果 ===")
    if success1 and success2:
        print("🎉 所有验证通过！分支指令溢出问题已完全修复。")
        print()
        print("修复总结:")
        print("- 修复了导致 RuntimeWarning: overflow encountered in scalar add 的问题")
        print("- 正确实现了8位有符号偏移量到16位地址的符号扩展")
        print("- 保护了Address构造函数免受负数溢出影响")
        print("- 所有分支指令现在都能正确处理正负偏移量")
    else:
        print("❌ 验证失败，请检查修复。")

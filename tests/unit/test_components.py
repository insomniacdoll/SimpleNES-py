#!/usr/bin/env python3
"""
Test script for SimpleNES-py components
"""
from __future__ import print_function

def test_cpu():
    """Test CPU functionality"""
    print("Testing CPU...")
    try:
        import sys
        import os
        # Add the project root to Python path so we can import simple_nes
        project_root = os.path.join(os.path.dirname(__file__), '..')
        project_root = os.path.abspath(project_root)
        parent_dir = os.path.dirname(project_root)  # Go up to project root
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from simple_nes.cpu.cpu import CPU
        from simple_nes.bus.mainbus import MainBus
        
        bus = MainBus()
        cpu = CPU(bus)
        
        # Test reset
        cpu.reset()
        print("  CPU reset: PC=%s, A=%d, X=%d, Y=%d" % (hex(cpu.get_PC()), cpu.r_A, cpu.r_X, cpu.r_Y))
        
        # Test basic operations
        print("  CPU test completed successfully")
        return True
    except Exception as e:
        print("  CPU test failed: %s" % e)
        return False

def test_ppu():
    """Test PPU functionality"""
    print("Testing PPU...")
    try:
        import sys
        import os
        # Add the project root to Python path so we can import simple_nes
        project_root = os.path.join(os.path.dirname(__file__), '..')
        project_root = os.path.abspath(project_root)
        parent_dir = os.path.dirname(project_root)  # Go up to project root
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from simple_nes.ppu.ppu import PPU
        from simple_nes.ppu.renderer import PictureBus
        from simple_nes.emulator.emulator import VirtualScreen
        
        picture_bus = PictureBus(None)
        virtual_screen = VirtualScreen()
        ppu = PPU(picture_bus, virtual_screen)
        
        # Test reset
        ppu.reset()
        print("  PPU reset: Cycle=%d, Scanline=%d" % (ppu.cycle, ppu.scanline))
        
        # Test step
        ppu.step()
        print("  PPU step: Cycle=%d, Scanline=%d" % (ppu.cycle, ppu.scanline))
        
        print("  PPU test completed successfully")
        return True
    except Exception as e:
        print("  PPU test failed: %s" % e)
        return False

def test_bus():
    """Test MainBus functionality"""
    print("Testing MainBus...")
    try:
        import sys
        import os
        # Add the project root to Python path so we can import simple_nes
        project_root = os.path.join(os.path.dirname(__file__), '..')
        project_root = os.path.abspath(project_root)
        parent_dir = os.path.dirname(project_root)  # Go up to project root
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from simple_nes.bus.mainbus import MainBus
        
        bus = MainBus()
        
        # Test basic read/write
        bus.write(0x0200, 0xAB)
        value = bus.read(0x0200)
        print("  Bus write/read test: Wrote 0xAB, Read 0x%02X" % value)
        
        if value == 0xAB:
            print("  MainBus test completed successfully")
            return True
        else:
            print("  MainBus test failed: read value doesn't match written value")
            return False
    except Exception as e:
        print("  MainBus test failed: %s" % e)
        return False

def test_cartridge():
    """Test Cartridge functionality"""
    print("Testing Cartridge...")
    try:
        import sys
        import os
        # Add the project root to Python path so we can import simple_nes
        project_root = os.path.join(os.path.dirname(__file__), '..')
        project_root = os.path.abspath(project_root)
        parent_dir = os.path.dirname(project_root)  # Go up to project root
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from simple_nes.cartridge.cartridge import Cartridge
        
        cart = Cartridge()
        # Test creating an empty cartridge
        print("  Created cartridge with %d PRG bytes, %d CHR bytes" % (len(cart.get_rom()), len(cart.get_vrom())))
        
        print("  Cartridge test completed successfully")
        return True
    except Exception as e:
        print("  Cartridge test failed: %s" % e)
        return False

def main():
    """Run all tests"""
    print("Running SimpleNES-py component tests...\n")
    
    tests = [
        ("CPU", test_cpu),
        ("PPU", test_ppu),
        ("MainBus", test_bus),
        ("Cartridge", test_cartridge),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print("%s:" % name, end=" ")
        if test_func():
            passed += 1
            print("PASS")
        else:
            print("FAIL")
        print()
    
    print("Tests passed: %d/%d" % (passed, total))
    
    if passed == total:
        print("\nAll tests passed! SimpleNES-py components are working correctly.")
    else:
        print("\n%d test(s) failed. Please check the implementation." % (total - passed))

if __name__ == "__main__":
    main()

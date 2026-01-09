#!/usr/bin/env python3
"""
Test script for SimpleNES-py components
"""
from __future__ import print_function

def test_cpu():
    """Test CPU functionality"""
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
    
    # Test basic operations
    assert cpu is not None

def test_ppu():
    """Test PPU functionality"""
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
    
    # Test step
    ppu.step()
    
    assert ppu is not None

def test_bus():
    """Test MainBus functionality"""
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
    
    assert value == 0xAB

def test_cartridge():
    """Test Cartridge functionality"""
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
    
    assert cart is not None

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

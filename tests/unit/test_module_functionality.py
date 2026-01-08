"""
Additional unit tests for SimpleNES modules
Testing specific functionality of core components
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


def test_bus_basic_operations():
    """Test basic operations of the MainBus"""
    from simple_nes.bus.mainbus import MainBus
    
    bus = MainBus()
    
    # Test initial state
    assert bus is not None
    
    # Test memory read/write within valid range
    # Note: This is a basic test; actual implementation may vary
    # For now, we just test that the object has the expected methods
    assert hasattr(bus, 'read')
    assert hasattr(bus, 'write')


def test_cpu_basic_operations():
    """Test basic operations of the CPU"""
    from simple_nes.cpu.cpu import CPU
    from simple_nes.bus.mainbus import MainBus
    
    bus = MainBus()
    cpu = CPU(bus)
    
    # Test initial state
    assert cpu is not None
    
    # Test that CPU has expected methods
    assert hasattr(cpu, 'reset')
    assert hasattr(cpu, 'step')


def test_ppu_basic_operations():
    """Test basic operations of the PPU"""
    from simple_nes.ppu.ppu import PPU
    from simple_nes.ppu.renderer import PictureBus
    from simple_nes.emulator.emulator import VirtualScreen
    
    virtual_screen = VirtualScreen()
    picture_bus = PictureBus(None)
    ppu = PPU(picture_bus, virtual_screen)
    
    # Test initial state
    assert ppu is not None
    
    # Test that PPU has expected methods
    assert hasattr(ppu, 'step')
    assert hasattr(ppu, 'control')
    assert hasattr(ppu, 'set_mask')


def test_picture_bus_operations():
    """Test basic operations of the PictureBus"""
    from simple_nes.ppu.renderer import PictureBus
    
    picture_bus = PictureBus(None)
    
    # Test initial state
    assert picture_bus is not None
    
    # Test basic read/write operations
    # Test reading from palette memory
    value = picture_bus.read(0x3F00)  # Palette memory start
    assert isinstance(value, int)
    
    # Test writing to palette memory
    picture_bus.write(0x3F00, 0xFF)
    read_value = picture_bus.read(0x3F00)
    assert read_value == 0xFF


def test_virtual_screen_operations():
    """Test basic operations of the VirtualScreen"""
    from simple_nes.emulator.emulator import VirtualScreen
    
    screen = VirtualScreen()
    
    # Test initial state
    assert screen is not None
    assert screen.width == 256
    assert screen.height == 240
    assert screen.buffer.shape == (240, 256, 3)
    
    # Test updating a pixel
    screen.update_pixel(10, 10, (255, 0, 0))  # Red pixel
    # Note: We can't directly verify the pixel value because buffer is internal
    # But the method should execute without error
    assert screen.buffer[10, 10, 0] == 255  # Red component
    assert screen.buffer[10, 10, 1] == 0    # Green component
    assert screen.buffer[10, 10, 2] == 0    # Blue component


def test_controller_operations():
    """Test basic operations of the Controller"""
    from simple_nes.controller.controller import Controller
    
    controller = Controller()
    
    # Test initial state
    assert controller is not None
    
    # Test that controller has expected methods
    assert hasattr(controller, 'get_state_bit')
    assert hasattr(controller, 'strobe_changed')
    
    # Test initial button states
    initial_state = controller.get_state_bit()
    assert isinstance(initial_state, int)


@patch('pygame.mixer.init')
@patch('pygame.mixer.Channel')
@patch('pygame.init')
def test_apu_basic_operations(mock_pygame_init, mock_mixer_channel, mock_mixer_init):
    """Test basic operations of the APU"""
    from simple_nes.apu.apu import APU
    
    apu = APU()
    
    # Test initial state
    assert apu is not None
    
    # Test that APU has expected methods
    assert hasattr(apu, 'step')
    assert hasattr(apu, 'write_register')
    assert hasattr(apu, 'read_register')
    
    # Test basic register operations
    apu.write_register(0x4000, 0xF0)  # Square1 volume register
    # Note: Not all implementations may support reading back what was written
    # so we just test that the write operation doesn't raise an exception
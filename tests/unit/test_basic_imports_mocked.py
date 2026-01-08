"""
Unit tests for SimpleNES modules with proper pygame mocking
These tests ensure that modules can be imported and basic functionality works
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os


def test_mainbus_import():
    """Test that MainBus can be imported and instantiated"""
    from simple_nes.bus.mainbus import MainBus
    bus = MainBus()
    assert bus is not None


def test_cartridge_import():
    """Test that Cartridge can be imported and instantiated"""
    from simple_nes.cartridge.cartridge import Cartridge
    cart = Cartridge()
    assert cart is not None


def test_mapper_import():
    """Test that Mapper can be imported"""
    from simple_nes.cartridge.mapper import Mapper
    assert Mapper is not None


def test_cpu_import():
    """Test that CPU can be imported and instantiated"""
    from simple_nes.cpu.cpu import CPU
    from simple_nes.bus.mainbus import MainBus
    
    bus = MainBus()
    cpu = CPU(bus)
    assert cpu is not None


def test_ppu_import():
    """Test that PPU can be imported and instantiated"""
    from simple_nes.ppu.ppu import PPU
    from simple_nes.ppu.renderer import PictureBus
    from simple_nes.emulator.emulator import VirtualScreen
    
    virtual_screen = VirtualScreen()
    picture_bus = PictureBus(None) 
    ppu = PPU(picture_bus, virtual_screen)
    assert ppu is not None


def test_renderer_import():
    """Test that Renderer can be imported and instantiated"""
    from simple_nes.ppu.renderer import Renderer, PictureBus
    from simple_nes.ppu.ppu import PPU
    from simple_nes.emulator.emulator import VirtualScreen
    
    virtual_screen = VirtualScreen()
    picture_bus = PictureBus(None)
    ppu = PPU(picture_bus, virtual_screen)
    renderer = Renderer(ppu)
    assert renderer is not None


def test_controller_import():
    """Test that Controller components can be imported and instantiated"""
    from simple_nes.controller.controller import Controller, ControllerManager
    
    controller1 = Controller()
    controller2 = Controller()
    manager = ControllerManager()
    assert controller1 is not None
    assert controller2 is not None
    assert manager is not None


@patch('pygame.mixer', MagicMock())
@patch('pygame.init')
def test_apu_import(mock_pygame_init):
    """Test that APU can be imported and instantiated with mocked pygame"""
    # Make sure mixer module is properly mocked
    import sys
    from unittest.mock import MagicMock
    
    if 'pygame' in sys.modules and hasattr(sys.modules['pygame'], 'mixer'):
        sys.modules['pygame'].mixer = MagicMock()
    else:
        # Ensure pygame.mixer is mocked at the module level
        import pygame
        pygame.mixer = MagicMock()
        pygame.mixer.init = MagicMock()
        pygame.mixer.Channel = MagicMock()
    
    from simple_nes.apu.apu import APU
    
    apu = APU()
    assert apu is not None


@patch('pygame.display.set_mode')
@patch('pygame.display.set_caption')
@patch('pygame.mixer', MagicMock())
@patch('pygame.time.Clock')
@patch('pygame.init')
def test_emulator_import(mock_pygame_init, mock_clock, mock_caption, mock_set_mode):
    """Test that Emulator can be imported and instantiated with mocked pygame"""
    # Mock the display surface
    mock_surface = MagicMock()
    mock_set_mode.return_value = mock_surface
    mock_clock.return_value = MagicMock()
    
    from simple_nes.emulator.emulator import Emulator
    
    emulator = Emulator()
    assert emulator is not None


def test_full_emulator_module_import():
    """Test that the full emulator system can be imported"""
    from simple_nes.emulator.emulator import Emulator
    from simple_nes.cpu.cpu import CPU
    from simple_nes.ppu.ppu import PPU
    from simple_nes.bus.mainbus import MainBus
    from simple_nes.cartridge.cartridge import Cartridge
    from simple_nes.cartridge.mapper import Mapper
    from simple_nes.controller.controller import ControllerManager
    from simple_nes.apu.apu import APU
    from simple_nes.ppu.renderer import Renderer, PictureBus
    
    # Verify all classes exist
    assert Emulator is not None
    assert CPU is not None
    assert PPU is not None
    assert MainBus is not None
    assert Cartridge is not None
    assert Mapper is not None
    assert ControllerManager is not None
    assert APU is not None
    assert Renderer is not None
    assert PictureBus is not None
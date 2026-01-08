"""
Basic unit tests for SimpleNES modules
These tests ensure that modules can be imported and basic functionality works
"""
import pytest
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


def test_apu_import():
    """Test that APU can be imported and instantiated"""
    import pygame
    pygame.init()  # Initialize pygame before importing APU
    
    # Mock pygame.mixer if it's not available
    import sys
    from unittest.mock import Mock
    
    # Check if mixer is available
    if not hasattr(pygame, 'mixer') or pygame.mixer is None or isinstance(pygame.mixer, Mock):
        # If mixer is not available, we'll mock it
        original_mixer = pygame.mixer if hasattr(pygame, 'mixer') else None
        pygame.mixer = Mock()
        pygame.mixer.init = Mock()
        pygame.mixer.Channel = Mock()
    
    from simple_nes.apu.apu import APU
    
    apu = APU()
    assert apu is not None


def test_emulator_import():
    """Test that Emulator can be imported and instantiated"""
    import pygame
    from unittest.mock import Mock
    
    # Initialize pygame and handle potential missing modules
    pygame.init()
    
    # Mock pygame.mixer if needed
    if not hasattr(pygame, 'mixer') or pygame.mixer is None or isinstance(pygame.mixer, Mock):
        original_mixer = pygame.mixer if hasattr(pygame, 'mixer') else None
        pygame.mixer = Mock()
        pygame.mixer.init = Mock()
        pygame.mixer.Channel = Mock()
    
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
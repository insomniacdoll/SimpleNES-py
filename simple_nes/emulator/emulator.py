"""
Main Emulator for SimpleNES-py
Coordinates all components of the NES emulation
"""
import pygame
import sys
import time
import numpy as np
from typing import Optional, List

# Import our components
from simple_nes.cpu.cpu import CPU
from simple_nes.ppu.ppu import PPU
from simple_nes.ppu.renderer import PictureBus, Renderer
from simple_nes.bus.mainbus import MainBus
from simple_nes.cartridge.cartridge import Cartridge
from simple_nes.cartridge.mapper import Mapper
from simple_nes.controller.controller import ControllerManager
from simple_nes.apu.apu import APU
from simple_nes.util.logging import info, error, debug, warning

# Constants
NES_VIDEO_WIDTH = 256
NES_VIDEO_HEIGHT = 240

class VirtualScreen:
    def __init__(self, width: int = NES_VIDEO_WIDTH, height: int = NES_VIDEO_HEIGHT):
        self.width = width
        self.height = height
        self.buffer = np.zeros((height, width, 3), dtype=np.uint8)
    
    def update_pixel(self, x: int, y: int, color: tuple):
        """Update a single pixel in the virtual screen"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = color
    
    def set_pixel(self, x: int, y: int, color: tuple):
        """Set a single pixel in the virtual screen (alias for update_pixel)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = color

class Emulator:
    def __init__(self, config_path: str = None):
        # Initialize pygame
        pygame.init()
        
        # Initialize components
        self.bus = MainBus()
        self.cartridge = Cartridge()
        self.mapper = None
        
        # Create picture bus (connects PPU to graphics memory)
        self.picture_bus = PictureBus(None)  # Will be connected to mapper later
        
        # Create virtual screen for PPU to render to
        self.virtual_screen = VirtualScreen()
        
        # Create PPU with picture bus and virtual screen
        self.ppu = PPU(self.picture_bus, self.virtual_screen)
        
        # Create CPU with main bus
        self.cpu = CPU(self.bus)
        
        # Create APU for audio with IRQ callback
        self.apu = APU(irq_callback=self._irq_interrupt)
        
        # Initialize controller manager with config
        self.controller_manager = ControllerManager(config_path)
        
        # Log emulator initialization
        info("SimpleNES emulator initialized")
        
        # Initialize pygame window
        self.screen_scale = 3  # Default scale
        self.desired_width = 0
        self.desired_height = 0
        
        # Create pygame window
        self.screen_width = NES_VIDEO_WIDTH * self.screen_scale
        self.screen_height = NES_VIDEO_HEIGHT * self.screen_scale
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("SimpleNES-py")
        
        # Create renderer
        self.renderer = Renderer(self.virtual_screen)
        
        # FPS control
        self.clock = pygame.time.Clock()
        self.target_fps = 60  # NTSC NES runs at ~60 FPS
        
        # Timing
        self.cycle_timer = time.perf_counter()
        self.elapsed_time = 0
        self.cpu_cycle_duration = 1 / (1.7898 * 10**6)  # NTSC CPU clock rate
        
        # Set up PPU interrupt callback
        self.ppu.set_interrupt_callback(self._nmi_interrupt)
        
        # Set up memory callbacks for I/O registers
        self._setup_io_callbacks()
        
        # Set up APU callbacks
        self._setup_apu_callbacks()
    
    def _setup_apu_callbacks(self):
        """Set up callbacks for APU registers"""
        # Set up APU register callbacks in the main bus
        # APU registers range from 0x4000-0x4013
        for addr in range(0x4000, 0x4014):
            # Create closure to capture the current addr value
            def make_write_callback(a):
                return lambda value: self.apu.write_register(a, value)
            def make_read_callback(a):
                return lambda: self.apu.read_register(a)
            
            self.bus.set_write_callback(addr, make_write_callback(addr))
            if addr != 0x4014:  # 0x4014 is write-only (DMC I/O)
                self.bus.set_read_callback(addr, make_read_callback(addr))
    
    def _update_mirroring(self):
        """Callback to update nametable mirroring"""
        # In a complete implementation, this would update the PictureBus
        # with the current mirroring configuration
        mirroring_type = self.mapper.get_name_table_mirroring() if self.mapper else 0
        self.picture_bus.mirroring_type = mirroring_type
    
    def _setup_io_callbacks(self):
        """Set up callbacks for I/O register access"""
        # PPU write registers
        self.bus.set_write_callback(0x2000, self.ppu.control)
        self.bus.set_write_callback(0x2001, self.ppu.set_mask)
        self.bus.set_write_callback(0x2003, self.ppu.set_oam_address)
        self.bus.set_write_callback(0x2005, self.ppu.set_scroll)
        self.bus.set_write_callback(0x2006, self.ppu.set_data_address)
        self.bus.set_write_callback(0x2007, self.ppu.set_data)
        self.bus.set_write_callback(0x2004, self.ppu.set_oam_data)
        
        # PPU read registers
        self.bus.set_read_callback(0x2002, self.ppu.get_status)
        self.bus.set_read_callback(0x2007, self.ppu.get_data)
        self.bus.set_read_callback(0x2004, self.ppu.get_oam_data)
        
        # Controller registers
        self.bus.set_read_callback(0x4016, self._read_controller1)
        self.bus.set_read_callback(0x4017, self._read_controller2)
        self.bus.set_write_callback(0x4016, self._write_controller_strobe)
        
        # DMA register
        self.bus.set_write_callback(0x4014, self._dma_transfer)
    
    def _nmi_interrupt(self):
        """Handle NMI interrupt from PPU"""
        self.cpu.interrupt('NMI')
    
    def _irq_interrupt(self):
        """Handle IRQ interrupt from mapper (e.g., MMC3)"""
        self.cpu.interrupt('IRQ')
    
    def _read_controller1(self) -> int:
        """Read from controller port 1"""
        return self.controller_manager.controller1.get_state_bit()
    
    def _read_controller2(self) -> int:
        """Read from controller port 2"""
        return self.controller_manager.controller2.get_state_bit()
    
    def _write_controller_strobe(self, value: int):
        """Handle controller strobe signal"""
        strobe = bool(value & 1)
        self.controller_manager.controller1.strobe_changed(strobe)
        self.controller_manager.controller2.strobe_changed(strobe)
    
    def _dma_transfer(self, page: int):
        """Handle DMA transfer to PPU OAM"""
        # Get the page from CPU memory space and transfer to PPU OAM
        page_ptr = self.bus.get_page_ptr(page)
        if page_ptr:
            self.ppu.do_DMA(page_ptr)
        # DMA takes 513 or 514 CPU cycles
        self.cpu.skip_DMA_cycles()
    
    def set_video_width(self, width: int):
        """Set the video width (aspect ratio will be maintained)"""
        self.desired_width = width
        self.screen_scale = width // NES_VIDEO_WIDTH
        if self.screen_scale < 1:
            self.screen_scale = 1
    
    def set_video_height(self, height: int):
        """Set the video height (aspect ratio will be maintained)"""
        self.desired_height = height
        self.screen_scale = height // NES_VIDEO_HEIGHT
        if self.screen_scale < 1:
            self.screen_scale = 1
    
    def set_video_scale(self, scale: float):
        """Set the video scale factor"""
        self.screen_scale = int(scale)
        if self.screen_scale < 1:
            self.screen_scale = 1
    
    def set_keys(self, p1_keys: List, p2_keys: List):
        """Set custom key mappings for controllers"""
        self.controller_manager.set_controller_keys(p1_keys, p2_keys)
    
    def load_rom(self, rom_path: str) -> bool:
        """Load a ROM file into the emulator"""
        debug(f"Attempting to load ROM: {rom_path}")
        
        if not self.cartridge.load_from_file(rom_path):
            error(f"Failed to load ROM: {rom_path}")
            return False
        
        info(f"Successfully loaded ROM: {rom_path}")
        info(f"  Mapper: {self.cartridge.get_mapper()}")
        info(f"  PRG ROM size: {len(self.cartridge.get_rom())} bytes")
        info(f"  CHR ROM size: {len(self.cartridge.get_vrom())} bytes")
        
        # Create appropriate mapper
        self.mapper = Mapper.create_mapper(
            self.cartridge.get_mapper(),
            self.cartridge,
            self._irq_interrupt,  # interrupt callback for IRQ
            self._nmi_interrupt,  # NMI callback
            self._update_mirroring  # mirroring callback
        )
        
        if self.mapper is None:
            error(f"Failed to create mapper for ROM: {rom_path}")
            return False
        
        # Set the mapper in the bus and picture bus
        self.bus.set_mapper(self.mapper)
        # Update the picture bus to refer to mapper for CHR access
        self.picture_bus.mapper = self.mapper
        
        # Reset CPU to start execution
        self.cpu.reset(skip_vblank_wait=False)
        
        info("ROM loaded and emulator reset successfully")
        return True
    
    def run(self, rom_path: str):
        """Main emulation loop - time-driven like C++ version"""
        if not self.load_rom(rom_path):
            error(f"Failed to load ROM: {rom_path}")
            return
        
        info("Starting emulation...")
        
        # Create window
        self.screen_width = NES_VIDEO_WIDTH * self.screen_scale
        self.screen_height = NES_VIDEO_HEIGHT * self.screen_scale
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("SimpleNES-py")
        
# Clock constants (matching C++ implementation)
        # NES CPU: ~1.7898 MHz (NTSC)
        # NES PPU: ~5.369 MHz (3x CPU speed)
        # Frame: 60 FPS
        cpu_clock_period_ns = 559  # ~1.7898 MHz
        cpu_clock_period_s = cpu_clock_period_ns / 1e9
        max_cycles_per_frame = 29781  # One frame worth of cycles (NTSC: ~29780.5 CPU cycles per frame)
        
        # Timing variables
        last_wakeup = time.perf_counter()
        elapsed_time = 0.0
        running = True
        frame_count = 0
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    info("Emulator window closed by user")
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        info("ESC pressed, exiting emulator")
                        running = False
            
            # Update controller states based on current keys
            self.controller_manager.update_controller_states()
            
            # Calculate elapsed time since last frame
            now = time.perf_counter()
            elapsed_time += now - last_wakeup
            last_wakeup = now
            
            # Run emulation for elapsed time
            # This is the time-driven approach matching C++ implementation
            # We need to run enough cycles for PPU to complete at least one full frame
            cycles_this_frame = 0
            
            # Continue executing for max_cycles_per_frame cycles
            while elapsed_time > cpu_clock_period_s and cycles_this_frame < max_cycles_per_frame:
                # PPU (3 cycles per CPU cycle)
                self.ppu.step()
                self.ppu.step()
                self.ppu.step()
                
                # Check for PPU scanline-based interrupts (for MMC3, etc.)
                if self.mapper:
                    self.mapper.scanline_irq()
                
                # CPU (1 cycle)
                self.cpu.step()
                
                # APU (1 cycle)
                self.apu.step()
                
                elapsed_time -= cpu_clock_period_s
                cycles_this_frame += 1
            
            # Render frame
            self._render_frame()
            
            # Control frame rate - this adds the necessary delay
            self.clock.tick(self.target_fps)
            frame_count += 1
        
        info("Emulator shutting down...")
        pygame.quit()
        sys.exit()
    
    def _render_frame(self):
        """Render the current frame to the screen"""
        # Use the renderer to update the display
        self.renderer.update_display(self.screen, self.screen_scale)
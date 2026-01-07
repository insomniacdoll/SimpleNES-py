"""
Rendering system for SimpleNES-py
Handles converting PPU output to Pygame display
"""
import pygame
import numpy as np
from src.simple_nes.ppu.ppu import PPU
from ..bus.mainbus import MainBus
from ..cartridge.mapper import Mapper

class Renderer:
    def __init__(self, ppu: PPU, screen_width: int = 256, screen_height: int = 240):
        self.ppu = ppu
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialize pygame display surface
        self.display_surface = pygame.Surface((screen_width, screen_height))
        
        # Palette mapping (simplified)
        # In a real implementation, this would use the NES color palette
        self.palette = self._generate_nes_palette()
    
    def _generate_nes_palette(self):
        """Generate a simplified NES color palette"""
        # This is a simplified palette - a full implementation would use the
        # exact NES color values
        palette = []
        for i in range(64):  # NES has 64 colors in its palette
            if i < 16:
                # First 16 colors are grays and blacks
                val = int(i * 16)
                palette.append((val, val, val))
            elif i < 32:
                # Next 16 are various colors
                palette.append((255, 0, 0))  # Red
            elif i < 48:
                # Next 16 are more colors
                palette.append((0, 255, 0))  # Green
            else:
                # Last 16
                palette.append((0, 0, 255))  # Blue
        return palette
    
    def render_frame(self):
        """Render a complete frame from PPU data"""
        # Get the picture buffer from PPU
        picture_buffer = self.ppu.picture_buffer
        
        # Convert the PPU buffer to a pygame surface
        # Create a temporary surface to hold the raw pixel data
        temp_surface = pygame.Surface((self.screen_width, self.screen_height))
        
        # Copy pixels from PPU buffer to pygame surface
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                # Get RGB values from picture buffer
                r, g, b = picture_buffer[y, x]
                color = (int(r), int(g), int(b))
                temp_surface.set_at((x, y), color)
        
        # Scale the surface to fit the display requirements
        return temp_surface
    
    def update_display(self, screen, scale_factor=1):
        """Update the display with the current frame"""
        # Render the current frame
        frame_surface = self.render_frame()
        
        # Scale the frame if needed
        if scale_factor != 1:
            frame_surface = pygame.transform.scale(
                frame_surface,
                (self.screen_width * scale_factor, self.screen_height * scale_factor)
            )
        
        # Blit to the main screen
        screen.blit(frame_surface, (0, 0))
        pygame.display.flip()

class PictureBus:
    """
    Picture Bus - handles communication between PPU and graphics memory
    """
    def __init__(self, mapper):
        self.mapper = mapper
        self.vram = [0] * 0x1000  # 4KB VRAM
        self.palette_memory = [0] * 0x20  # 32 bytes for palette
        self.mirroring_type = 0  # 0=horizontal, 1=vertical, etc.
    
    def read(self, addr):
        """Read from picture memory"""
        if addr < 0x2000:
            # Pattern table access - goes to cartridge CHR ROM/RAM
            if self.mapper:
                return self.mapper.read_chr(addr)
            else:
                return 0
        elif addr < 0x3000:
            # Nametable access - mirrored to 0x2000-0x2FFF
            actual_addr = addr & 0x2FFF
            if actual_addr >= 0x2800:
                actual_addr -= 0x800  # Nametable 2 mirrors nametable 0
            elif actual_addr >= 0x2400:
                actual_addr -= 0x400  # Nametable 1 mirrors nametable 0 or 2 depending on mirroring
            elif actual_addr >= 0x2000:
                actual_addr -= 0x000  # Nametable 0
                
            # Handle nametable mirroring based on cartridge type
            actual_addr = actual_addr & 0x2FFF  # Keep within VRAM range
            if actual_addr < len(self.vram):
                return self.vram[actual_addr]
            else:
                return 0
        elif addr >= 0x3F00 and addr < 0x4000:
            # Palette memory
            palette_addr = (addr - 0x3F00) & 0x1F  # Mirror at 0x20 bytes
            return self.palette_memory[palette_addr]
        else:
            # Other addresses return 0
            return 0
    
    def write(self, addr, value):
        """Write to picture memory"""
        if addr < 0x2000:
            # Pattern table access - goes to cartridge CHR ROM/RAM
            if self.mapper:
                self.mapper.write_chr(addr, value)
        elif addr < 0x3000:
            # Nametable access - mirrored to 0x2000-0x2FFF
            actual_addr = addr & 0x2FFF
            if actual_addr >= 0x2800:
                actual_addr -= 0x800  # Nametable 2 mirrors nametable 0
            elif actual_addr >= 0x2400:
                actual_addr -= 0x400  # Nametable 1 mirrors nametable 0 or 2 depending on mirroring
            elif actual_addr >= 0x2000:
                actual_addr -= 0x000  # Nametable 0
                
            # Handle nametable mirroring based on cartridge type
            actual_addr = actual_addr & 0x2FFF  # Keep within VRAM range
            if actual_addr < len(self.vram):
                self.vram[actual_addr] = value
        elif addr >= 0x3F00 and addr < 0x4000:
            # Palette memory
            palette_addr = (addr - 0x3F00) & 0x1F  # Mirror at 0x20 bytes
            self.palette_memory[palette_addr] = value
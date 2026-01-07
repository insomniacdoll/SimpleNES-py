"""
Controller system for SimpleNES-py
Handles input from keyboard/gamepad
"""
import pygame
from typing import List

class Controller:
    def __init__(self):
        # Controller state - corresponds to NES controller bits
        self.state = 0
        self.strobe = False
        
        # Button mapping (for keyboard)
        self.button_map = {
            'A': 0,        # Bit 0
            'B': 1,        # Bit 1
            'SELECT': 2,   # Bit 2
            'START': 3,    # Bit 3
            'UP': 4,       # Bit 4
            'DOWN': 5,     # Bit 5
            'LEFT': 6,     # Bit 6
            'RIGHT': 7     # Bit 7
        }
        
        # Button states
        self.buttons = {
            'A': False,
            'B': False,
            'SELECT': False,
            'START': False,
            'UP': False,
            'DOWN': False,
            'LEFT': False,
            'RIGHT': False
        }
    
    def set_key_state(self, key: str, pressed: bool):
        """Set the state of a specific button"""
        if key in self.buttons:
            self.buttons[key] = pressed
    
    def strobe_changed(self, strobe: bool):
        """Handle strobe signal change from CPU"""
        if not self.strobe and strobe:
            # Rising edge - latch current state
            self.state = 0
            if self.buttons['A']:
                self.state |= 1 << 0
            if self.buttons['B']:
                self.state |= 1 << 1
            if self.buttons['SELECT']:
                self.state |= 1 << 2
            if self.buttons['START']:
                self.state |= 1 << 3
            if self.buttons['UP']:
                self.state |= 1 << 4
            if self.buttons['DOWN']:
                self.state |= 1 << 5
            if self.buttons['LEFT']:
                self.state |= 1 << 6
            if self.buttons['RIGHT']:
                self.state |= 1 << 7
        self.strobe = strobe
    
    def get_state_bit(self) -> int:
        """Get the current state bit and shift the register"""
        bit = self.state & 1
        if not self.strobe:
            # Shift register if not in strobe mode
            self.state >>= 1
        return bit

class ControllerManager:
    def __init__(self):
        self.controller1 = Controller()
        self.controller2 = Controller()
        self.keyboard_mapping = self._default_keyboard_mapping()
    
    def _default_keyboard_mapping(self):
        """Set up default keyboard mappings"""
        return {
            # Player 1
            pygame.K_j: 'A',           # A
            pygame.K_k: 'B',           # B
            pygame.K_RSHIFT: 'SELECT', # Select
            pygame.K_RETURN: 'START',  # Start
            pygame.K_w: 'UP',          # Up
            pygame.K_s: 'DOWN',        # Down
            pygame.K_a: 'LEFT',        # Left
            pygame.K_d: 'RIGHT',       # Right
            # Player 2
            pygame.K_KP5: 'A',         # A
            pygame.K_KP6: 'B',         # B
            pygame.K_KP8: 'SELECT',    # Select
            pygame.K_KP9: 'START',     # Start
            pygame.K_UP: 'UP',         # Up
            pygame.K_DOWN: 'DOWN',     # Down
            pygame.K_LEFT: 'LEFT',     # Left
            pygame.K_RIGHT: 'RIGHT'    # Right
        }
    
    def update_from_pygame_events(self, events: List):
        """Process pygame events to update controller states"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in self.keyboard_mapping:
                    button = self.keyboard_mapping[event.key]
                    if button in ['A', 'B', 'SELECT', 'START', 'UP', 'DOWN', 'LEFT', 'RIGHT']:
                        # This is for controller 1 - in a real implementation
                        # we might want to distinguish between controllers
                        self.controller1.set_key_state(button, True)
            elif event.type == pygame.KEYUP:
                if event.key in self.keyboard_mapping:
                    button = self.keyboard_mapping[event.key]
                    if button in ['A', 'B', 'SELECT', 'START', 'UP', 'DOWN', 'LEFT', 'RIGHT']:
                        self.controller1.set_key_state(button, False)
    
    def update_controller_states(self):
        """Update controller states based on current keyboard state"""
        keys = pygame.key.get_pressed()
        
        # Update player 1 controls
        self.controller1.set_key_state('A', keys[pygame.K_j])
        self.controller1.set_key_state('B', keys[pygame.K_k])
        self.controller1.set_key_state('SELECT', keys[pygame.K_RSHIFT])
        self.controller1.set_key_state('START', keys[pygame.K_RETURN])
        self.controller1.set_key_state('UP', keys[pygame.K_w])
        self.controller1.set_key_state('DOWN', keys[pygame.K_s])
        self.controller1.set_key_state('LEFT', keys[pygame.K_a])
        self.controller1.set_key_state('RIGHT', keys[pygame.K_d])
        
        # Update player 2 controls
        self.controller2.set_key_state('A', keys[pygame.K_KP5])
        self.controller2.set_key_state('B', keys[pygame.K_KP6])
        self.controller2.set_key_state('SELECT', keys[pygame.K_KP8])
        self.controller2.set_key_state('START', keys[pygame.K_KP9])
        self.controller2.set_key_state('UP', keys[pygame.K_UP])
        self.controller2.set_key_state('DOWN', keys[pygame.K_DOWN])
        self.controller2.set_key_state('LEFT', keys[pygame.K_LEFT])
        self.controller2.set_key_state('RIGHT', keys[pygame.K_RIGHT])
    
    def set_controller_keys(self, p1_keys: List, p2_keys: List):
        """Set custom key mappings for controllers"""
        # This would take pygame key constants and map them to controller buttons
        # Implementation would depend on how we receive the key mappings
        pass
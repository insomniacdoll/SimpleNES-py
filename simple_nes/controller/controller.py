"""
Controller system for SimpleNES-py
Handles input from keyboard/gamepad
"""
import pygame
from typing import List
from ..util.config import Config

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
        if strobe:
            # When strobe is 1, latch current state
            self.state = 0
            shift = 0
            for button in ['A', 'B', 'SELECT', 'START', 'UP', 'DOWN', 'LEFT', 'RIGHT']:
                if self.buttons[button]:
                    self.state |= (1 << shift)
                shift += 1
        self.strobe = strobe
    
    def get_state_bit(self) -> int:
        """Get the current state bit and shift the register"""
        if self.strobe:
            # When strobe is 1, return A button state
            ret = 1 if self.buttons['A'] else 0
        else:
            ret = self.state & 1
            self.state >>= 1
        return ret | 0x40

def get_pygame_key_from_string(key_str: str):
    """Convert string representation of key to pygame key constant"""
    # Remove 'K_' prefix if present
    if key_str.startswith('K_'):
        key_str = key_str[2:]
    
    # Get the pygame key constant
    try:
        return getattr(pygame, f'K_{key_str}')
    except AttributeError:
        # If key is not found, return a default key
        print(f"Warning: Key '{key_str}' not found, using default")
        return getattr(pygame, 'K_UNKNOWN')

class ControllerManager:
    def __init__(self, config_path: str = None):
        self.controller1 = Controller()
        self.controller2 = Controller()
        self.config = Config(config_path)
        self.keyboard_mapping = self._load_keyboard_mapping()
    
    def _load_keyboard_mapping(self):
        """Load keyboard mappings from configuration"""
        controller_config = self.config.get_controller_config()
        mapping = {}
        
        # Player 1 mappings
        p1_config = controller_config.get('player1', {})
        for key_str, button in p1_config.items():
            pygame_key = get_pygame_key_from_string(button)
            if pygame_key != pygame.K_UNKNOWN:
                mapping[pygame_key] = key_str
        
        # Player 2 mappings
        p2_config = controller_config.get('player2', {})
        for key_str, button in p2_config.items():
            pygame_key = get_pygame_key_from_string(button)
            if pygame_key != pygame.K_UNKNOWN:
                mapping[pygame_key] = key_str
        
        return mapping
    
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
        
        # Load key mappings from config for player 1
        p1_config = self.config.get_controller_config().get('player1', {})
        self.controller1.set_key_state('A', keys[get_pygame_key_from_string(p1_config.get('A', 'K_j'))])
        self.controller1.set_key_state('B', keys[get_pygame_key_from_string(p1_config.get('B', 'K_k'))])
        self.controller1.set_key_state('SELECT', keys[get_pygame_key_from_string(p1_config.get('SELECT', 'K_RSHIFT'))])
        self.controller1.set_key_state('START', keys[get_pygame_key_from_string(p1_config.get('START', 'K_RETURN'))])
        self.controller1.set_key_state('UP', keys[get_pygame_key_from_string(p1_config.get('UP', 'K_w'))])
        self.controller1.set_key_state('DOWN', keys[get_pygame_key_from_string(p1_config.get('DOWN', 'K_s'))])
        self.controller1.set_key_state('LEFT', keys[get_pygame_key_from_string(p1_config.get('LEFT', 'K_a'))])
        self.controller1.set_key_state('RIGHT', keys[get_pygame_key_from_string(p1_config.get('RIGHT', 'K_d'))])
        
        # Load key mappings from config for player 2
        p2_config = self.config.get_controller_config().get('player2', {})
        self.controller2.set_key_state('A', keys[get_pygame_key_from_string(p2_config.get('A', 'K_KP5'))])
        self.controller2.set_key_state('B', keys[get_pygame_key_from_string(p2_config.get('B', 'K_KP6'))])
        self.controller2.set_key_state('SELECT', keys[get_pygame_key_from_string(p2_config.get('SELECT', 'K_KP8'))])
        self.controller2.set_key_state('START', keys[get_pygame_key_from_string(p2_config.get('START', 'K_KP9'))])
        self.controller2.set_key_state('UP', keys[get_pygame_key_from_string(p2_config.get('UP', 'K_UP'))])
        self.controller2.set_key_state('DOWN', keys[get_pygame_key_from_string(p2_config.get('DOWN', 'K_DOWN'))])
        self.controller2.set_key_state('LEFT', keys[get_pygame_key_from_string(p2_config.get('LEFT', 'K_LEFT'))])
        self.controller2.set_key_state('RIGHT', keys[get_pygame_key_from_string(p2_config.get('RIGHT', 'K_RIGHT'))])
    
    def set_controller_keys(self, p1_keys: dict, p2_keys: dict):
        """Set custom key mappings for controllers"""
        controller_config = self.config.get_controller_config()
        
        # Update player 1 keys
        if p1_keys:
            for button, key in p1_keys.items():
                if button in controller_config['player1']:
                    controller_config['player1'][button] = key
        
        # Update player 2 keys
        if p2_keys:
            for button, key in p2_keys.items():
                if button in controller_config['player2']:
                    controller_config['player2'][button] = key
        
        # Update the keyboard mapping
        self.keyboard_mapping = self._load_keyboard_mapping()
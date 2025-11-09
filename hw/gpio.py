# For GPIO access
from machine import Pin
# For time-based debouncing
import time

# Constants
DEBOUNCE_TIME = 20   # Debounce time in milliseconds


class Player:
    """Represents a player with button, LED, and state tracking"""
    
    def __init__(self, name, btn_pin, led_pin):
        self.name = name
        self.btn = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self.led = Pin(led_pin, Pin.OUT, None)
        self.lockout = False
        self.last_interrupt_time = 0

class ControlButton:
    """Represents a control button with state tracking"""
    
    def __init__(self, name, pin):
        self.name = name
        self.btn = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.last_interrupt_time = 0


# Configuration for players
PLAYER_CONFIG = [
    {'name': 'player1', 'btn_pin': 0, 'led_pin': 13},
    {'name': 'player2', 'btn_pin': 1, 'led_pin': 14},
    {'name': 'player3', 'btn_pin': 2, 'led_pin': 15},
]

# Configuration for control buttons
CONTROL_BUTTONS = {
    'correct': 16,
    'incorrect': 4,
    'next_question': 5
}

# Initialize players
players = {
    config['name']: Player(config['name'], config['btn_pin'], config['led_pin'])
    for config in PLAYER_CONFIG
}

# Initialize control buttons
control_btns = {
    name: ControlButton(name, pin)
    for name, pin in CONTROL_BUTTONS.items()
}

# Store button press events
button_events = []

# Global lockout state - when True, all player buttons are disabled
global_lockout = False


# Factory function to create player button handlers
def create_player_handler(player: Player):
    """Creates an interrupt handler for a player button"""
    def handler(pin):
        global button_events, global_lockout
        # Check lockouts - don't process if locked out
        if global_lockout or player.lockout:
            return
        global_lockout = True
        player.lockout = True
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, player.last_interrupt_time) > DEBOUNCE_TIME:
            button_events.append(player.name)
            player.last_interrupt_time = current_time
            # Turn on LED for 5 seconds
            player.led.value(1)
    return handler


# Factory function to create control button handlers
def create_control_handler(control_btn, reset_global_lockout=True, reset_player_lockout=False):
    """Creates an interrupt handler for control buttons"""
    def handler(pin):
        global button_events, global_lockout
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, control_btn.last_interrupt_time) > DEBOUNCE_TIME:
            button_events.append(control_btn.name)
            control_btn.last_interrupt_time = current_time
            # Reset all player LEDs
            for player in players.values():
                player.led.value(0)
            # Reset global lockout if requested
            if reset_global_lockout:
                global_lockout = False
            # Reset all per-player lockouts if requested
            if reset_player_lockout:
                for player in players.values():
                    player.lockout = False
    return handler

# Configure interrupts for all buttons (trigger on rising edge)
# Set up player button interrupts
for player in players.values():
    handler = create_player_handler(player)
    player.btn.irq(trigger=Pin.IRQ_RISING, handler=handler)

# Set up control button interrupts
for btn in control_btns.values():
    reset_player = (btn.name == 'next_question')
    handler = create_control_handler(btn, reset_global_lockout=True, reset_player_lockout=reset_player)
    btn.btn.irq(trigger=Pin.IRQ_RISING, handler=handler)

# Get and clear button events
def get_button_events():
    """Returns list of buttons that were pressed and clears the event queue"""
    global button_events
    events = button_events.copy()
    button_events = []
    return events

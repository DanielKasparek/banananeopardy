# For GPIO access
from machine import Pin

# For time-based debouncing
import time

# Constants
DEBOUNCE_TIME: int = 500  # Debounce time in milliseconds


class Player:
    """Represents a player with button, LED, and state tracking"""

    def __init__(self, name: str, btn_pin: int, led_pin: int) -> None:
        self.name: str = name
        self.btn: Pin = Pin(btn_pin, Pin.IN, Pin.PULL_UP)
        self.led: Pin = Pin(led_pin, Pin.OUT, None)
        self.lockout: bool = False


class ControlButton:
    """Represents a control button with state tracking"""

    def __init__(self, name: str, pin: int) -> None:
        self.name: str = name
        self.btn: Pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.last_interrupt_time: int = 0


# Initialize players
players: dict[str, Player] = {
    "player1": Player("player1", btn_pin=0, led_pin=13),
    "player2": Player("player2", btn_pin=1, led_pin=14),
    "player3": Player("player3", btn_pin=2, led_pin=15),
}

# Initialize control buttons
control_btns: dict[str, ControlButton] = {
    "correct": ControlButton("correct", pin=16),
    "incorrect": ControlButton("incorrect", pin=4),
    "next_question": ControlButton("next_question", pin=5),
}

# Store button press events
button_events: list[str] = []

# Global lockout state - when True, all player buttons are disabled
global_lockout: bool = False


# Factory function to create player button handlers
def create_player_handler(player: Player):
    """Creates an interrupt handler for a player button"""

    def handler(pin: Pin) -> None:
        global button_events, global_lockout
        # Check lockouts - don't process if locked out
        if global_lockout or player.lockout:
            return
        global_lockout = True
        player.lockout = True
        button_events.append(player.name)
        # Turn on LED
        player.led.value(1)

    return handler


# Factory function to create control button handlers
def create_control_handler(
    control_btn: ControlButton,
    reset_global_lockout: bool = True,
    reset_player_lockout: bool = False,
):
    """Creates an interrupt handler for control buttons"""

    def handler(pin: Pin) -> None:
        global button_events, global_lockout
        current_time = time.ticks_ms()
        if (
            time.ticks_diff(current_time, control_btn.last_interrupt_time)
            > DEBOUNCE_TIME
        ):
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
    player.btn.irq(trigger=Pin.IRQ_FALLING, handler=handler)

# Set up control button interrupts (trigger on button press, not release)
for btn in control_btns.values():
    reset_player = btn.name == "next_question"
    handler = create_control_handler(
        btn, reset_global_lockout=True, reset_player_lockout=reset_player
    )
    btn.btn.irq(trigger=Pin.IRQ_FALLING, handler=handler)


# Get and clear button events
def get_button_events() -> list[str]:
    """Returns list of buttons that were pressed and clears the event queue"""
    global button_events
    events: list[str] = button_events.copy()
    button_events = []
    return events

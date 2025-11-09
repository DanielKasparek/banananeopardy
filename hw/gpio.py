# For GPIO access
from machine import Pin
# For time-based debouncing
import time

# Initialize button inputs with pull-down resistors
# Assuming buttons connect GPIO to 3.3V when pressed
player1_btn = Pin(0, Pin.IN, Pin.PULL_UP)
player2_btn = Pin(1, Pin.IN, Pin.PULL_UP)
player3_btn = Pin(2, Pin.IN, Pin.PULL_UP)
correct_btn = Pin(16, Pin.IN, Pin.PULL_UP)
incorrect_btn = Pin(4, Pin.IN, Pin.PULL_UP)
next_question_btn = Pin(5, Pin.IN, Pin.PULL_UP)
player3_led = Pin(15, Pin.OUT, None)

# Store button press events
button_events = []

# Debounce time in milliseconds
DEBOUNCE_TIME = 50

# Last interrupt time for each button (for debouncing)
last_interrupt_time = {
    'player1': 0,
    'player2': 0,
    'player3': 0,
    'correct': 0,
    'incorrect': 0,
    'next_question': 0
}

# Interrupt handler for player 1 button
def player1_handler(pin):
    global button_events, last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['player1']) > DEBOUNCE_TIME:
        button_events.append('player1')
        last_interrupt_time['player1'] = current_time

# Interrupt handler for player 2 button
def player2_handler(pin):
    global button_events, last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['player2']) > DEBOUNCE_TIME:
        button_events.append('player2')
        last_interrupt_time['player2'] = current_time

# Interrupt handler for player 3 button
def player3_handler(pin):
    global button_events, last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['player3']) > DEBOUNCE_TIME:
        button_events.append('player3')
        last_interrupt_time['player3'] = current_time
        # Toggle player 3 LED
        player3_led.value(not player3_led.value())

# Interrupt handler for correct button
def correct_handler(pin):
    global button_events, last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['correct']) > DEBOUNCE_TIME:
        button_events.append('correct')
        last_interrupt_time['correct'] = current_time

# Interrupt handler for incorrect button
def incorrect_handler(pin):
    global button_events, last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['incorrect']) > DEBOUNCE_TIME:
        button_events.append('incorrect')
        last_interrupt_time['incorrect'] = current_time

# Interrupt handler for next question button
def next_question_handler(pin):
    global button_events, last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['next_question']) > DEBOUNCE_TIME:
        button_events.append('next_question')
        last_interrupt_time['next_question'] = current_time

# Configure interrupts for all buttons (trigger on rising edge)
player1_btn.irq(trigger=Pin.IRQ_RISING, handler=player1_handler)
player2_btn.irq(trigger=Pin.IRQ_RISING, handler=player2_handler)
player3_btn.irq(trigger=Pin.IRQ_RISING, handler=player3_handler)
correct_btn.irq(trigger=Pin.IRQ_RISING, handler=correct_handler)
incorrect_btn.irq(trigger=Pin.IRQ_RISING, handler=incorrect_handler)
next_question_btn.irq(trigger=Pin.IRQ_RISING, handler=next_question_handler)

# Get and clear button events
def get_button_events():
    """Returns list of buttons that were pressed and clears the event queue"""
    global button_events
    events = button_events.copy()
    button_events = []
    return events
 
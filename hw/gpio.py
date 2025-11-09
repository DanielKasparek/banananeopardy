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

# Initialize LED outputs for each player
player1_led = Pin(13, Pin.OUT, None)
player2_led = Pin(14, Pin.OUT, None)
player3_led = Pin(15, Pin.OUT, None)

# Store button press events
button_events = []

# Lockout state - when True, player buttons are disabled
lockout_active = False

# Per-player lockout - tracks which players have already pressed their button this question
player_lockout = {
    'player1': False,
    'player2': False,
    'player3': False
}

# LED timer tracking (stores the time when LED should turn off, 0 means off)
led_timers = {
    'player1': 0,
    'player2': 0,
    'player3': 0
}

# LED duration in milliseconds (5 seconds)
LED_DURATION = 5000

# Debounce time in milliseconds
DEBOUNCE_TIME = 20

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
    global button_events, last_interrupt_time, led_timers, lockout_active, player_lockout
    # Check global lockout - don't process if locked out
    if lockout_active:
        return
    # Check per-player lockout - don't process if this player is locked out
    if player_lockout['player1']:
        return
    lockout_active = True
    player_lockout['player1'] = True
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['player1']) > DEBOUNCE_TIME:
        button_events.append('player1')
        last_interrupt_time['player1'] = current_time
        # Turn on LED for 5 seconds if not already on
        if led_timers['player1'] == 0:
            player1_led.value(1)
            led_timers['player1'] = time.ticks_add(current_time, LED_DURATION)

# Interrupt handler for player 2 button
def player2_handler(pin):
    global button_events, last_interrupt_time, led_timers, lockout_active, player_lockout
    # Check global lockout - don't process if locked out
    if lockout_active:
        return
    # Check per-player lockout - don't process if this player is locked out
    if player_lockout['player2']:
        return
    lockout_active = True
    player_lockout['player2'] = True
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['player2']) > DEBOUNCE_TIME:
        button_events.append('player2')
        last_interrupt_time['player2'] = current_time
        # Turn on LED for 5 seconds if not already on
        if led_timers['player2'] == 0:
            player2_led.value(1)
            led_timers['player2'] = time.ticks_add(current_time, LED_DURATION)

# Interrupt handler for player 3 button
def player3_handler(pin):
    global button_events, last_interrupt_time, led_timers, lockout_active, player_lockout
    # Check global lockout - don't process if locked out
    if lockout_active:
        return
    # Check per-player lockout - don't process if this player is locked out
    if player_lockout['player3']:
        return
    lockout_active = True
    player_lockout['player3'] = True
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['player3']) > DEBOUNCE_TIME:
        button_events.append('player3')
        last_interrupt_time['player3'] = current_time
        # Turn on LED for 5 seconds if not already on
        if led_timers['player3'] == 0:
            player3_led.value(1)
            led_timers['player3'] = time.ticks_add(current_time, LED_DURATION)

# Interrupt handler for correct button
def correct_handler(pin):
    global button_events, last_interrupt_time, lockout_active
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['correct']) > DEBOUNCE_TIME:
        button_events.append('correct')
        last_interrupt_time['correct'] = current_time
        # Reset lockout when correct is pressed
        lockout_active = False

# Interrupt handler for incorrect button
def incorrect_handler(pin):
    global button_events, last_interrupt_time, lockout_active
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['incorrect']) > DEBOUNCE_TIME:
        button_events.append('incorrect')
        last_interrupt_time['incorrect'] = current_time
        # Reset lockout when incorrect is pressed
        lockout_active = False

# Interrupt handler for next question button
def next_question_handler(pin):
    global button_events, last_interrupt_time, lockout_active, player_lockout
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time['next_question']) > DEBOUNCE_TIME:
        button_events.append('next_question')
        last_interrupt_time['next_question'] = current_time
        # Reset global lockout when next question is pressed
        lockout_active = False
        # Reset all per-player lockouts when next question is pressed
        player_lockout['player1'] = False
        player_lockout['player2'] = False
        player_lockout['player3'] = False

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

# Update LED states based on timers
def update_leds():
    """Check LED timers and turn off LEDs when their time expires"""
    global led_timers
    current_time = time.ticks_ms()
    
    # Check player 1 LED
    if led_timers['player1'] != 0 and time.ticks_diff(current_time, led_timers['player1']) >= 0:
        player1_led.value(0)
        led_timers['player1'] = 0
    
    # Check player 2 LED
    if led_timers['player2'] != 0 and time.ticks_diff(current_time, led_timers['player2']) >= 0:
        player2_led.value(0)
        led_timers['player2'] = 0
    
    # Check player 3 LED
    if led_timers['player3'] != 0 and time.ticks_diff(current_time, led_timers['player3']) >= 0:
        player3_led.value(0)
        led_timers['player3'] = 0
 
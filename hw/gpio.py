# For GPIO access
from machine import Pin
# For async sleep so GPIO is non-blocking
from uasyncio import sleep

# Initialize button inputs with pull-down resistors
# Assuming buttons connect GPIO to 3.3V when pressed
player1_btn = Pin(0, Pin.IN, Pin.PULL_DOWN)
player2_btn = Pin(1, Pin.IN, Pin.PULL_DOWN)
player3_btn = Pin(2, Pin.IN, Pin.PULL_DOWN)
correct_btn = Pin(3, Pin.IN, Pin.PULL_DOWN)
incorrect_btn = Pin(4, Pin.IN, Pin.PULL_DOWN)
next_question_btn = Pin(5, Pin.IN, Pin.PULL_DOWN)

# Store previous button states for edge detection
prev_states = {
    'player1': 0,
    'player2': 0,
    'player3': 0,
    'correct': 0,
    'incorrect': 0,
    'next_question': 0
}

# Get current button states
def get_button_states():
    """Returns a dictionary with current state of all buttons"""
    return {
        'player1': player1_btn.value(),
        'player2': player2_btn.value(),
        'player3': player3_btn.value(),
        'correct': correct_btn.value(),
        'incorrect': incorrect_btn.value(),
        'next_question': next_question_btn.value()
    }

# Check for button press events (rising edge)
def get_button_presses():
    """Returns a dictionary of buttons that were just pressed (rising edge)"""
    global prev_states
    current_states = get_button_states()
    presses = {}
    
    for button_name in current_states:
        # Detect rising edge (button just pressed)
        if current_states[button_name] == 1 and prev_states[button_name] == 0:
            presses[button_name] = True
        else:
            presses[button_name] = False
        
        # Update previous state
        prev_states[button_name] = current_states[button_name]
    
    return presses

# Async function to poll buttons
async def poll_buttons():
    """Continuously poll button states"""
    while True:
        presses = get_button_presses()
        print(presses)
        # Check if any button was pressed
        for button_name, pressed in presses.items():
            if pressed:
                print(f"{button_name} button pressed")
        
        await sleep(0.05)  # Poll every 50ms for responsive input
 
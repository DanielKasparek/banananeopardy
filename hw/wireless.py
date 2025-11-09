# Enable wireless support
from network import WLAN

# Enable wait timer
from time import sleep

# Get secrets
from secrets import SSID, PASS

# Create a wireless AP to allow devices to connect to


def connectWireless():
    # Set WLAN config
    wlan = WLAN(WLAN.IF_AP)
    wlan.config(essid=SSID, password=PASS)
    wlan.active(True)

    # Check connection
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        sleep(1)

    # If improper connection or never reached
    if wlan.status() != 3:
        raise RuntimeError("network connection failed")
    else:
        status = wlan.ifconfig()
        # Return IP
        return status[0]

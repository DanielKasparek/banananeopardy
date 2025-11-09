# Async code inspired by Digikey youtube video: https://youtu.be/5VLvmA__2v0 and post: https://www.digikey.com/en/maker/projects/getting-started-with-asyncio-in-micropython-raspberry-pi-pico/110b4243a2f544b6af60411a85f0437c
from uasyncio import sleep, run
import json

# Allow for connection to wireless
from wireless import connectWireless

# Allow for GPIO access
from gpio import get_button_events

import machine
import sys

# Original code for web socket server by Florin Dragan licensed under the MIT License: https://gitlab.com/florindragan/raspberry_pico_w_websocket/-/blob/main/LICENSE
# MIT License
#
# Copyright (c) 2023 Florin Dragan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from ws_connection import ClientClosedError
from ws_server import WebSocketServer, WebSocketClient


class clientHandle(WebSocketClient):
    def process(self, dataList):
        try:
            # Send button data to client
            self.connection.write(dataList)
        except ClientClosedError:
            self.connection.close()


class AppServer(WebSocketServer):
    # Sets html to load and max connections allowed
    def __init__(self):
        super().__init__("index.html", 10)

    # Creates a client on connection
    def _make_client(self, conn):
        return clientHandle(conn)

# Failsafe
# https://forums.raspberrypi.com/viewtopic.php?t=351934
enable_21 = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
if enable_21.value() == 1:
    print("enable-pin not connected to GND, exit")
    sys.exit()

# Connect to WiFi network
ip = connectWireless()

# Configure and start server
server = AppServer()
server.start()

# Main loop


async def main():
    # "Loop"
    while True:
        # Get button events from interrupt handlers
        button_events = get_button_events()

        # Send button press events to all connected clients
        if button_events:
            data = json.dumps({"buttons": button_events})
            server.process_all(data)
            print(f"Buttons pressed: {button_events}")


run(main())

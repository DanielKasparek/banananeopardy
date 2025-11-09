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

import os
import socket
import network
import time
import websocket_helper
from time import sleep
from ws_connection import WebSocketConnection, ClientClosedError

# Class definition of client? (Used to send data to client)


class WebSocketClient:
    def __init__(self, conn):
        self.connection = conn

    def process(self):
        pass

    def parse(self):
        pass


# Class definition of server?


class WebSocketServer:
    # Initialization of new server
    def __init__(self, page, max_connections=1):
        self._listen_s = None
        self._clients = []
        self._max_connections = max_connections
        self._page = page

    # Sets up the socket on the proper ip and port
    def _setup_conn(self, port, accept_handler):
        self._listen_s = socket.socket()
        self._listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ai = socket.getaddrinfo("0.0.0.0", port)
        addr = ai[0][4]

        self._listen_s.bind(addr)
        self._listen_s.listen(1)
        if accept_handler:
            self._listen_s.setsockopt(socket.SOL_SOCKET, 20, accept_handler)

    # Accepts client connections
    def _accept_conn(self, listen_sock):
        cl, remote_addr = listen_sock.accept()

        if len(self._clients) >= self._max_connections:
            # Maximum connections limit reached
            cl.setblocking(True)
            try:
                cl.sendall("HTTP/1.1 503 Too many connections\n\n")
                cl.sendall("\n")
                sleep(0.1)
            except:
                pass
            cl.close()
            return

        # Set a timeout to prevent hanging
        cl.settimeout(2.0)
        
        # Read and parse the HTTP request to determine type
        is_websocket = False
        request_path = '/'
        webkey = None
        
        try:
            clr = cl.makefile("rwb", 0)
            # Read request line
            request_line = clr.readline()
            if request_line:
                # Parse request path
                parts = request_line.decode('utf-8').split(' ')
                if len(parts) >= 2:
                    request_path = parts[1]
            
            # Read headers
            while True:
                line = clr.readline()
                if not line or line == b"\r\n":
                    break
                if b":" in line:
                    h, v = [x.strip() for x in line.split(b":", 1)]
                    if h.lower() == b"upgrade" and b"websocket" in v.lower():
                        is_websocket = True
                    if h == b"Sec-WebSocket-Key":
                        webkey = v
        except:
            # Error reading request, close connection
            try:
                cl.close()
            except:
                pass
            return

        # Handle based on request type
        if is_websocket and webkey:
            # WebSocket connection
            try:
                from ubinascii import b2a_base64
                from uhashlib import sha1
                
                d = sha1(webkey)
                d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
                respkey = d.digest()
                respkey = b2a_base64(respkey)[:-1]
                
                cl.send(b"HTTP/1.1 101 Switching Protocols\r\n")
                cl.send(b"Upgrade: websocket\r\n")
                cl.send(b"Connection: Upgrade\r\n")
                cl.send(b"Sec-WebSocket-Accept: ")
                cl.send(respkey)
                cl.send(b"\r\n\r\n")
                
                cl.settimeout(None)  # Remove timeout for websocket
                self._clients.append(
                    self._make_client(
                        WebSocketConnection(remote_addr, cl, self.remove_connection)
                    )
                )
            except:
                try:
                    cl.close()
                except:
                    pass
        else:
            # HTTP request - serve file
            try:
                self._serve_file_from_path(cl, request_path)
            except:
                pass
            try:
                cl.close()
            except:
                pass

    def _make_client(self, conn):
        return WebSocketClient(conn)



    # Get content type based on file extension
    def _get_content_type(self, filename):
        if filename.endswith('.html'):
            return 'text/html'
        elif filename.endswith('.css'):
            return 'text/css'
        elif filename.endswith('.js'):
            return 'application/javascript'
        elif filename.endswith('.json'):
            return 'application/json'
        elif filename.endswith('.png'):
            return 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return 'image/jpeg'
        elif filename.endswith('.gif'):
            return 'image/gif'
        elif filename.endswith('.ico'):
            return 'image/x-icon'
        elif filename.endswith('.svg'):
            return 'image/svg+xml'
        elif filename.endswith('.webmanifest'):
            return 'application/manifest+json'
        elif filename.endswith('.txt'):
            return 'text/plain'
        else:
            return 'application/octet-stream'

    # Serve file based on request path
    def _serve_file_from_path(self, sock, request_path):
        # Clean up path and default to index.html
        if request_path == '/' or request_path == '':
            request_path = '/index.html'
        
        # Remove leading slash and construct file path
        file_path = 'web' + request_path
        
        try:
            # Check if file exists
            os.stat(file_path)
            content_type = self._get_content_type(file_path)
            
            # Send HTTP headers
            sock.sendall(
                "HTTP/1.1 200 OK\nConnection: close\nServer: piMI\nContent-Type: {}\n".format(content_type)
            )
            length = os.stat(file_path)[6]
            sock.sendall("Content-Length: {}\n\n".format(length))
            
            # Determine if file should be read as binary or text
            is_binary = content_type.startswith('image/') or content_type == 'application/octet-stream'
            
            # Send file content
            if is_binary:
                with open(file_path, "rb") as f:
                    chunk_size = 512
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        sock.sendall(chunk)
            else:
                with open(file_path, "r") as f:
                    for line in f:
                        sock.sendall(line)
        except OSError:
            # File not found, send 404
            try:
                sock.sendall("HTTP/1.1 404 Not Found\nConnection: close\nServer: piMI\nContent-Type: text/html\n\n")
                sock.sendall("<html><body><h1>404 Not Found</h1><p>File not found: {}</p></body></html>".format(file_path))
            except:
                pass



    # Stop the server
    def stop(self):
        if self._listen_s:
            self._listen_s.close()
        self._listen_s = None
        for client in self._clients:
            client.connection.close()

    # Start the server up (Default port 80)
    def start(self, port=80):
        if self._listen_s:
            self.stop()
        self._setup_conn(port, self._accept_conn)

    # Run process on all connected clients
    def process_all(self, dataList):
        for client in self._clients:
            client.process(dataList)

    # Run parse on all connected clients
    def parse_all(self):
        for client in self._clients:
            client.parse()

    # Remove a specific client's connection
    def remove_connection(self, conn):
        for client in self._clients:
            if client.connection is conn:
                self._clients.remove(client)
                return

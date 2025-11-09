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
            cl.sendall("HTTP/1.1 503 Too many connections\n\n")
            cl.sendall("\n")
            # TODO: Make sure the data is sent before closing (Not biggest concern)
            sleep(0.1)
            cl.close()
            return

        # Read the request first
        try:
            cl.setblocking(False)
            request = cl.recv(1024).decode('utf-8')
            cl.setblocking(True)
        except:
            cl.close()
            return

        # Check if it's a WebSocket upgrade request
        if 'Upgrade: websocket' in request or 'upgrade: websocket' in request.lower():
            try:
                websocket_helper.server_handshake(cl)
                self._clients.append(
                    self._make_client(
                        WebSocketConnection(remote_addr, cl, self.remove_connection)
                    )
                )
            except:
                cl.close()
        else:
            # Regular HTTP request, serve webpage
            self._serve_http_request(cl, request)
            return

    def _make_client(self, conn):
        return WebSocketClient(conn)

    # Parse HTTP request and get the requested path
    def _parse_http_request(self, request):
        try:
            # Extract the path from the first line (e.g., "GET /path HTTP/1.1")
            lines = request.split('\r\n')
            if lines:
                parts = lines[0].split(' ')
                if len(parts) >= 2:
                    path = parts[1]
                    # Default to index.html for root path
                    if path == '/' or path == '':
                        path = '/index.html'
                    return path
        except:
            pass
        return '/index.html'

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

    # Serve HTTP request from web folder
    def _serve_http_request(self, sock, request):
        path = self._parse_http_request(request)
        # Remove leading slash and construct file path in web folder
        file_path = 'web' + path
        
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
        except OSError as e:
            # File not found or error reading file
            try:
                sock.sendall("HTTP/1.1 404 Not Found\nConnection: close\nServer: piMI\nContent-Type: text/html\n\n")
                sock.sendall("<html><body><h1>404 Not Found</h1><p>The requested file was not found.</p></body></html>")
            except:
                pass
        
        try:
            sock.close()
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

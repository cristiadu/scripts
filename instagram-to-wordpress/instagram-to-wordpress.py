#!/usr/bin/python3

import json
import http.server
import socketserver
import threading
import time
from typing import Tuple
from http import HTTPStatus


class SimpleHttpServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)

    @property
    def api_response(self):
        return json.dumps({"message": "Ok! Auth Code Retrieved."}).encode()

    def do_GET(self):
        if self.path.startswith('/'):
            OAuthServer.authorization_code = self.path
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(self.api_response))


class OAuthServer:
    authorization_code = ""
    PORT = 8000
    _my_server: SimpleHttpServer

    def start_oauth_server(self):
        # Create an object of the above class
        # Star the server
        print(f"Server started at {self.PORT}")
        authorization_code = ""
        self._my_server = socketserver.TCPServer(("0.0.0.0", self.PORT), SimpleHttpServer)
        self._my_server.serve_forever()
    
    def stop_oauth_server(self):
        print(f"Server shutdown requested on port {self.PORT}")
        self._my_server.shutdown()


if __name__ == "__main__":
    oauth_server = OAuthServer()
    serverThread = threading.Thread(target=oauth_server.start_oauth_server)
    serverThread.start()
    print("It started")
    while(OAuthServer.authorization_code == ""):
        print(OAuthServer.authorization_code)
        time.sleep(5)
    print(OAuthServer.authorization_code)
    oauth_server.stop_oauth_server()
    serverThread.join()

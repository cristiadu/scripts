#!/usr/bin/python3

import json
import http.server
import socketserver
import threading
import time
from typing import Tuple
from http import HTTPStatus
from urllib.parse import urlsplit, parse_qs


class SimpleHttpServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)

    @property
    def api_response(self):
        return json.dumps({"message": "OAuth Authorization code was successfully retrieved." if OAuthServer.authorization_code != "" else "Missing OAuth Authorization code from request!"}).encode()

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/':
            query_string = parse_qs(url.query)
            if 'authorization_code' in query_string:
                OAuthServer.authorization_code = query_string['authorization_code'][0]
        self.send_response(HTTPStatus.OK if OAuthServer.authorization_code != "" else HTTPStatus.BAD_REQUEST)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(self.api_response))


class OAuthServer:
    authorization_code = ""
    PORT = 8000
    _my_server: SimpleHttpServer

    def start_oauth_server(self):
        # Start the server
        authorization_code = ""
        tries = 0 # tries 5 times to start server before identifying as an error.
        server_started = False
        while server_started is False and tries < 5:
            try:
                self._my_server = socketserver.TCPServer(("0.0.0.0", self.PORT), SimpleHttpServer)
                server_started = True
                print(f"Server started at {self.PORT}")
                self._my_server.serve_forever()
            except Exception as err:
                tries += 1
                server_started = False
                if tries == 5:
                    print(f"Exception happened while starting server: {err}")
                    exit(1)
                else:
                    time.sleep(5) # waits 2 seconds before next try
    
    def stop_oauth_server(self):
        print(f"Server shutdown requested on port {self.PORT}")
        self._my_server.shutdown()


if __name__ == "__main__":
    oauth_server = OAuthServer()
    server_thread = threading.Thread(target=oauth_server.start_oauth_server)

    try:
        server_thread.start()
        while(OAuthServer.authorization_code == "" and server_thread.is_alive()):
            time.sleep(5)
        
        # It was stopped due to an error on the OAuthServer thread.
        if not server_thread.is_alive():
            server_thread.join()
            exit(1)

        print(f"Authorization Code retrieved is: {OAuthServer.authorization_code}")
    except KeyboardInterrupt:
        print("Execution of script interrupted by user")
    finally:
        oauth_server.stop_oauth_server()
        server_thread.join()

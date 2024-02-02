#!/usr/bin/python3

import json
import http.server
import os
import socketserver
import ssl
import threading
import time
import webbrowser
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
            if 'code' in query_string:
                OAuthServer.authorization_code = query_string['code'][0]
        self.send_response(HTTPStatus.OK if OAuthServer.authorization_code != "" else HTTPStatus.BAD_REQUEST)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(self.api_response))


class OAuthServer:
    authorization_code = ""
    PORT = 8000
    _my_server: SimpleHttpServer
    _server_started = False

    def start_oauth_server(self):
        # Start the server
        authorization_code = ""
        tries = 0 # tries 5 times to start server before identifying as an error.
        while not self._server_started and tries < 5:
            try:
                if not 'SSL_PASSWORD' in os.environ:
                    print(f"Missing SSL_PASSWORD set as environment variable.")
                    exit(1)

                socketserver.TCPServer.allow_reuse_address = True
                self._my_server = socketserver.TCPServer(("0.0.0.0", self.PORT), SimpleHttpServer)
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain("./cert.pem", "./key.pem", password=os.environ['SSL_PASSWORD'])
                self._my_server.socket = ssl_context.wrap_socket (self._my_server.socket, server_side=True)
                print(f"Server started at {self.PORT}")
                self._server_started = True
                self._my_server.serve_forever()
            except Exception as err:
                tries += 1
                self._server_started = False
                if tries == 5:
                    print(f"Exception happened while starting server: {err}")
                    exit(1)
                else:
                    time.sleep(2) # waits 2 seconds before next try
    
    def stop_oauth_server(self):
        if self._server_started:
            print(f"Server shutdown requested on port {self.PORT}")
            self._my_server.shutdown()


if __name__ == "__main__":
    # 1. Initial request needs to be opened in the browser so user accepts giving Instagram permissions.
    app_id = "688975250098546"
    redirect_url = "https://localhost:8000/"
    webbrowser.open(f'https://api.instagram.com/oauth/authorize?client_id={app_id}&redirect_uri={redirect_url}&scope=user_profile,user_media&response_type=code', new=2)

    # 2. Logic so OAuth authorization code is retrieved by temporary server created for this purpose.
    oauth_server = OAuthServer()
    server_thread = threading.Thread(target=oauth_server.start_oauth_server)
    try:
        server_thread.start()
        while(OAuthServer.authorization_code == ""):
            # It was stopped due to an error on the OAuthServer thread.
            if not server_thread.is_alive():
                print("Error happened while executing thread.")
                exit(1)
            else:
                time.sleep(5)

        print(f"Authorization Code retrieved is: {OAuthServer.authorization_code}")
    except KeyboardInterrupt:
        print("Execution of script interrupted by user")
    finally:
        oauth_server.stop_oauth_server()
        server_thread.join()

    # 3. Call to retrieve short lived access-token
        
    # 4. Call to retrieve long-lived access-token and save it as a file.

#!/usr/bin/python3


from datetime import datetime
import os
from dotenv import load_dotenv
import requests


class WordpressClient():
    _client_id: str
    _client_secret: str
    _username: str
    _application_password: str
    _site: str
    _access_token: str
    _expiration_date: float

    def __init__(self, client_id, client_secret, username, application_password, site):
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._application_password = application_password
        self._site = site
        self._authenticate_user()

    def _refresh_token_if_needed(self):
        now_timestamp = datetime.timestamp(datetime.now())
        if self._expiration_date <= now_timestamp:
            print('Access token will be renewed.')
            self._authenticate_user()

    def _authenticate_user(self):
        token_response = requests.post('https://public-api.wordpress.com/oauth2/token',
                                       {'client_id': self._client_id, 'client_secret': self._client_secret,
                                        'grant_type': 'password', 'username': self._username, 'password': self._application_password})
        token_json = token_response.json()
        required_keys = ['access_token', 'blog_id']
        if any(key not in token_json for key in required_keys):
            print(
                f'Missing one or more required keys ({required_keys}) from response of token request: {token_json}')
            exit(1)
        print(f'Wordpress Token: {token_json}')
        self._access_token = token_json['access_token']
        self._site_id = token_json['blog_id']

    def create_post(self, title, content):
        return


if __name__ == '__main__':
    load_dotenv()
    required_env_keys = ['WORDPRESS_CLIENT_ID', 'WORDPRESS_CLIENT_SECRET',
                         'WORDPRESS_USERNAME', 'WORDPRESS_APPLICATION_PASSWORD', 'WORDPRESS_SITE']
    if any(env_key not in os.environ for env_key in required_env_keys):
        print(
            f'Missing one of the environment variables required for wordpress authentication {required_env_keys}')
        exit(1)

    client = WordpressClient(os.environ['WORDPRESS_CLIENT_ID'], os.environ['WORDPRESS_CLIENT_SECRET'],
                             os.environ['WORDPRESS_USERNAME'], os.environ['WORDPRESS_APPLICATION_PASSWORD'], os.environ['WORDPRESS_SITE'])

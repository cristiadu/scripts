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

    def __init__(self, client_id, client_secret, username, application_password, site):
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._application_password = application_password
        self._site = site
        self._authenticate_user()

    @property
    def auth_header(self):
        return {'Authorization': f'Bearer {self._access_token}'}

    def _refresh_token(self):
        print('Access token will be renewed.')
        self._authenticate_user()

    def _authenticate_user(self):
        token_response = requests.post('https://public-api.wordpress.com/oauth2/token',
                                       {'client_id': self._client_id, 'client_secret': self._client_secret,
                                        'grant_type': 'password', 'username': self._username, 'password': self._application_password})
        token_json = token_response.json()
        required_keys = ['access_token']
        if any(key not in token_json for key in required_keys):
            print(
                f'Missing one or more required keys ({required_keys}) from response of token request: {token_json}')
            exit(1)
        print(f'Wordpress Token: {token_json}')
        self._access_token = token_json['access_token']

    def upload_post_media(self, file_path, caption, post_id = None):
        # TODO: Verify sizing is correct for images within the posts, verify if post reference needs to be updated.
        media_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/media',
                                       headers=self.auth_header,
                                       data={'date': datetime.now(), 'alt_text': caption, 'caption': caption, 'description': caption,
                                             'post': post_id if post_id else 0},
                                       files={'file': open(file_path, "rb"), 'caption': caption})
        media_json = media_response.json()
        print(f'Media Data: {media_json}')

    def create_post(self, title, content, categories = [], tags=[], author = None, post_medias_path = []):
        # {'date':'{current_timezone_date}', 'status':'publish', 'format': 'standard', 'title':'{title}', 'content':'{content}', 'author':'{author}', 'comment_status':'open', 'categories':'{categories}', 'tags':'{tags}'}
        # TODO: Create media_ids from post using "upload_post_media" before post.
        # TODO: author, category and tags need the ID and not the name as part of the request, we need to retrieve them first.
        # TODO: Discover how to reference uploaded media on the post itself, how to add into content.
        post_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/posts',
                                      headers=self.auth_header,
                                      data={'date': datetime.now(), 'status': 'publish', 'format': 'standard',
                                            'title': title, 'content': content, 'comment_status': 'open'})
        post_json = post_response.json()
        print(f'Post Data: {post_json}')


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
    
    client.create_post('My Title', 'My Content', ['test-post'], ['test-tag'])
    client.upload_post_media('test_img.jpg', 'My Caption')


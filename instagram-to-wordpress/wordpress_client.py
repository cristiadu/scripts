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

        if token_response.status_code != 200:
            print(f'Error while trying to authenticate [{token_response.url}]: {token_json}')
            exit(1)

        required_keys = ['access_token']
        if any(key not in token_json for key in required_keys):
            print(
                f'Missing one or more required keys ({required_keys}) from response of token request: {token_json}')
            exit(1)
        print(f'Wordpress Token: {token_json}')
        self._access_token = token_json['access_token']

    def upload_post_media(self, file_path, caption, alt_text, description, post_id = None, self_call = False):
        # TODO: Verify sizing is correct for images within the posts, verify if post reference needs to be updated.
        media_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/media',
                                       headers=self.auth_header,
                                       data={'date': datetime.now(), 'alt_text': alt_text, 'caption': caption, 'description': description,
                                             'post': post_id if post_id else 0},
                                       files={'file': open(file_path, "rb"), 'caption': caption})
        
        if media_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.upload_post_media(file_path, caption, alt_text, description, post_id, True)
        media_json = media_response.json()

        if media_response.status_code not in [200, 201]:
            print(f'Error while trying to upload media [{media_response.url}]: {media_json}')
            exit(1)

        print(f'Media Data: {media_json}')

    def create_post(self, title, content, categories = [], tags=[], author = None, post_medias_path = [], self_call =  False):
        # {'date':'{current_timezone_date}', 'status':'publish', 'format': 'standard', 'title':'{title}', 'content':'{content}', 'author':'{author}', 'comment_status':'open', 'categories':'{categories}', 'tags':'{tags}'}
        # TODO: author, category and tags need the ID and not the name as part of the request, we need to retrieve them first.
        # TODO: Discover how to reference uploaded media on the post itself, how to add into content.
        # TODO: Check which kind of formatting language can be used on posts (html, markdown, etc)
        post_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/posts',
                                      headers=self.auth_header,
                                      data={'date': datetime.now(), 'status': 'publish', 'format': 'standard',
                                            'title': title, 'content': content, 'comment_status': 'open'})
        
        if post_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.create_post(title, content, categories, tags, author, post_medias_path, True)
        post_json = post_response.json()

        if post_response.status_code not in [200, 201]:
            print(f'Error while trying to create post [{post_response.url}]: {post_json}')
            exit(1)

        print(f'Post Data: {post_json}')

        for media_path in post_medias_path:
            self.upload_post_media(media_path, f'Post {title} media {media_path}', f'Post {title} media {media_path}', f'Media uploaded for post titled: {title}')

    def get_author_id(self, author):
        # TODO: Given an author (email or username), get the user ID associated to it.
        return

    def get_category_id(self, category):
        # TODO: Given a category name (string), get the category ID associated to it.
        return
    
    def get_tag_id(self, tag):
        # TODO: Given a tag name (string), get the tag ID associated to it.
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
    
    client.create_post('My Title', 'My Content', post_medias_path=['test/test_img.jpg'])

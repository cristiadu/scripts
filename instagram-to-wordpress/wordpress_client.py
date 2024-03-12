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
        return media_json

    def create_post(self, title, content, categories = [], tags=[], date = datetime.now(), author = None, post_medias_path = [], self_call =  False):
        media_ids = []
        for media_path in post_medias_path:
            media_data = self.upload_post_media(media_path, f'{title}', f'{title}', f'Media uploaded for post titled: {title}')
            media_id = media_data['id']  # get the media ID from the response
            media_ids.append(media_id)

        # Create a gallery with the uploaded media IDs
        gallery_shortcode = f'[gallery ids="{",".join(map(str, media_ids))}"]'
        content = f'{gallery_shortcode}{content}'  # add the gallery to the post content
        post_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/posts',
                                      headers=self.auth_header,
                                      data={'date': date, 'status': 'publish', 'format': 'standard',
                                            'title': title, 'content': content, 'comment_status': 'open',
                                            'author': self.get_author_id(author) if author else None,
                                            'categories': ','.join([str(self.retrieve_or_create_category_id(category)) for category in categories]),
                                            'tags': ','.join([str(self.retrieve_or_create_tag_id(tag)) for tag in tags])})
        
        if post_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.create_post(title, content, categories, tags, author, post_medias_path, True)
        post_json = post_response.json()

        if post_response.status_code not in [200, 201]:
            print(f'Error while trying to create post [{post_response.url}]: {post_json}')
            exit(1)

        print(f'Post Data: {post_json}')

    def get_author_id(self, author, self_call = False):
        author_response = requests.get(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/users?search={author}',
                                    headers=self.auth_header)
        
        if author_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.get_author_id(author, True)
        author_json = author_response.json()

        if author_response.status_code != 200:
            print(f'Error while trying to retrieve author [{author_response.url}]: {author_json}')
            exit(1)
        
        if len(author_json) == 0:
            print(f'Could not find author matching string: {author_json}')
            exit(1)

        return author_json[0]['id']
    
    def retrieve_or_create_category_id(self, category, self_call = False):
        category_id = self.get_category_id(category)
        if category_id is not None:
            return category_id
        
        # New category, so create it.
        category_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/categories',
                                    headers=self.auth_header,
                                    data={'name': category})
        
        if category_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.get_category_id(category, True)
        category_json = category_response.json()

        if category_response.status_code not in [200, 201]:
            print(f'Error while trying to create category [{category_response.url}]: {category_json}')
            exit(1)

        print(f'Category Data: {category_json}')
        return category_json['id']

    def get_category_id(self, category, self_call = False):
        category_response = requests.get(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/categories?search={category}',
                                    headers=self.auth_header)
        
        if category_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.retrieve_or_create_category_id(category, True)
        category_json = category_response.json()

        if category_response.status_code != 200:
            print(f'Error while trying to retrieve category [{category_response.url}]: {category_json}')
            exit(1)

        return category_json[0]['id'] if len(category_json) != 0 else None
    
    def retrieve_or_create_tag_id(self, tag, self_call = False):
        tag_id = self.get_tag_id(tag)
        if tag_id is not None:
            return tag_id

        # New tag, so create it.
        tag_response = requests.post(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/tags',
                                    headers=self.auth_header,
                                    data={'name': tag})
        
        if tag_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.retrieve_or_create_tag_id(tag, True)
        tag_json = tag_response.json()

        if tag_response.status_code not in [200, 201]:
            print(f'Error while trying to create tag [{tag_response.url}]: {tag_json}')
            exit(1)

        print(f'Tag Data: {tag_json}')
        return tag_json['id']

    def get_tag_id(self, tag, self_call = False):
        tag_response = requests.get(f'https://public-api.wordpress.com/wp/v2/sites/{self._site}/tags?search={tag}',
                                    headers=self.auth_header)
        
        if tag_response.status_code == 401 and not self_call:
            self._refresh_token()
            self.get_tag_id(tag, True)
        tag_json = tag_response.json()

        if tag_response.status_code != 200:
            print(f'Error while trying to retrieve tag [{tag_response.url}]: {tag_json}')
            exit(1)

        return tag_json[0]['id'] if len(tag_json) != 0 else None


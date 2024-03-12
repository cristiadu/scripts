#!/usr/bin/python3

import array
import io
import json
import requests
from datetime import datetime, timedelta


class InstagramMedia():
    def __init__(self, json_data):
        if 'id' not in json_data:
            raise RuntimeError('Missing ID on Instagram media json_data')

        self.id: str = json_data['id']
        self.media_type: str = json_data['media_type'] if 'media_type' in json_data else ''
        self.permalink: str = json_data['permalink'] if 'permalink' in json_data else ''
        self.media_url: str = json_data['media_url'] if 'media_url' in json_data else ''
        self.thumbnail_url: str = json_data['thumbnail_url'] if 'thumbnail_url' in json_data else ''
        self.caption: str = json_data['caption'] if 'caption' in json_data else ''
        self.username: str = json_data['username'] if 'username' in json_data else ''
        self.timestamp: str = json_data['timestamp'] if 'timestamp' in json_data else ''
        self.children: array = json_data['children'] if 'children' in json_data else []

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class InstagramUser():
    def __init__(self, json_data):
        if 'id' not in json_data:
            raise RuntimeError('Missing ID on Instagram user json_data')

        self.id: str = json_data['id']
        self.username: str = json_data['username'] if 'username' in json_data else ''
        self.account_type: str = json_data['account_type'] if 'account_type' in json_data else ''
        self.media_count: int = json_data['media_count'] if 'media_count' in json_data else -1

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class InstagramClient():
    last_post_fetch_date: float
    _user_id: str
    _access_token: str
    _expiration_date: float
    _config_file: str
    _API_VERSION = 'v19.0'
    _ALL_CHILDREN_MEDIA_FIELDS = 'id,media_type,permalink,media_url,thumbnail_url,username,timestamp'
    _ALL_MEDIA_FIELDS = f'{_ALL_CHILDREN_MEDIA_FIELDS},caption'
    _ALL_USER_FIELDS = 'id,account_type,username,media_count'
    _BASE_API_PATH = 'https://graph.instagram.com'

    def __init__(self, config_file):
        required_keys = ['user_id', 'access_token', 'expiration_date', 'last_post_fetch_date']
        f = open(config_file)
        config = json.load(f)
        f.close()
        if any(key not in config for key in required_keys):
            print(f'Missing one or more required keys ({required_keys}) from configuration file: {config}')
            exit(1)

        self._user_id = config['user_id']
        self._access_token = config['access_token']
        self._expiration_date = config['expiration_date']
        self.last_post_fetch_date = config['last_post_fetch_date'] if 'last_post_fetch_date' in config else 0
        self._config_file = config_file
        self._refresh_token_if_needed()

    def _refresh_token_if_needed(self):
        now_timestamp = datetime.timestamp(datetime.now())
        if self._expiration_date <= now_timestamp:
            print('Access token will be renewed.')
            self._refresh_token()

    def _refresh_token(self):
        # 4. Call to refresh long-lived access-token.
        long_lived_response = requests.get(
            f'{self._BASE_API_PATH}/refresh_access_token?grant_type=ig_refresh_token&access_token={self._access_token}')
        long_lived_json = long_lived_response.json()

        if long_lived_response.status_code != 200:
            print(f'Error while trying to refresh authentication token [{long_lived_response.url}]: {long_lived_json}')
            exit(1)

        required_keys = ['access_token', 'expires_in']
        if any(key not in long_lived_json for key in required_keys):
            print(f'Missing one or more required keys ({required_keys}) from response of long lived request: {long_lived_json}')
            exit(1)
        print(f'Long Lived Token: {long_lived_json}')
        self._access_token = long_lived_json['access_token']
        time_change = timedelta(seconds=long_lived_json['expires_in'])
        self._expiration_date = datetime.timestamp(datetime.now() + time_change)
        self._refresh_config_file()

    def _refresh_config_file(self):
        with io.open(self._config_file, 'w', encoding='utf-8') as f:
            json_data = json.dumps({'access_token': self._access_token,
                                    'user_id': self._user_id,
                                    'expiration_date': self._expiration_date,
                                    'last_post_fetch_date': self.last_post_fetch_date}, ensure_ascii=False, indent=2)
            f.write(json_data)
            print(f'JSON data saved to file: {json_data}')

    def set_fetch_date(self, fetch_date):
        self.last_post_fetch_date = fetch_date
        self._refresh_config_file()

    def get_user_details(self, fields=_ALL_USER_FIELDS):
        response = requests.get(
            f'{self._BASE_API_PATH}/{self._API_VERSION}/{self._user_id}?access_token={self._access_token}&fields={fields}')
        response_json = response.json()

        if response.status_code != 200:
            print(f'Error while trying to make user details request {response.url}: {response_json}')
            exit(1)

        return InstagramUser(response_json)

    def get_user_medias(self, since: int = None, until: int = None, fields=_ALL_MEDIA_FIELDS, with_children_data=False, exclude_media_ids=[]):
        print(f'Fetching media from profile since: {datetime.fromtimestamp(since)}')
        response = requests.get(
            f'{self._BASE_API_PATH}/{self._API_VERSION}/{self._user_id}/media?access_token={self._access_token}&fields={fields}&since={since if since else ""}&until={until if until else ""}')
        response_json = response.json()
        response_data = []

        if 'data' in response_json:
            response_data = response_json['data']

        while 'paging' in response_json and 'next' in response_json['paging']:
            response = requests.get(response_json['paging']['next'])
            response_json = response.json()

            if 'data' in response_json:
                response_data.extend(response_json['data'])

        if response.status_code != 200:
            print(f'Error while trying to make media request {response.url}: {response_json}')
            exit(1)

        # Remove filtered items.
        for index, media in enumerate(response_data):
            if media['id'] in exclude_media_ids or media['media_type'] == 'VIDEO':
                del response_data[index]

        if with_children_data:
            for media in response_data:
                # children are only available for "CAROUSEL_ALBUM" media types.
                if ('media_type', 'CAROUSEL_ALBUM') in media.items():
                    media['children'] = self.get_media_children(media['id'])

        return [InstagramMedia(media_json) for media_json in response_data]

    def get_media_children(self, media_id, fields=_ALL_CHILDREN_MEDIA_FIELDS):
        response = requests.get(
            f'{self._BASE_API_PATH}/{self._API_VERSION}/{media_id}/children?access_token={self._access_token}&fields={fields}')
        response_json = response.json()
        response_data = []

        if 'data' in response_json:
            response_data = response_json['data']

        for index, media in enumerate(response_data):
            if media['media_type'] == 'VIDEO':
                print(f'Video media type is not supported for children media: {media}')
                del response_data[index]

        while 'paging' in response_json and 'next' in response_json['paging']:
            response = requests.get(response_json['paging']['next'])
            response_json = response.json()
            response_data.extend(response_json['data'])

        if response.status_code != 200:
            print(f'Error while trying to make media children request [{response.url}]: {response_json}')
            exit(1)

        return [InstagramMedia(media_json) for media_json in response_data]
    
    def download_media(self, media, destination_path):
        file_path = None
        response = requests.get(media, stream=True)
        if response.status_code == 200:
            with open(f'{destination_path}', 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
                file_path = file.name
            print(f'Image downloaded to {destination_path}')

        return file_path

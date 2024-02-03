#!/usr/bin/python3

import io
import json
import requests
from datetime import datetime, timedelta


class InstagramClient():
    _user_id: str
    _access_token: str
    _expiration_date: float
    _config_file: str

    def __init__(self, config_file):
        required_keys = ['user_id', 'access_code', 'expiration_date']
        f = open(config_file)
        config = json.load(f)
        f.close()
        if any(key not in config for key in required_keys):
            print(f"Missing one or more required keys ({required_keys}) from configuration file: {config}")

        self._user_id = config['user_id']
        self._access_token = config['access_token']
        self._expiration_date = config['expiration_date']
        self._config_file = config_file
        self._refresh_token_if_needed()

    def _refresh_token_if_needed(self):
        now_timestamp = datetime.timestamp(datetime.now())
        if(self._expiration_date <= now_timestamp):
            print('Access token will be renewed.')
            self._refresh_token()


    def _refresh_token(self):
        # 4. Call to refresh long-lived access-token.
        long_lived_response = requests.get(
            f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={self._access_token}")
        long_lived_json = long_lived_response.json()
        required_keys = ['access_token', 'expires_in']
        if any(key not in long_lived_json for key in required_keys):
            print(f"Missing one or more required keys ({required_keys}) from response of long lived request: {long_lived_json}")
            exit(1)
        print(f"Long Lived Token: {long_lived_json}")
        self._access_token = long_lived_json['access_token']
        time_change = timedelta(seconds=long_lived_json['expires_in'])
        self._expiration_date = datetime.timestamp(datetime.now() + time_change)
        self._refresh_config_file()
        
    def _refresh_config_file(self):
        with io.open(self._config_file, 'w', encoding='utf-8') as f:
            json_data = json.dumps({'access_token': self._access_token,
                                    'user_id': self._user_id,
                                    'expiration_date': self._expiration_date}, ensure_ascii=False, indent=2)
            f.write(json_data)
            print(f"JSON data saved to file: {json_data}")


if __name__ == "__main__":
    instagram_client = InstagramClient('access_token.json')
#!/usr/bin/python3

import re
from instagram_client import InstagramClient
from wordpress_client import WordpressClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
required_env_keys = ['WORDPRESS_CLIENT_ID', 'WORDPRESS_CLIENT_SECRET',
                     'WORDPRESS_USERNAME', 'WORDPRESS_APPLICATION_PASSWORD', 'WORDPRESS_SITE']
if any(env_key not in os.environ for env_key in required_env_keys):
    print(f'Missing one of the environment variables required for authentication {required_env_keys}')
    exit(1)

# Initialize Instagram and WordPress clients
instagram_client = InstagramClient('instagram_config.json')
wordpress_client = WordpressClient(os.environ['WORDPRESS_CLIENT_ID'], os.environ['WORDPRESS_CLIENT_SECRET'],
                                   os.environ['WORDPRESS_USERNAME'], os.environ['WORDPRESS_APPLICATION_PASSWORD'], os.environ['WORDPRESS_SITE'])

# Fetch posts from Instagram
instagram_posts = instagram_client.get_user_medias(with_children_data=True)

# For each Instagram post, create a corresponding post on WordPress
for media in instagram_posts:
    title = media.timestamp.format('DD/MM/YYYY HH:mm') 
    content = media.caption  # Replace this with your own logic for generating the content
    hashtags = re.findall(r"#(\w+)", media.caption)
    media_paths = [instagram_client.download_media(media.media_url, f'./test/{media.media_url.split("/")[-1].split("?")[0]}')]

    if len(media.children) > 0:
        media_paths = [instagram_client.download_media(child_media.media_url, f'./test/{child_media.media_url.split("/")[-1].split("?")[0]}') for child_media in media.children]
    print(media_paths)
    # Use hashtags as both tags and categories
    wordpress_client.create_post(title, content, categories=hashtags, tags=hashtags, post_medias_path=media_paths)
    for media_path in media_paths:
        os.remove(media_path)
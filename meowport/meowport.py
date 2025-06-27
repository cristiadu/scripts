#!/usr/bin/env python3
"""
meowport.py
Script to download all the `:meow-` based emojis from the Slackmojis blob cats page and import them into a Discord server using the Discord API.
No external dependencies required (uses only Python standard library).
"""
import os
import re
import urllib.request
import html
import http.client
import json
import dotenv
import random
import base64
import time

SLACKMOJIS_URL = "https://slackmojis.com/categories/25-blob-cats-emojis"
DOWNLOAD_DIR = "./downloaded"

# Discord API endpoint for uploading emojis
DISCORD_API_URL = "https://discord.com/api/v10/guilds/{guild_id}/emojis"

# Helper: Download a URL to a file
def download_file(url, dest):
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
        out_file.write(response.read())

# Step 1: Scrape the Slackmojis page for :meow- emojis
def fetch_meow_emojis():
    req = urllib.request.Request(
        SLACKMOJIS_URL,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode('utf-8')
    # Find all emoji <li> blocks (single quotes, robust)
    emoji_blocks = re.findall(r"<li class='emoji[^']*'[^>]*>.*?</li>", html_content, re.DOTALL)
    print(f"DEBUG: Found {len(emoji_blocks)} <li class='emoji'> blocks.")
    emojis = []
    for block in emoji_blocks:
        # Find emoji name (any name containing 'meow', case-insensitive, allow whitespace/newlines)
        name_match = re.search(r"<div class=['\"]name['\"][^>]*>\s*:([^:]*meow[^:]*):\s*</div>", block, re.IGNORECASE | re.DOTALL)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        # Find image url (single or double quotes)
        img_match = re.search(r"<img[^>]+src=['\"]([^'\"]+)['\"]", block)
        if not img_match:
            continue
        img_url = html.unescape(img_match.group(1))
        emojis.append({'name': name, 'url': img_url})
    print(f"DEBUG: Found {len(emojis)} emojis with 'meow' in the name.")
    return emojis

# Step 2: Download all found emojis
def download_emojis(emojis):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
   # if len(emojis) > 50:
      #  emojis = random.sample(emojis, 50)
       # print(f"Selected 50 random emojis for download.")
    used_filenames = set()
    for emoji in emojis:
        # Remove query params from URL for extension
        url_path = emoji['url'].split('?')[0]
        ext = os.path.splitext(url_path)[1]
        base_filename = emoji['name'] + ext
        filename = base_filename
        # Ensure unique filename if duplicate
        count = 1
        while filename in used_filenames:
            filename = f"{emoji['name']}_{count}{ext}"
            count += 1
        used_filenames.add(filename)
        dest = os.path.join(DOWNLOAD_DIR, filename)
        print(f"Downloading {emoji['name']} -> {dest}")
        download_file(emoji['url'], dest)
        emoji['file_path'] = dest
    return emojis

# Step 3: Upload emojis to Discord
def upload_to_discord(emojis, guild_id, bot_token):
    for emoji in emojis:
        # Discord emoji name requirements: <=32 chars, alphanumeric/underscore only
        valid_name = re.sub(r'[^a-zA-Z0-9_]', '_', emoji['name'])[:32]
        if not os.path.exists(emoji['file_path']):
            print(f"Skipping {emoji['name']}: file not found.")
            continue
        file_size = os.path.getsize(emoji['file_path'])
        if file_size > 256 * 1024:
            print(f"Skipping {emoji['name']}: file too large ({file_size} bytes).")
            continue
        with open(emoji['file_path'], 'rb') as f:
            img_data = f.read()
        b64_img = "data:image/png;base64," + base64.b64encode(img_data).decode('utf-8')
        payload = json.dumps({
            "name": valid_name,
            "image": b64_img
        })
        attempt = 0
        while True:
            conn = http.client.HTTPSConnection("discord.com")
            endpoint = f"/api/v10/guilds/{guild_id}/emojis"
            headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json"
            }
            conn.request("POST", endpoint, body=payload, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read().decode('utf-8')
            if resp.status == 201:
                print(f"Uploaded {emoji['name']} to Discord.")
                conn.close()
                break
            elif resp.status == 429:
                try:
                    data = json.loads(resp_body)
                    retry_after = float(data.get("retry_after", 5))
                except Exception:
                    retry_after = 5
                print(f"Rate limited on {emoji['name']}, retrying after {retry_after} seconds...")
                conn.close()
                time.sleep(retry_after)
                attempt += 1
                if attempt > 2:
                    print(f"Failed to upload {emoji['name']} after multiple retries.")
                    break
                continue
            else:
                print(f"Failed to upload {emoji['name']}: {resp.status} {resp.reason} | {resp_body}")
                conn.close()
                break

if __name__ == "__main__":
    # Load .env if present
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    server_id = os.environ.get("DISCORD_SERVER_ID")
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")

    print("Fetching emojis with 'meow' in the name from Slackmojis...")
    emojis = fetch_meow_emojis()
    print(f"Found {len(emojis)} matching emojis.")
    emojis = download_emojis(emojis)
    print("\nTo upload to Discord, set your DISCORD_SERVER_ID and DISCORD_BOT_TOKEN in a .env file or as environment variables.")
    #if server_id and bot_token:
        #upload_to_discord(emojis, server_id, bot_token)
    #else:
    print("Skipping Discord upload (no credentials provided). Downloaded files are in:", DOWNLOAD_DIR)

# Meowport

Script to download all the `meow`-named emojis from the Slackmojis blob cats page and import them into a Discord server using the Discord API.

## Features
- Scrapes all emojis with 'meow' in the name from https://slackmojis.com/categories/25-blob-cats-emojis
- Downloads them to a local directory
- Optionally uploads them to a Discord server (requires bot token and server ID)

## Setup
1. Clone this repository or copy the `meowport` folder.
2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Copy `.env.template` to `.env` and fill in your Discord server (guild) ID and bot token:

```bash
cp .env.template .env
# Edit .env and set DISCORD_SERVER_ID and DISCORD_BOT_TOKEN
```

## Usage

```bash
python3 meowport.py
```

- Downloads all matching emojis to `meowport/downloaded_emojis/`.
- If credentials are set, uploads them to your Discord server.

## Environment Variables
- `DISCORD_SERVER_ID`: Your Discord server (guild) ID
- `DISCORD_BOT_TOKEN`: Your Discord bot token

You can set these in a `.env` file or as environment variables.

## Notes
- Only the Python standard library and `python-dotenv` are required.
- The script uses the Discord API to upload emojis. Your bot must have the `Manage Emojis and Stickers` permission in your server.

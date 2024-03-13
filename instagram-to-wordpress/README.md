# Instagram to WordPress Python Script

This project contains a Python script that automates the process of transferring posts from Instagram to WordPress.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them:

- Python 3.x
- pip

### Installing

1. Run the following:
```bash
git clone https://github.com/yourusername/instagram-to-wordpress.git
cd instagram-to-wordpress
pip install -r requirements.txt
```
2. Create `.env` file with following values:
```bash
# Temporary Server variables
SSL_PASSWORD="<SSL_PASSWORD>"

# Instagram API variables
INSTAGRAM_APP_ID="<INSTAGRAM_APP_ID>"
INSTAGRAM_APP_SECRET="<INSTAGRAM_APP_SECRET>"
INSTAGRAM_PASSWORD="<INSTAGRAM_PASSWORD>"

# Wordpress API variables
WORDPRESS_CLIENT_ID="<WORDPRESS_CLIENT_ID>"
WORDPRESS_CLIENT_SECRET="<WORDPRESS_CLIENT_SECRET>"
WORDPRESS_USERNAME="<WORDPRESS_USERNAME>"
WORDPRESS_APPLICATION_PASSWORD="<WORDPRESS_APPLICATION_PASSWORD>"
WORDPRESS_SITE="<SITE>.wordpress.com"
```
replacing the placeholders with your credentials.

3. Run `oauth_server_instagram.py` so instagram long lived authentication token can be retrieved.

** PS:** this setup is only needed once as a setup process.

```bash
chmod +x ./oauth_server_instagram.py
./oauth_server_instagram.py
```

this will also create the file `instagram_config.json` used later by the `InstagramClient` class.

## Running the Script

To run the script and create posts based on instagram photos, run the following:
```bash
cd instagram-to-wordpress
chmod +x ./instagram-to-wordpress.py
./instagram-to-wordpress.py
```
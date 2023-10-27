"""
Script created for fetching new jobs from LinkedIn, ignoring reposted ones.
For now it will only use LinkedIn's only indicators to say if it's reposted or not. They are:
    1. Job ID is the same as a previously fetched one (if acknowledged = true)
    2. Status is set as "reposted" by LinkedIn.
    3. I already applied to such job.
"""
import os
import sqlite3

import requests

DB_PATH = "./new_linkedin_jobs.db"
CLIENT_ID_ENV = "LINKEDIN_CLIENT_ID"
CLIENT_SECRET_ENV = "LINKEDIN_CLIENT_SECRET"


def initialize_db(conn: sqlite3.Connection):
    """
    Initialize database with apropriate tables.
    """
    cursor = conn.cursor()
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies
            ([id] INTEGER PRIMARY KEY, [name] TEXT, [blacklisted] BOOLEAN DEFAULT false, [tech] BOOLEAN DEFAULT false)
            ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs
            ([job_id] INTEGER PRIMARY KEY, [title] TEXT NOT NULL, [applied] BOOLEAN DEFAULT false, [reposted] BOOLEAN DEFAULT false, [company_id] INTEGER NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies (id) )
            ''')
    conn.commit()


def retrieve_linkedin_token():
    """
    Retrieve LinkedIn App OAuth2 Token for API access.
    """
    req = requests.post("https://www.linkedin.com/oauth/v2/accessToken", timeout=60, params={
        "grant_type": "client_credentials",
        "client_id": os.getenv(CLIENT_ID_ENV),
        "client_secret": os.getenv(CLIENT_SECRET_ENV)
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return req.json()


def fetch_jobs(access_token: str, query="Software"):
    """
    Retrieve, using an access_token provided, the job list from LinkedIn, given a query term.
    """
    req = requests.get("https://api.linkedin.com/v2/jobs", timeout=60,
                       headers={"Authorization": f"Bearer {access_token}"})
    return req.json()


if __name__ == '__main__':
    with sqlite3.connect("new_linkedin_jobs.db") as conn:
        initialize_db(conn)
        access_token = retrieve_linkedin_token()
        jobs = fetch_jobs(access_token)

        print(access_token)



# %%
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime
import csv
import random
import os
import pandas as pd
import json
import requests

# %%
account_mapping = pd.read_csv('account_id_mapping.csv')
#account_mapping.drop('Unnamed: 0', axis=1, inplace=True)
#account_mapping.rename(columns={"Instagram ID": "ID"}, inplace=True)
#account_mapping.to_csv('account_id_mapping.csv', index=False)
account_mapping

# %%
def get_following(account, id):
    base_url = f"https://www.instagram.com/api/v1/friendships/{id}/following/"
    save_file = f"following_jsons/{account}_{id}.json"

    headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cookie": (
        "datr=4UTGZz9QFOv83f-GWiRTQVK3; "
        "ig_did=EB28A296-4AEA-49C4-AECC-044931EBF73E; "
        "dpr=1.7999999523162842; "
        "mid=Z8ZE4QAEAAHJ6aXAdgHIT-817cjp; "
        "csrftoken=wkj97SKKL7Ib2y6qevgGoiHS6dgZusbb; "
        "ig_nrcb=1; "
        "wd=872x914; "
        "ds_user_id=72135168504; "
        "sessionid=72135168504%3AsKJbGxmuavkBP1%3A17%3AAYfvjUylrSjapk6oKZ-M3NfGiM-N34V4sVUbePtBfQ; "
        'rur="RVA\\05472135168504\\0541772607502:01f77562ece9dccb75763c2c3e845ebeccbdefbce597c8eeded7fba27b7f8f23ed8d45dd"'
    ),
    "priority": "u=1, i",
    "referer": "https://www.instagram.com/scmpnews/following/",
    "sec-ch-prefers-color-scheme": "dark",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-full-version-list": '"Not A(Brand";v="8.0.0.0", "Chromium";v="132.0.6834.160", "Google Chrome";v="132.0.6834.160"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": "macOS",
    "sec-ch-ua-platform-version": "14.6.1",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "x-asbd-id": "359341",
    "x-csrftoken": "wkj97SKKL7Ib2y6qevgGoiHS6dgZusbb",
    "x-ig-app-id": "936619743392459",
    "x-ig-www-claim": "hmac.AR1dPQMB70iMzNfm5xAsqGijl_HSgjaxPNOrRXWLyAzau1YO",
    "x-requested-with": "XMLHttpRequest",
    "x-web-session-id": "1dll6s:ka0kq9:62egfc"
}



    # Load previous progress if available
    if os.path.exists(save_file):
        with open(save_file, "r") as f:
            saved_data = json.load(f)
            all_following = saved_data.get("all_following", [])
            max_id = saved_data.get("max_id", None)
    else:
        all_following = []
        max_id = None

    print(f"{len(all_following)} accounts found for {account} so far...")

    # Retry parameters
    max_retries = 5
    retry_wait_time = 60  # Wait 1 minute if blocked

    while True:
        # Build the URL with pagination
        url = f"{base_url}?count=12"
        if max_id:
            url += f"&max_id={max_id}"
        
        retries = 0
        while retries < max_retries:
            response = requests.get(url, headers=headers)
            response.raise_for_status() 
            if response.status_code == 200:
                break  # Success, continue scraping
            
            elif response.status_code in [401, 400, 429]:  # Rate-limited or temporarily banned
                print(f"Rate limited! Waiting {retry_wait_time} seconds...")
                time.sleep(retry_wait_time)
                retries += 1
                retry_wait_time *= 2  # Exponential backoff
                continue  # Retry request
            
            else:
                print(f"Error: {response.status_code}, {response.text}")
                exit()

        try:
            # Parse JSON response
            data = response.json()
            print(data)
        except json.JSONDecodeError:
            print("Failed to parse JSON response.")
            exit()

        users = data.get("users", [])
        if not users:
            print("No more users found.")
            break  # Stop scraping if no users found

        all_following.extend(users)  # Add new users to list
        max_id = data.get("next_max_id")  # Update max_id for pagination

        # Save after each request
        with open(save_file, "w") as f:
            json.dump({"all_following": all_following, "max_id": max_id}, f, indent=4)
        print(f"[{account}] Saved progress: {len(all_following)} accounts.")

        # Stop if there are no more pages
        if not max_id:
            break

        # Delay to prevent bans
        time.sleep(random.uniform(1,2))

    # Final save
    with open(save_file, "w") as f:
        json.dump({"all_following": all_following, "max_id": None}, f, indent=4)

    print(f"Scraping complete for {account}! Total accounts retrieved: {len(all_following)}")

# %%
for index, row in account_mapping.iterrows():
    account = row['Account']
    id = row['ID']
    print(f"----- Processing {account} -----")

    save_file = f"following_jsons/{account}_{id}.json"
    
    # Check if the save file exists
    if os.path.exists(save_file):
        with open(save_file, "r") as f:
            saved_data = json.load(f)
            max_id = saved_data.get("max_id", None)

        # If max_id is None, scraping is complete; skip this account
        if max_id is None:
            print(f"Skipping {account} - Already fully scraped.")
            continue
        else:
            get_following(account, id)
    else:
        print(f"File does not exist for {account}, starting from 0.")
        get_following(account, id)
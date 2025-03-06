

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
# this is new version from chatgpt

import os
import json
import time
import random
import requests

def get_following(account, id):
    base_url = f"https://www.instagram.com/api/v1/friendships/{id}/following/"
    save_file = f"following_jsons/{account}_{id}.json"
    
    session = requests.Session()
    
    headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "datr=pLlfZ9oUt-gimOGZkhSv2che; ig_did=ADA02B91-358F-4A94-B771-BC1991C1508A; ig_nrcb=1; ps_l=1; ps_n=1; dpr=1.7999999523162842; mid=Z55x1gAEAAEeXrf1nto_oqWIJ5Ce; csrftoken=EGs4IcNIQxOP3CD5C2qv6f8JKeM34qWe; ds_user_id=69869436110; sessionid=69869436110%3A2YS7jv0uGNjhQu%3A14%3AAYc_kTy2nI9SKWwIeO4ptW0iYTrnk8Fjga9RC_EwLQ; wd=869x914; rur=\"NHA,69869436110,1772827539:01f76cb776d571d44058f1c903447eac07410be777f3f12b5f96e6c8597e3358fe4dd91b\"",
    "Priority": "u=1, i",
    "Referer": "https://www.instagram.com/gareth_tong/following/",
    "Sec-CH-Prefers-Color-Scheme": "light",
    "Sec-CH-UA": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
    "Sec-CH-UA-Full-Version-List": "\"Not A(Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"132.0.6834.160\", \"Google Chrome\";v=\"132.0.6834.160\"",
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Model": "\"\"",
    "Sec-CH-UA-Platform": "\"macOS\"",
    "Sec-CH-UA-Platform-Version": "\"14.6.1\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-ASBD-ID": "359341",
    "X-CSRFToken": "EGs4IcNIQxOP3CD5C2qv6f8JKeM34qWe",
    "X-IG-App-ID": "936619743392459",
    "X-IG-WWW-Claim": "hmac.AR3JRwqPGoKm62ZMR4_IuS8d3Ob0x4S0OUEY3EbNbQ5AHyJ4",
    "X-Requested-With": "XMLHttpRequest",
    "X-Web-Session-ID": "imd0rr:yduuzh:vnu3pk"
    }
    
    session.headers.update(headers)
    
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
    
    max_retries = 5
    retry_wait_time = 60
    
    while True:
        url = f"{base_url}?count=12"
        if max_id:
            url += f"&max_id={max_id}"
        
        retries = 0
        while retries < max_retries:
            response = session.get(url, allow_redirects=False)
            
            if response.status_code == 200:
                session.cookies.update(response.cookies)
                break
            elif response.status_code == 302:
                print("Breaking loop due to redirect.")
                return
            elif response.status_code in [401, 400, 429]:
                print(f"Rate limited! (Error {response.status_code}) Waiting {retry_wait_time} seconds...")
                time.sleep(retry_wait_time)
                retries += 1
                retry_wait_time *= 2
                continue
            else:
                print(f"Error: {response.status_code}, {response.text}")
                exit()
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Failed to parse JSON response")
            exit()
        
        users = data.get("users", [])
        if not users:
            print("No more users found.")
            break
        
        all_following.extend(users)
        max_id = data.get("next_max_id")
        
        with open(save_file, "w") as f:
            json.dump({"all_following": all_following, "max_id": max_id}, f, indent=4)
        print(f"[{account}] Saved progress: {len(all_following)} accounts.")
        
        if not max_id:
            break
        
        time.sleep(random.uniform(1, 2))
    
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
            result = get_following(account, id)
    else:
        print(f"File does not exist for {account}, starting from 0.")
        result = get_following(account, id)
    
    #if result == None:
        #print("Status Code 302 Redirect. Header no longer valid, breaking.")
        #break


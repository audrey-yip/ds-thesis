

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
new_accounts = []
with open("first_layer_following.json", 'r') as file:
    following_raw = json.load(file)
    
for account, followed_dict in following_raw.items():
    for followed_account_name, followed_id in followed_dict.items():
        new_accounts.append({
            "ID": followed_id,
            "Account": followed_account_name,
            "Layer": 2
        })

new_accounts

# %%
new_accounts_df = pd.DataFrame(new_accounts)
account_mapping_2 = pd.concat([account_mapping, new_accounts_df], ignore_index=True)


# %%
account_mapping_2.to_csv("account_id_mapping.csv")

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

# %%
# TRIED AUTOMATING KEEPING THE BROWSER OPEN, DID NOT WORK

# Log In to Instagram
def login_to_instagram(driver, username, password):
    driver.get('https://www.instagram.com/accounts/login/')
    time.sleep(3)
    
    # Locate the username and password fields and enter your credentials
    username_input = driver.find_element("name", "username")
    password_input = driver.find_element("name", "password")
    
    username_input.send_keys(username)
    password_input.send_keys(password)
    
    # Press the login button
    login_button = driver.find_element("xpath", '//*[@id="loginForm"]/div/div[3]/button')
    login_button.click()
    
    print("Successfully logged in!")
    time.sleep(5)

# Function to navigate to the reels page
def navigate_to_url(driver, account_name):
    try:
        account_url = f"https://www.instagram.com/{account_name}/"
        driver.get(account_url)
        print(f"Navigated to url: {account_url}")
        time.sleep(3)
    except Exception as e:
        print(f"Error navigating to {account_url}: {e}")

from seleniumwire import webdriver  # Use selenium-wire instead of selenium
import time

account_name = 'outcastsfromthe853'

# Set up the browser (Chrome)
options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # Run in headless mode (no GUI)
options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection

driver = webdriver.Chrome(options=options)  # Use selenium-wire WebDriver

login_to_instagram(driver, 'audreythesis2024', 'wellesley')

navigate_to_url(driver, account_name)
time.sleep(random.randint(5, 6))

following_element = driver.find_element(By.XPATH, f"//a[@href='/{account_name}/following/']")
following_element.click()
time.sleep(random.randint(5, 6))

# Intercept API requests
for request in driver.requests:
    if "api/v1/friendships" in request.url:  # Filter Instagram API calls
        headers = request.headers


def get_following_new(account, id, headers):
    base_url = f"https://www.instagram.com/api/v1/friendships/{id}/following/"
    save_file = f"following_jsons/{account}_{id}.json"
    
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

for index, row in account_mapping.iterrows():
    account = row['Account']
    id = row['Instagram ID']
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
            get_following_new(account, id, headers)
    else:
        print(f"File does not exist for {account}, starting from 0.")
        get_following_new(account, id, headers)

# %% [markdown]
# # Headers for Rotation

# %%
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-IG-App-ID": "936619743392459",
    "X-CSRFToken": "V9SRZkDu88oIJMlzkwD2f2",
    "X-ASBD-ID": "359341",
    "X-FB-Friendly-Name": "PolarisUserHoverCardContentV2Query",
    "X-FB-LSD": "LJQStINYW9rdQMHkZFDQos",
    "Cookie": (
        "csrftoken=V9SRZkDu88oIJMlzkwD2f2; "
        "sessionid=69869436110%3A3CMFMTtNI8r2xk%3A16%3AAYeRtOdOSUCI_laG7sdgfoWG_JOwPKpXHrX-h6MavQ; "
        "ds_user_id=69869436110; "
        "mid=Z8NvDQAEAAFd4Lxh9Vaf6-iE6Eec; "
        "ig_did=FB0B306D-C4C1-4AEF-B249-ADAD5A624A07; "
        "dpr=1.7999999523162842; "
        "rur=NHA\05469869436110\0541772400165:01f728f05227711aca9cf523d1145c8a50bdb9ab687a9f6a32f5b5eb36251138f325a2bc"
    )
}

headers_1 = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.160 Safari/537.36",
    "X-IG-App-ID": "936619743392459",
    "X-CSRFToken": "HXj2iA0sdKXRpezGyGXD9bjDo0ZkTF13",
    "X-ASBD-ID": "359341",
    "X-FB-Friendly-Name": "PolarisUserHoverCardContentV2Query",
    "X-FB-LSD": "LJQStINYW9rdQMHkZFDQos",
    "Cookie": (
        "csrftoken=HXj2iA0sdKXRpezGyGXD9bjDo0ZkTF13; "
        "sessionid=72126920994%3AWhTTezpKqHTHRN%3A21%3AAYfc_2SrurGbdkenAhHrEPUfJ8RsItKaryIiZDrVug; "
        "ds_user_id=72126920994; "
    ),
    "Referer": "https://www.instagram.com/scmpnews/following/?hl=en"
    }


headers_2 = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "X-IG-App-ID": "936619743392459",
    "X-CSRFToken": "wkj97SKKL7Ib2y6qevgGoiHS6dgZusbb",
    "Cookie": (
        "csrftoken=wkj97SKKL7Ib2y6qevgGoiHS6dgZusbb; "
        "sessionid=72135168504%3AsKJbGxmuavkBP1%3A17%3AAYcYOVjvFFZXFYzniwO2eCb33OY4HHfHI0WH_lwNAQ; "
        "ds_user_id=72135168504"
    ),
    "Referer": "https://www.instagram.com/scmpnews/following/?hl=en"
}




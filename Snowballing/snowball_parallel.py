"""
Code for Snowballing
Goal: Given list of accounts, go to their "following" and get that list of creators
author: Audrey Yip
"""

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

########################################
# Helper functions
########################################
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

# Function to navigate to the url page
def navigate_to_url(driver, url):
    try:
        driver.get(url)
        print(f"Navigated to url: {url}")
        time.sleep(3)
    except Exception as e:
        print(f"Error navigating to {url}: {e}")

# Helper function to read the account tracker
def read_account_tracker(filename):
    if os.path.exists(filename):
        with open(filename, mode="r") as file:
            reader = csv.DictReader(file)
            return {row["Account"]: {"Found Count": int(row["Found Count"]), "Actual Count": int(row["Actual Count"])} for row in reader}
    return {}

# Helper function to read the account tracker
def read_account_tracker(filename):
    if os.path.exists(filename):
        with open(filename, mode="r") as file:
            reader = csv.DictReader(file)
            return {row["Account"]: {"Found Count": int(row["Found Count"]), "Actual Count": int(row["Actual Count"])} for row in reader}
    return {}

# Helper function for saving info to the tracker
def save_account_tracker(tracker_file, tracker_data):
    # Initialize existing data dictionary
    existing_data = {}

    # Load existing data if the file exists
    if os.path.exists(tracker_file):
        with open(tracker_file, mode='r', encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                account = row["Account"]
                existing_data[account] = {
                    "Found Count": int(row["Found Count"]),
                    "Actual Count": int(row["Actual Count"]),
                    "Timestamp": row["Timestamp"],
                    "Comments": row.get("Comments", "")  # Ensure there is a default empty string for missing comments
                }

    # Update existing data with new tracker data
    for account, data in tracker_data.items():
        existing_data[account] = {
            "Found Count": data.get("Found Count", existing_data.get(account, {}).get("Found Count", 0)),
            "Actual Count": data.get("Actual Count", existing_data.get(account, {}).get("Actual Count", 0)),
            "Timestamp": data.get("Timestamp", existing_data.get(account, {}).get("Timestamp", "")),
            "Comments": data.get("Comments", existing_data.get(account, {}).get("Comments", ""))  # Include comments field
        }

    # Write the merged data back to the file
    with open(tracker_file, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ["Account", "Found Count", "Actual Count", "Timestamp", "Comments"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        for account, data in existing_data.items():
            writer.writerow({
                "Account": account,
                "Found Count": data["Found Count"],
                "Actual Count": data["Actual Count"],
                "Timestamp": data["Timestamp"],
                "Comments": data["Comments"]  # Include comments in the row
            })

# Helper function to load existing accounts for a user
def load_existing_accounts(account_name):
    directory = "snowball_following_csvs"
    filename = os.path.join(directory, f"{account_name}_following_accounts.csv")
    if os.path.exists(filename):
        with open(filename, mode="r") as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip the header
            return {row[0] for row in reader}
    return set()

# Helper function to save new accounts
def save_new_accounts(account_name, accounts):
    directory = "snowball_following_csvs"
    filename = os.path.join(directory, f"{account_name}_following_accounts.csv")
    os.makedirs(directory, exist_ok=True)
    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            writer.writerow(["Account Name", "Timestamp"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for account in accounts:
            writer.writerow([account, timestamp])

# Helper function to dismiss automated activity pop-up
def dismiss_ok_button(driver):
    """
    Attempts to locate and click the "OK" button to dismiss the 'Try Again Later' popup.

    Returns:
        bool: True if the button was successfully clicked, False otherwise.
    """
    xpath_1 = "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[2]/button[2]"
    class_name = "_a9-- _ap36 _a9_1"
    # Look for the "OK" button by its XPath
    print("Error trying to scroll... We may have been clocked as a bot.... Looking for OK button to close 'Try Again Later' Pop up")
    time.sleep(random.uniform(0,3))
    try:
        print("Looking for OK button to close 'Try Again Later' popup using XPath")
        ok_button = driver.find_element(By.XPATH, xpath_1)
        ok_button.click()  # Click the button if found
        print("OK button clicked to dismiss popup (found via XPath).")
        time.sleep(random.uniform(2,3))
        return True
    except Exception as xpath_error:
        print(f"Error while trying to click the OK button via XPath: {str(xpath_error)}")
        
    try:
        print("Looking for OK button to close 'Try Again Later' popup using class name")
        ok_button = driver.find_element(By.CLASS_NAME, class_name)
        ok_button.click()  # Click the button if found
        print("OK button clicked to dismiss popup (found via class name).")
        time.sleep(random.uniform(2,3))
        return True
    except Exception as class_error:
        print(f"Error while trying to click the OK button via class name: {str(class_error)}")
    
    time.sleep(random.uniform(2,3))
    
    return False

def check_account_private(driver):
    try:
        # Locate the "This account is private" element
        account_priv_element = driver.find_element(By.XPATH, "/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/div[1]/div/div[1]/div[2]/div/div/span")
        account_priv_message = account_priv_element.text

        # Check if the text matches the "This account is private" message
        if account_priv_message == "This account is private":
            print("This account is private. Skipping.")
            return True  # Indicate the account is private

    except Exception as e:
        # Log the error but proceed with the next steps
        print(f"Account should be public")

    return False  # Indicate the account is not private or an error occurred

# Helper function to read in list of account names from the csv
def read_account_names_from_csv(csv_file):
    account_names = []
    with open(csv_file, mode='r', encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            account_names.append(row['Account Name']) 
    return account_names

########################################
# Main Function
########################################
# Main Function
def snowballing(account_list):
    tracker_file = os.path.join("snowball_following_csvs", "_accounts_count_tracking_with_comments.csv")
    tracker_data = read_account_tracker(tracker_file)

    driver = webdriver.Chrome()
    try:
        login_to_instagram(driver, 'audreythesis2024', 'wellesley')
        time.sleep(random.randint(8, 10))
        
        # Shuffle the list 
        #random.shuffle(account_list)
        #print(f"Order of Shuffled Account list this run: {account_list}")

        for account_name in account_list:
            print(f"--- Now Running Code for {account_name} ---")
            # Check Instagram's count against csv
            if account_name in tracker_data:
                tracked_info = tracker_data[account_name]

                if "Comments" in tracked_info:
                    if tracked_info["Found Count"] == tracked_info["Actual Count"] or tracked_info["Comments"] == "Collection complete":
                        print(f"Skipping {account_name}, all {tracked_info["Found Count"]} accounts already found.")
                        continue
                    if tracked_info["Comments"] == "Account is Private":
                        print(f"Skipping {account_name}, This account is private.")
                        continue
                    if tracked_info["Comments"] == "Mismatch in number of accounts, but within [-5, 5]":
                        print(f"Skipping {account_name}, Mismatch in number of accounts, but within [-5, 5]")
                        continue
                else:
                    num_accounts_found_before = int(tracked_info["Found Count"])
                    print(f"Not all accounts followed by {account_name} found yet, {num_accounts_found_before} found previously based on tracker. Begin scraping.")
            else:
                print(f"{account_name} is not in the tracker.")

            
            # If some are already found, start with that set and navigate to Instagram
            following_accounts = load_existing_accounts(account_name)
            num_accounts_found_before = len(following_accounts)
            print(f"Now checking csv itself... Loaded {num_accounts_found_before} from csv")
            account_link = f"https://www.instagram.com/{account_name}/"

            # Navigate to the account's page
            try:
                navigate_to_url(driver, account_link)
                time.sleep(random.uniform(3,4))
            except Exception as e:
                print(f"Error navigating to {account_name}: {e}")
                continue  # Skip to the next account

            # Check if the account is private
            if check_account_private(driver):
                print(f"Skipping {account_name} as it is private.")
                # Update Tracker
                tracker_data[account_name]["Comments"] = "Account is Private"
                save_account_tracker(tracker_file, tracker_data)
                continue  # Skip to the next account
            
            try:
                # Find the "following" element to get actual number of followers
                following_element = driver.find_element(By.XPATH, f"//a[@href='/{account_name}/following/']")
                following_count_text = following_element.find_element(By.XPATH, "./*").text.replace(",", "")  # "./*" gets the first child
                actual_following_count = int(following_count_text)
                print(f"Actual number of accounts followed: {actual_following_count}")
                accounts_to_find = actual_following_count - num_accounts_found_before
                print(f"This means there are {accounts_to_find} new accounts to find.")

                if account_name not in tracker_data:
                    tracker_data[account_name] = {
                        "Found Count": num_accounts_found_before,  
                        "Actual Count": actual_following_count,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    # Save the tracker immediately after adding a new account
                    save_account_tracker(tracker_file, tracker_data)  
                    print(f"New entry added to tracker for {account_name} before scraping with Found Count = {num_accounts_found_before} and Actual Count = {actual_following_count}.")
            except Exception as e:
                print(f"Error finding following count for {account_name}: {e}")
                tracker_data[account_name] = {
                    "Found Count": 0,  
                    "Actual Count": 0,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "CommentS":"Follows 0 accounts"
                }
                # Save the tracker immediately after adding a new account
                save_account_tracker(tracker_file, tracker_data)  

                continue

            if accounts_to_find == 0:
                print(f"All acounts have been found for {account_name} as now. Exiting")
                continue
            elif -5 <= accounts_to_find <= 5:
                print(f"Skipping {account_name}, as the number of accounts to find ({accounts_to_find}) is within range [-5, 5]. Majority already found.")
                
                # Update Tracker
                tracker_data[account_name]["Comments"] = "Mismatch in number of accounts, but within [-5, 5]"
                save_account_tracker(tracker_file, tracker_data)
                continue
            
            # Click on the "following" button to see the list of accounts followed by this user
            try:
                following_element.click()
                time.sleep(random.uniform(6, 8))
            except Exception as e:
                print(f"Error clicking on following for {account_name}, could be following 0 accounts: {str(e)}")
                tracker_data[account_name]["Comments"] = "Following 0 accounts"
                save_account_tracker(tracker_file, tracker_data)
                continue
            
            # Extract the following list now
            max_retries = 6
            retry_count = 0
            previous_accounts_count = num_accounts_found_before # for scrolling mechanism
            accounts_from_this_run = 0
            
            # attempt scrolling for a bit if many accounts were already found
            if num_accounts_found_before > 0:
                its = int(num_accounts_found_before/12)
                print(f"Scrolling for {its} times, trying to bypass already found accounts")
                
                popup_dismissed = False  # Only used for initial scrolling

                for i in range(its):
                    print(f"Initial scrolling - {i + 1} of {its} scrolls ----")
                    try:
                        # Attempt to locate the popup and scroll
                        popup = driver.find_element(By.CSS_SELECTOR, ".xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja")
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup)
                        time.sleep(random.uniform(6, 8))
                    except Exception as e:
                        error_message = str(e)
                        time.sleep(random.randint(4, 5))

                        if not popup_dismissed and ".xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja" in error_message:
                            print("Error trying to scroll... We may have been clocked as a bot. Attempting to dismiss 'Try Again Later' popup.")
                            
                            # Attempt to dismiss the popup
                            if dismiss_ok_button(driver):
                                print("'Try Again Later' popup dismissed successfully.")
                                popup_dismissed = True  # Set the flag to True
                            else:
                                print("Failed to dismiss 'Try Again Later' popup.")


            print("Scraping Begins! Please don't break...")
            while retry_count < max_retries and len(following_accounts) < actual_following_count:
                try:
                    following_elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".x1dm5mii.x16mil14.xiojian.x1yutycm"))
                    )

                    for element in following_elements:
                        # Check if num accounts match -- break out of for loop if so
                        if len(following_accounts) == actual_following_count:
                            print(f"All {actual_following_count} acounts found! Exiting for loop for adding accounts")
                            break

                        try:
                            # Find the account name
                            child_element = element.find_element(By.CSS_SELECTOR, ".x1rg5ohu")
                            user_name = child_element.text

                            if user_name not in following_accounts:
                                following_accounts.add(user_name)
                                save_new_accounts(account_name, [user_name])
                                accounts_from_this_run +=1
                                print(f"Found new account: {user_name} --- {accounts_from_this_run} of {accounts_to_find} found on this run. --- Running Total = {len(following_accounts)} of {actual_following_count} actual accounts")
                                retry_count = 0
                                time.sleep(random.uniform(0,0.5))
                        except Exception as e:
                            print(f"Error extracting account name: {e}")

                    if len(following_accounts) == actual_following_count:
                        print(f"All {actual_following_count} acounts found! Exiting while loop for scrolling mechanism")
                        break
                    
                    # Scroll down to load more following accounts
                    try:
                        popup = driver.find_element(By.CSS_SELECTOR, ".xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja")
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup)
                        time.sleep(random.uniform(3, 4))
                    except Exception as e:
                        error_message = str(e)
                        
                        # Check if the error message matches the specific issue with the "Following" block
                        if "xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja" in error_message:
                            try:
                                dismiss_ok_button(driver)
                            except Exception as ok_error:
                                print(f"Error while trying to click the OK button: {ok_error}")
                        else:
                            # If it's a different exception, handle it normally
                            retry_count += 1
                            time.sleep(random.randint(4, 6) * retry_count)
                            print(f"Error during scrolling: {e} (Attempt {retry_count + 1}) of {max_retries}")
                            continue  # Skip to the next retry
                    else:
                        current_accounts_count = len(following_accounts)
                        if current_accounts_count == previous_accounts_count:
                            retry_count += 1
                            print(f"No new accounts loaded, retrying... (Attempt {retry_count + 1} of {max_retries})")
                            try:
                                print("Checking to see if there's a pop-up... we may have been clocked.")
                                dismiss_ok_button(driver)
                            except Exception as ok_error:
                                print(f"Error while trying to click the OK button: {str(ok_error)}")
                            time.sleep(random.randint(4, 6) * retry_count)
                            
                        else:
                            retry_count = 0
                        previous_accounts_count = current_accounts_count

                except Exception as e:
                    print(f"Error during scrolling overall: {e}")
                    retry_count += 1
            
            # Update tracker data
            tracker_data[account_name] = {
                "Found Count": len(following_accounts),
                "Actual Count": actual_following_count,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Comments": "Collection complete"
            }
            save_account_tracker(tracker_file, tracker_data)  # Save after each account
            print(f"Total accounts found followed by {account_name}: {len(following_accounts)} of {actual_following_count} actual accounts")
            print(f"Tracker saved for {account_name}.")
    finally:
        driver.quit()

if __name__ == "__main__":
    csv_file = '2nd_layer_accounts.csv'
    account_names = read_account_names_from_csv(csv_file)
    snowballing(account_names)
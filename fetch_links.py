import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def fetch_tiktok_video_links(username):
    driver_path = "/home/syx/Desktop/chromedriver"  # Replace with your actual path
    service = Service(driver_path)

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headlessly (without opening a window)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    url = f'https://www.tiktok.com/@{username}'
    driver.get(url)

    time.sleep(5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    video_urls = []
    videos = driver.find_elements(By.XPATH, '//a[contains(@href, "/video/")]')
    for video in videos:
        video_urls.append(f'https://www.tiktok.com{video.get_attribute("href")}')

    driver.quit()

    return video_urls

def load_existing_data(filename):
    try:
        with open(filename, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return {"users": {}}

def save_links_to_json(filename, data):
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

def update_video_links(data, username, new_links):
    # Get current links for the user, if any
    existing_links = data["users"].get(username, [])

    # Add new links, avoiding duplicates
    updated_links = list(set(existing_links + new_links))

    # Update the data dictionary
    data["users"][username] = updated_links

    return data

def read_usernames_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            usernames = file.read().splitlines()
        return usernames
    except FileNotFoundError:
        print(f"{file_path} not found.")
        return []

def main():
    filename = "tiktok_video_links.json"
    data = load_existing_data(filename)

    # Read usernames from usernames.txt
    usernames = read_usernames_from_file("usernames.txt")

    if not usernames:
        print("No usernames found. Please ensure the usernames.txt file is present and populated.")
        return

    while True:
        for username in usernames:
            print(f"Fetching video links for @{username}...")
            new_links = fetch_tiktok_video_links(username)
            if new_links:
                data = update_video_links(data, username, new_links)
                save_links_to_json(filename, data)
                print(f"Video links updated for @{username}")
            else:
                print(f"No new videos found for @{username}")
        
        print("Waiting for 30 minutes before fetching again...")
        time.sleep(1800)  # Wait for 30 minutes (1800 seconds)

if __name__ == "__main__":
    main()

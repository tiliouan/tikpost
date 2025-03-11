import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def tiktok_upload_post(driver, file_path, caption=""):
    wait = WebDriverWait(driver, 30)
    
    # Wait for the file input element to be present.
    try:
        print("Waiting for file input element...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
    except Exception as e:
        print("File input element not found:", e)
        return False
    
    # Send the absolute file path.
    try:
        print("Uploading file:", file_path)
        file_input.send_keys(file_path)
    except Exception as e:
        print("Error sending file path:", e)
        return False
    
    # Wait for the upload process to start/complete.
    print("Waiting for file upload to start...")
    time.sleep(20)  # Adjust if uploads are slow
    
    # Input the caption.
    try:
        print("Locating caption text area...")
        caption_input = driver.find_element(By.XPATH, "//textarea")
        caption_input.send_keys(caption)
        print("Caption entered:", caption)
    except Exception as e:
        print("Error entering caption:", e)
    
    # Wait 15 seconds before attempting to click the Post button.
    print("Waiting 15 seconds before clicking Post...")
    time.sleep(15)
    
    # Retry loop to click the Post button automatically.
    retry_timeout = 60  # seconds
    start_time = time.time()
    clicked = False
    while time.time() - start_time < retry_timeout:
        try:
            print("Attempting to locate and click the Post button...")
            post_button = driver.find_element(By.XPATH, "//button[@data-e2e='post_video_button']")
            driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
            time.sleep(1)
            post_button.click()
            print("Clicked Post button successfully.")
            clicked = True
            break
        except Exception as e:
            print("Error clicking Post button:", e)
            print("Retrying in 5 seconds...")
            time.sleep(5)
    
    if not clicked:
        print("Failed to click the Post button after retrying for {} seconds.".format(retry_timeout))
    else:
        # Allow time for the post process to complete.
        time.sleep(10)
    
    return clicked

def main():
    folder_path = "downloaded_tiktoks"
    if not os.path.isdir(folder_path):
        print(f"Folder '{folder_path}' does not exist. Exiting.")
        return
    
    # Setup Chrome options for a persistent session.
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=./chrome_profile")
    
    driver = webdriver.Chrome(options=options)
    
    print("Opening browser with persistent profile.")
    print("If you are not logged in to TikTok, please log in manually in the opened browser window.")
    print("Waiting 20 seconds for you to complete login (if needed)...")
    time.sleep(20)
    
    mp4_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp4')]
    if not mp4_files:
        print("No MP4 files found in the folder. Exiting.")
    else:
        # Store the main window handle.
        main_window = driver.current_window_handle
        total_files = len(mp4_files)
        for idx, file in enumerate(mp4_files):
            file_path = os.path.abspath(os.path.join(folder_path, file))
            caption = os.path.splitext(file)[0]
            print("Uploading file:", file, "with caption:", caption)
            
            # Open a new tab for the upload page.
            driver.execute_script("window.open('https://www.tiktok.com/upload?lang=en', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(10)  # Allow the upload page to load
            
            posted = tiktok_upload_post(driver, file_path, caption=caption)
            
            # Close the current tab and return to the main window.
            driver.close()
            driver.switch_to.window(main_window)
            
            # Wait 1 hour before processing the next video, if any remain.
            if idx < total_files - 1:
                print("Waiting 3 hour before uploading the next video...")
                time.sleep(10800)
    
    print("Finished uploading. Closing browser.")
    driver.quit()

if __name__ == "__main__":
    main()

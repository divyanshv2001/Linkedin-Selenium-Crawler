import time
import pickle
import sqlite3
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from openpyxl import Workbook
def view_data():
    # Connect to the SQLite database
    conn = sqlite3.connect("linkedin_profile_evaluation.db")  # Replace with your database file path
    cursor = conn.cursor()

    # Execute a SQL query to select all data from the evaluated_profiles table
    cursor.execute("SELECT * FROM evaluated_profiles")

    # Fetch all results
    rows = cursor.fetchall()

    # Print the results
    for row in rows:
        print(row)  # Each row is a tuple

    # Close the cursor and connection
    cursor.close()
    conn.close()
# Step 1: Setup database for tracking evaluated profiles
def setup_database():
    conn = sqlite3.connect("linkedin_profile_evaluation.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluated_profiles (
            profile_url TEXT PRIMARY KEY,
            name TEXT,
            score INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_profile_evaluation(profile_url, name, score, status):
    conn = sqlite3.connect("linkedin_profile_evaluation.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO evaluated_profiles (profile_url, name, score, status) VALUES (?, ?, ?, ?)",
                   (profile_url, name, score, status))
    conn.commit()
    conn.close()

def is_profile_evaluated(profile_url):
    conn = sqlite3.connect("linkedin_profile_evaluation.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM evaluated_profiles WHERE profile_url = ?", (profile_url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Step 2: Profile evaluation criteria
def evaluate_profile(driver):
    score = 0
    profile_details = {
        "profile_photo": False,
        "background_image": False,
        "about_section": False,
        "activity": False,
        "skills": False,
        "languages": False,
        "connections": False,
        "contact_info": False,
        "awards_projects": False,
        "volunteering": False,
        "recommendations": False,
        "is_hiring": False,
        "additional_buttons": False,
        "premium_member": False,
        "location": False,
        "headline": False,
        "full_name": False,
        "interests": False,
        "highlights": False,
        "featured": False,
        "recent_posts": False,
        "education": False,
        "endorsements": False,
    }

    def check_element(by, value, weight, detail_key):
        nonlocal score
        try:
            if driver.find_element(by, value):
                score += weight
                profile_details[detail_key] = True
        except:
            pass

    # Check for profile photo
    check_element(By.CLASS_NAME, "pv-top-card-profile-picture__image", 10, "profile_photo")

    # Check for background image
    check_element(By.CLASS_NAME, "profile-background-image__image-container", 5, "background_image")

    # Check for About section
    check_element(By.ID, "about", 10, "about_section")

    # Check for recent activity
    try:
        activity = driver.find_elements(By.CLASS_NAME, "pv-recent-activity-section")
        if activity:
            score += 10
            profile_details["activity"] = True
    except:
        pass

    # Check for skills
    check_element(By.ID, "skills", 10, "skills")

    # Check for languages
    check_element(By.CLASS_NAME, "pv-accomplishments-block__title", 5, "languages")

    # Check for connections count (at least 500+ considered a good network)
    try:
        connections_text = driver.find_element(By.CLASS_NAME, "pv-top-card--list-bullet").text
        connections_count = int(connections_text.split("+")[0].strip()) if "+" in connections_text else 0
        if connections_count >= 500:
            score += 10
            profile_details["connections"] = True
    except:
        pass

    # Check for recommendations
    check_element(By.CLASS_NAME, "recommendations-inlining", 10, "recommendations")

    # Check for featured section
    check_element(By.CLASS_NAME, "pv-profile-section--featured", 5, "featured")

    # Check for recent posts
    try:
        recent_posts = driver.find_elements(By.CLASS_NAME, "feed-shared-update-v2")
        if recent_posts:
            score += 5
            profile_details["recent_posts"] = True
    except:
        pass

    # Check for education
    check_element(By.ID, "education", 10, "education")

    # Check for endorsements
    try:
        endorsements = driver.find_elements(By.CLASS_NAME, "pv-skill-entity")
        if endorsements:
            score += 5
            profile_details["endorsements"] = True
    except:
        pass

    # Return the final score and detailed profile evaluation
    print(score)
    return score, profile_details

# Step 3: Login and cookie management
def linkedin_login(driver, username, password):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    print("Complete 2FA if prompted.")
    input("Press Enter after completing additional login steps...")
    pickle.dump(driver.get_cookies(), open("linkedin_cookies.pkl", "wb"))
    

def load_cookies(driver):
    try:
        cookies = pickle.load(open("linkedin_cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
    except FileNotFoundError:
        print("No saved cookies found. Login required.")

# Step 4: Evaluate connections and remove if inactive/fake
def evaluate_connections(driver):
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    time.sleep(5)
    profiles_data = []
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'mn-connection-card__link')]")))
    connections = driver.find_elements(By.XPATH, "//a[contains(@class, 'mn-connection-card__link')]")
    for connection in connections:
        profile_url = connection.get_attribute("href")
        name = connection.text
        if is_profile_evaluated(profile_url):
            print(f"Skipping already evaluated profile: {name} ({profile_url})")
            continue
        driver.execute_script("window.open(arguments[0], '_blank');", profile_url)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)

        try:
            score, details = evaluate_profile(driver)
            status = "Inactive/Fake" if score < 25 else "Active/Real"
            profiles_data.append({"profile_url": profile_url, "name": name, "score": score, "status": status})
            save_profile_evaluation(profile_url, name, score, status)
            if status == "Inactive/Fake":
                confirm = input(f"Are you sure you want to remove {name}? (yes/no): ")
                if confirm.lower() == "yes":
                    remove_connection(driver, profile_url)
                print(f"Removed connection with {name} ({profile_url})")

        except Exception as e:
            print(f"Error evaluating {name} ({profile_url}): {e}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(2)

    return profiles_data

def remove_connection(driver, profile_url):
    try:
        driver.get(profile_url)
        time.sleep(5)
        more_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[6]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[2]/button"))
        )
        more_button.click()
        time.sleep(2)
        remove_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//html/body/div[6]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[2]/div/div/ul/li[6]/div"))
        )
        remove_button.click()
        time.sleep(2)
        print(f"Successfully removed connection: {profile_url}")
        time.sleep(2)
    except Exception as e:
        print(f"Error while removing connection: {e}")

def save_to_excel(data, filename="linkedin_profile_evaluation.xlsx"):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Profile URL", "Name", "Score", "Status"])

    for item in data:
        sheet.append([item["profile_url"], item["name"], item["score"], item["status"]])

    workbook.save(filename)
    print(f"Data saved to {filename}")
def main():
    setup_database()
    driver = webdriver.Chrome()  # Use appropriate driver path if necessary
    username = "........."
    password = "........."

    try:
        linkedin_login(driver, username, password)
        profiles_data = evaluate_connections(driver)
        save_to_excel(profiles_data)
        # view_data()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
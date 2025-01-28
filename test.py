import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def linkedin_login(driver, username, password):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    print("Complete 2FA if prompted.")
    time.sleep(15)
    remove_connection(driver,"https://www.linkedin.com/in/shaik-munawar-0011softwareengineer/")

def remove_connection(driver, profile_url):
    try:
        # Navigate to the specific profile URL
        driver.get(profile_url)
        time.sleep(5)  # Allow the profile page to load completely

        # Click on the "More" button (the three dots menu)
        more_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'More actions')]"))
        )
        more_button.click()
        time.sleep(2)  # Allow the dropdown to open

        # Click on the "Remove connection" option
        remove_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Remove connection']/.."))
        )
        remove_button.click()
        time.sleep(2)  # Wait for the confirmation prompt

        # Confirm the removal
        confirm_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Remove')]"))
        )
        confirm_button.click()
        print(f"Successfully removed connection: {profile_url}")

        time.sleep(2)  # Allow LinkedIn to process the removal
    except Exception as e:
        print(f"Error while removing connection: {e}")
def main():
    driver = webdriver.Chrome()  # Use appropriate driver path if necessary
    username = "vishwakarmadivyansh25022001@gmail.com"  # Replace with your LinkedIn email
    password = "Shandilya@25022001"  # Replace with your LinkedIn password
    profile_url = "https://www.linkedin.com/in/shaik-munawar-0011softwareengineer/"  # Replace with the profile URL of the connection to remove

    try:
        linkedin_login(driver, username, password)
        # remove_connection(driver, profile_url)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
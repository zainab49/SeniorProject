import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# Setup Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://ucs.uob.edu.bh/index.php")  # Replace with the actual URL

time.sleep(30)  # Wait for the page to fully load

# Locate the results table
tables = driver.find_elements(By.ID, "resultsTable")

new_data = []
for table in tables:
    rows = table.find_elements(By.CLASS_NAME, "row")  # Get rows inside table
    for row in rows:
        new_data.append(row.text.strip())  # Extract text content

# Close browser
driver.quit()

# File path
json_file = "data.json"

# Check if file exists and load existing data
existing_data = []
if os.path.exists(json_file):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except json.JSONDecodeError:
        existing_data = []

# Combine existing data with new data
combined_data = existing_data + new_data  # This is the correct line that was causing the error

# Save to JSON only if data is available
if combined_data:
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=4, ensure_ascii=False)
    print(f"Data saved to {json_file}. Total entries: {len(combined_data)}")
else:
    print("No data extracted!")
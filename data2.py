import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://ucs.uob.edu.bh/index.php")  # Replace with the actual URL

time.sleep(20)  # Wait for the page to fully load

# Locate the results table
tables = driver.find_elements(By.ID, "resultsTable")

data = []
for table in tables:
    rows = table.find_elements(By.CLASS_NAME, "row")  # Get rows inside table
    for row in rows:
        data.append(row.text.strip())  # Extract text content

# Print data to debug
# print(data)

# Save to JSON only if data is available
if data:
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("Data saved to data.json")
else:
    print("No data extracted!")

# Close browser
driver.quit()

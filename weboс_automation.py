from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json

# --- Load extracted invoice (or hardcode for testing) ---
invoice_data = {
    "Invoice Number": "786/3147",
    "Invoice Date": "09/01/2025",
    "Item Description": "USED CLOTHING",
    "Quantity": 20185.07,
    "Unit Value": 0.42,
    "Total Value": 8477.7281,
    "Country of Origin": "United States",
    "Currency": "$",
    "HS Code": "6309.0000",
    "Incoterm": "FOB"
}

# --- Initialize Chrome WebDriver ---
driver = webdriver.Chrome()
driver.get("https://www.weboc.gov.pk")

# Let you log in manually
time.sleep(20)

# --- Fill form fields ---
driver.find_element(By.NAME, "invoiceNumber").send_keys(invoice_data["Invoice Number"])
driver.find_element(By.NAME, "invoiceDate").send_keys(invoice_data["Invoice Date"])
driver.find_element(By.NAME, "itemDescription").send_keys(invoice_data["Item Description"])
driver.find_element(By.NAME, "quantity").send_keys(str(invoice_data["Quantity"]))
driver.find_element(By.NAME, "unitPrice").send_keys(str(invoice_data["Unit Value"]))
driver.find_element(By.NAME, "totalValue").send_keys(str(invoice_data["Total Value"]))
driver.find_element(By.NAME, "originCountry").send_keys(invoice_data["Country of Origin"])
driver.find_element(By.NAME, "hsCode").send_keys(invoice_data["HS Code"])

# Optionally click submit
# driver.find_element(By.ID, "submitBtn").click()

time.sleep(5)
driver.quit()

#!/usr/bin/env python3
import os, sys, time
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEMO_URL = os.environ.get("DEMO_URL", "https://www.saucedemo.com/")
USER = os.environ.get("DEMO_USER", "standard_user")
PWD  = os.environ.get("DEMO_PASS", "secret_sauce")

CHROME_BIN    = os.environ.get("CHROME_BIN")       # نتوقع google-chrome هنا
CHROMEDRIVER  = os.environ.get("CHROMEDRIVER")     # نخليه فاضي عشان Selenium Manager يشتغل

USERNAME_ID   = "user-name"
PASSWORD_ID   = "password"
LOGIN_BTN_ID  = "login-button"
INVENTORY_ITEM = ".inventory_item"
ADD_TO_CART_BTN = "button.btn_primary.btn_small.btn_inventory"
CART_LINK     = ".shopping_cart_link"
CART_ITEM     = ".cart_item"
REMOVE_BTN    = "button.btn_secondary.btn_small.cart_button"
CART_BADGE    = ".shopping_cart_badge"

def _make_driver() -> webdriver.Chrome:
    print("Starting the browser...")
    opts = Options()
    if CHROME_BIN:
        print(f"Using Chrome binary at: {CHROME_BIN}")
        opts.binary_location = CHROME_BIN

    # headless متوافق وحدّ من مشاكل الذاكرة
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")

    # الأفضل: اترك Selenium Manager يختار الدرايفر (بدون Service)
    try:
        if not CHROMEDRIVER:
            print("Using Selenium Manager to resolve chromedriver ...")
            return webdriver.Chrome(options=opts)
    except Exception as e:
        print(f"Selenium Manager failed: {e}")

    # بديل: إن كان فيه CHROMEDRIVER محدد أو مسارات شائعة
    paths = [CHROMEDRIVER] if CHROMEDRIVER else []
    paths += ["/usr/bin/chromedriver","/usr/lib/chromium/chromedriver",
              "/snap/bin/chromium.chromedriver","/usr/lib/chromium-browser/chromedriver"]
    for p in paths:
        if p and os.path.exists(p):
            print(f"Using chromedriver at: {p}")
            return webdriver.Chrome(service=Service(p), options=opts)

    raise RuntimeError("No compatible Chrome/Chromedriver found.")

def _wait(driver, by, value, timeout=30):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

def _wait_all(driver, by, value, timeout=30):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))

def login_and_test_flow() -> None:
    driver = _make_driver()
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(5)
    added: List[str] = []
    removed: List[str] = []
    try:
        print(f"Navigating to: {DEMO_URL}")
        driver.get(DEMO_URL)

        _wait(driver, By.ID, USERNAME_ID).send_keys(USER)
        _wait(driver, By.ID, PASSWORD_ID).send_keys(PWD)
        _wait(driver, By.ID, LOGIN_BTN_ID).click()

        _wait_all(driver, By.CSS_SELECTOR, INVENTORY_ITEM)
        items = driver.find_elements(By.CSS_SELECTOR, INVENTORY_ITEM)[:6]

        for i, item in enumerate(items, start=1):
            title_el = item.find_element(By.CLASS_NAME, "inventory_item_name")
            name = title_el.text.strip()
            item.find_element(By.CSS_SELECTOR, ADD_TO_CART_BTN).click()
            added.append(name)
            print(f"[ADD] {i}. {name}")

        _wait(driver, By.CSS_SELECTOR, CART_LINK).click()
        cart_items = _wait_all(driver, By.CSS_SELECTOR, CART_ITEM)
        print(f"Cart has {len(cart_items)} items after adding.")

        for i, ci in enumerate(cart_items, start=1):
            name = ci.find_element(By.CLASS_NAME, "inventory_item_name").text.strip()
            ci.find_element(By.CSS_SELECTOR, REMOVE_BTN).click()
            removed.append(name)
            print(f"[REMOVE] {i}. {name}")

        time.sleep(1)
        empty = (len(driver.find_elements(By.CSS_SELECTOR, CART_BADGE)) == 0)
        result = "PASS" if empty and len(added) == len(removed) == 6 else "FAIL"

        print("\n===== SELENIUM RUN SUMMARY =====")
        print(f"USER: {USER}")
        print(f"ADDED  ({len(added)}): {added}")
        print(f"REMOVED({len(removed)}): {removed}")
        print(f"RESULT: {result}")
        print("================================\n")

        if result != "PASS":
            raise RuntimeError("Functional assertions failed.")
    finally:
        try: driver.quit()
        except Exception: pass

if __name__ == "__main__":
    try:
        login_and_test_flow()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

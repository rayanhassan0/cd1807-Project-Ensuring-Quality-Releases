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

# نلزم استخدام snap chromium + chromedriver
CHROME_BIN   = os.environ.get("CHROME_BIN", "/snap/bin/chromium")
CHROMEDRIVER = os.environ.get("CHROMEDRIVER", "/snap/bin/chromium.chromedriver")

USERNAME_ID   = "user-name"
PASSWORD_ID   = "password"
LOGIN_BTN_ID  = "login-button"
INVENTORY_ITEM = ".inventory_item"
ADD_TO_CART_BTN = "button.btn_primary.btn_small.btn_inventory"
CART_LINK     = ".shopping_cart_link"
CART_ITEM     = ".cart_item"
REMOVE_BTN    = "button.btn_secondary.btn_small.cart_button"
CART_BADGE    = ".shopping_cart_badge"

def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def _make_driver() -> webdriver.Chrome:
    log("Starting the browser...")
    opts = Options()
    opts.page_load_strategy = "eager"

    # إلزامياً استخدم باينري الـsnap
    if not os.path.exists(CHROME_BIN):
      raise RuntimeError(f"Chrome binary not found at {CHROME_BIN}")
    opts.binary_location = CHROME_BIN
    log(f"Using Chrome binary at: {CHROME_BIN}")

    # أعلام CI
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--remote-debugging-port=9222")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--user-data-dir=/tmp/chrome-profile")
    opts.add_argument("--enable-logging")
    opts.add_argument("--v=1")

    # الزم الدرايفر الخاص بالـsnap
    if not os.path.exists(CHROMEDRIVER):
      raise RuntimeError(f"Chromedriver not found at {CHROMEDRIVER}")
    log(f"Using chromedriver at: {CHROMEDRIVER}")
    service = Service(CHROMEDRIVER)

    return webdriver.Chrome(service=service, options=opts)

def _wait(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

def _wait_all(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))

def login_and_test_flow() -> None:
    driver = _make_driver()
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(3)

    added: List[str] = []
    removed: List[str] = []

    try:
        log(f"Navigating to: {DEMO_URL}")
        t0 = time.time()
        driver.get(DEMO_URL)
        log(f"Page requested (elapsed {time.time()-t0:.1f}s)")

        log("Filling login form...")
        _wait(driver, By.ID, USERNAME_ID, timeout=20).send_keys(USER)
        _wait(driver, By.ID, PASSWORD_ID, timeout=20).send_keys(PWD)
        _wait(driver, By.ID, LOGIN_BTN_ID, timeout=10).click()

        log("Waiting inventory list...")
        _wait_all(driver, By.CSS_SELECTOR, INVENTORY_ITEM, timeout=20)

        items = driver.find_elements(By.CSS_SELECTOR, INVENTORY_ITEM)[:6]
        for i, item in enumerate(items, start=1):
            title_el = item.find_element(By.CLASS_NAME, "inventory_item_name")
            name = title_el.text.strip()
            item.find_element(By.CSS_SELECTOR, ADD_TO_CART_BTN).click()
            added.append(name)
            log(f"[ADD] {i}. {name}")

        log("Opening cart...")
        _wait(driver, By.CSS_SELECTOR, CART_LINK, timeout=10).click()
        cart_items = _wait_all(driver, By.CSS_SELECTOR, CART_ITEM, timeout=15)
        log(f"Cart has {len(cart_items)} items after adding.")

        for i, ci in enumerate(cart_items, start=1):
            name = ci.find_element(By.CLASS_NAME, "inventory_item_name").text.strip()
            ci.find_element(By.CSS_SELECTOR, REMOVE_BTN).click()
            removed.append(name)
            log(f"[REMOVE] {i}. {name}")

        time.sleep(1)
        empty = (len(driver.find_elements(By.CSS_SELECTOR, CART_BADGE)) == 0)
        result = "PASS" if empty and len(added) == len(removed) == 6 else "FAIL"

        print("\n===== SELENIUM RUN SUMMARY =====", flush=True)
        print(f"USER: {USER}", flush=True)
        print(f"ADDED  ({len(added)}): {added}", flush=True)
        print(f"REMOVED({len(removed)}): {removed}", flush=True)
        print(f"RESULT: {result}", flush=True)
        print("================================\n", flush=True)

        if result != "PASS":
            raise RuntimeError("Functional assertions failed.")

    finally:
        try:
            log("Quitting browser...")
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        login_and_test_flow()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

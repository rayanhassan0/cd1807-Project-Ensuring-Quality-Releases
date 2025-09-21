#!/usr/bin/env python3
import os
import sys
import time
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# استخدم webdriver-manager كحل افتراضي لإحضار الدرايفر المتوافق
from webdriver_manager.chrome import ChromeDriverManager

DEMO_URL = os.environ.get("DEMO_URL", "https://www.saucedemo.com/")
USER = os.environ.get("DEMO_USER", "standard_user")
PWD = os.environ.get("DEMO_PASS", "secret_sauce")

# متصفح Chromium من apt (الأكثر ثباتًا على بيئة Azure VM/agent)
CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/chromium-browser")
CHROMEDRIVER = os.environ.get("CHROMEDRIVER")  # إن تم تمريره من الـ YAML

# عناصر CSS/IDs
USERNAME_ID = "user-name"
PASSWORD_ID = "password"
LOGIN_BTN_ID = "login-button"
INVENTORY_ITEM = ".inventory_item"
ADD_TO_CART_BTN = "button.btn_primary.btn_small.btn_inventory"
CART_LINK = ".shopping_cart_link"
CART_ITEM = ".cart_item"
REMOVE_BTN = "button.btn_secondary.btn_small.cart_button"
CART_BADGE = ".shopping_cart_badge"


def _build_options() -> Options:
    opts = Options()
    opts.binary_location = CHROME_BIN
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    return opts


def _make_driver() -> webdriver.Chrome:
    """يبني Chrome/Chromium بوضع headless مع حل تلقائي لمشكلة chromedriver."""
    print("Starting the browser...")
    print(f"Using Chrome binary at: {CHROME_BIN}")
    opts = _build_options()

    # 1) لو فيه CHROMEDRIVER ممرّر أو موجود على القرص، استخدمه
    if CHROMEDRIVER and os.path.exists(CHROMEDRIVER):
        print(f"Using chromedriver at (from env): {CHROMEDRIVER}")
        return webdriver.Chrome(service=Service(CHROMEDRIVER), options=opts)

    # 2) جرّب مسارات شائعة (apt/snap/etc) — فقط لو كانت موجودة فعلاً
    for p in ("/usr/bin/chromedriver",
              "/usr/lib/chromium/chromedriver",
              "/usr/lib/chromium-browser/chromedriver",
              "/snap/bin/chromium.chromedriver"):
        if os.path.exists(p):
            print(f"Found chromedriver at: {p}")
            try:
                return webdriver.Chrome(service=Service(p), options=opts)
            except Exception as e:
                print(f"Driver at {p} failed to start: {e}")

    # 3) استخدم webdriver-manager لتنزيل الدرايفر المطابق تلقائيًا
    try:
        print("Falling back to webdriver-manager to fetch a compatible driver...")
        driver_path = ChromeDriverManager().install()
        print(f"webdriver-manager installed chromedriver at: {driver_path}")
        return webdriver.Chrome(service=Service(driver_path), options=opts)
    except Exception as e:
        print(f"webdriver-manager failed: {e}")

    # 4) كحل أخير: دع Selenium Manager يحاول اختيار الدرايفر
    print("Final fallback: Selenium Manager (may be slower).")
    return webdriver.Chrome(options=opts)


def _wait(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def _wait_all(driver, by, value, timeout=20):
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
        badge = driver.find_elements(By.CSS_SELECTOR, CART_BADGE)
        empty = (len(badge) == 0)
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
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        login_and_test_flow()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

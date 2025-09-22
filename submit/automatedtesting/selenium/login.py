#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# webdriver-manager
from webdriver_manager.chrome import ChromeDriverManager

DEMO_URL = os.environ.get("DEMO_URL", "https://www.saucedemo.com/")
USER = os.environ.get("DEMO_USER", "standard_user")
PWD = os.environ.get("DEMO_PASS", "secret_sauce")

CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")

USERNAME_ID = "user-name"
PASSWORD_ID = "password"
LOGIN_BTN_ID = "login-button"
INVENTORY_ITEM = ".inventory_item"
ADD_TO_CART_BTN = "button.btn_primary.btn_small.btn_inventory"
CART_LINK = ".shopping_cart_link"
CART_ITEM = ".cart_item"
REMOVE_BTN = "button.btn_secondary.btn_small.cart_button"
CART_BADGE = ".shopping_cart_badge"


def _make_driver() -> webdriver.Chrome:
    print("=== Starting Selenium with timeout (4m) ===")
    print("Starting the browser...")
    print(f"Using Chrome binary at: {CHROME_BIN}")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--remote-debugging-port=9222")

    # مجلدات عمل مؤقتة (إن وُفرت من الـ YAML)
    user_data_dir = os.environ.get("CHROME_USER_DATA_DIR")
    cache_dir = os.environ.get("CHROME_CACHE_DIR")
    if user_data_dir:
        opts.add_argument(f"--user-data-dir={user_data_dir}")
    if cache_dir:
        opts.add_argument(f"--disk-cache-dir={cache_dir}")

    if CHROME_BIN:
        opts.binary_location = CHROME_BIN

    print("Resolving chromedriver via webdriver-manager ...")
    driver_path = ChromeDriverManager().install()
    print(f"Chromedriver path: {driver_path}")
    service = Service(driver_path)

    return webdriver.Chrome(service=service, options=opts)


def _wait(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def _wait_all(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))


def _safe_click(driver: webdriver.Chrome, el, retries: int = 3):
    last_err = None
    for i in range(1, retries + 1):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            # جرّب النقر العادي
            el.click()
            return
        except Exception as e1:
            last_err = e1
            try:
                # جرّب ActionChains
                ActionChains(driver).move_to_element(el).pause(0.05).click().perform()
                return
            except Exception as e2:
                last_err = e2
                try:
                    # جرّب JS click
                    driver.execute_script("arguments[0].click();", el)
                    return
                except Exception as e3:
                    last_err = e3
                    time.sleep(0.4)
    raise last_err


def _go_to_cart(driver: webdriver.Chrome):
    """حاول فتح السلة بعدة طرق، ثم استخدم fallback مباشر."""
    # انتظر ظهور أيقونة السلة
    el = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, CART_LINK)))
    # جرّب النقر بعدة أساليب
    _safe_click(driver, el, retries=4)

    # انتظر عناصر السلة؛ إن فشل، استخدم fallback
    try:
        _wait_all(driver, By.CSS_SELECTOR, CART_ITEM, timeout=10)
        return
    except Exception:
        # fallback مباشر للرابط
        base = DEMO_URL.rstrip("/")
        driver.get(f"{base}/cart.html")
        _wait_all(driver, By.CSS_SELECTOR, CART_ITEM, timeout=10)


def _dump_artifacts(driver: webdriver.Chrome, prefix: str = "fail"):
    try:
        out_dir = os.path.expanduser("~/selenium/artifacts")
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(out_dir, f"{prefix}_{ts}.png")
        driver.save_screenshot(path)
        print(f"[ARTIFACT] Saved screenshot: {path}")
    except Exception as e:
        print(f"[ARTIFACT] Failed to save screenshot: {e}")


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

        # انتظر قائمة المنتجات
        _wait_all(driver, By.CSS_SELECTOR, INVENTORY_ITEM)
        items = driver.find_elements(By.CSS_SELECTOR, INVENTORY_ITEM)[:6]

        # أضف أول 6 عناصر
        for i, item in enumerate(items, start=1):
            title_el = item.find_element(By.CLASS_NAME, "inventory_item_name")
            name = title_el.text.strip()
            btn = item.find_element(By.CSS_SELECTOR, ADD_TO_CART_BTN)
            _safe_click(driver, btn, retries=2)
            added.append(name)
            print(f"[ADD] {i}. {name}")

        # افتح السلة وتحقق (مع محاولات + fallback)
        _go_to_cart(driver)
        cart_items = _wait_all(driver, By.CSS_SELECTOR, CART_ITEM)
        print(f"Cart has {len(cart_items)} items after adding.")

        # احذف الكل
        for i, ci in enumerate(cart_items, start=1):
            name = ci.find_element(By.CLASS_NAME, "inventory_item_name").text.strip()
            _safe_click(driver, ci.find_element(By.CSS_SELECTOR, REMOVE_BTN), retries=2)
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
            _dump_artifacts(driver, prefix="assert")
            raise RuntimeError("Functional assertions failed.")

    except Exception as e:
        _dump_artifacts(driver, prefix="exception")
        # اطبع معلومات إضافية مفيدة للتشخيص
        try:
            print(f"[DEBUG] URL: {driver.current_url}")
            print(f"[DEBUG] Title: {driver.title}")
        except Exception:
            pass
        print(f"ERROR: {e}", file=sys.stderr)
        raise
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

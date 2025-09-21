#!/usr/bin/env python3
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# نستخدم webdriver-manager بدون ChromeType (متوافق مع v4)
from webdriver_manager.chrome import ChromeDriverManager


DEMO_URL = os.getenv("DEMO_URL", "https://www.saucedemo.com/")
DEMO_USER = os.getenv("DEMO_USER", "standard_user")
DEMO_PASS = os.getenv("DEMO_PASS", "secret_sauce")


def build_driver():
    print("Starting the browser...")
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        print(f"Using Chrome binary at: {chrome_bin}")

    opts = Options()
    # Headless افتراضيًا داخل CI/Agent
    if os.getenv("CI", "true").lower() in ("1", "true", "yes"):
        # headless الجديد (Chrome 109+)
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    if chrome_bin:
        opts.binary_location = chrome_bin

    # يثبت ChromeDriver المطابق لنسخة Google Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(5)
    return driver


def login_and_cart_flow(user: str, password: str):
    driver = None
    added, removed = [], []
    try:
        driver = build_driver()
        print("Browser started successfully. Navigating to the demo page to login.")
        driver.get(DEMO_URL)

        # تسجيل الدخول
        driver.find_element(By.ID, "user-name").send_keys(user)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()

        # تأكيد الوصول للمنتجات
        driver.find_element(By.ID, "inventory_container")

        # إضافة 6 عناصر (كل العناصر الموجودة)
        items = driver.find_elements(By.CSS_SELECTOR, ".inventory_item")
        for it in items[:6]:
            name = it.find_element(By.CSS_SELECTOR, ".inventory_item_name").text
            btn = it.find_element(By.CSS_SELECTOR, "button.btn")
            if "Add to cart" in btn.text:
                btn.click()
                added.append(name)

        print(f"[INFO] User logged in: {user}")
        print(f"[INFO] Items added to cart ({len(added)}): {', '.join(added)}")

        # الذهاب للسلة
        driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()

        # إزالة جميع العناصر
        rm_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn.btn_secondary, button.cart_button")
        # أحيانًا لا يظهر الاسم مباشرة داخل صفحة السلة لكل زر؛ نقرأ الأسماء من عناصر السلة
        cart_items = driver.find_elements(By.CSS_SELECTOR, ".cart_item")
        names_in_cart = [ci.find_element(By.CSS_SELECTOR, ".inventory_item_name").text for ci in cart_items]

        for i, btn in enumerate(rm_buttons):
            # حاول قراءة الاسم من cart_items إن وُجد
            name = names_in_cart[i] if i < len(names_in_cart) else f"Item#{i+1}"
            btn.click()
            removed.append(name)

        print(f"[INFO] Items removed from cart ({len(removed)}): {', '.join(removed)}")

        # لقطة شاشة اختيارية للحفظ كأثر (مفيدة للـrubric)
        out_png = os.path.join(os.getenv("HOME", "/tmp"), "selenium-final.png")
        try:
            driver.save_screenshot(out_png)
            print(f"[INFO] Saved screenshot: {out_png}")
        except Exception as e:
            print(f"[WARN] Could not save screenshot: {e}")

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else DEMO_USER
    pwd = sys.argv[2] if len(sys.argv) > 2 else DEMO_PASS
    login_and_cart_flow(user, pwd)

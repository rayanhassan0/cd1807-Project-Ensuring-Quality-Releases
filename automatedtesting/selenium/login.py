#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# سقوط احتياطي إلى webdriver-manager إذا فشل Selenium Manager
def _build_driver_with_fallback(options: ChromeOptions):
    try:
        # المحاولة 1: دع Selenium Manager يدبر الدرايفر
        return webdriver.Chrome(options=options)
    except WebDriverException as e:
        print(f"[WARN] Selenium Manager failed: {e}. Falling back to webdriver-manager...")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.utils import ChromeType
            driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            return webdriver.Chrome(service=Service(driver_path), options=options)
        except Exception as e2:
            print(f"[ERROR] webdriver-manager fallback failed: {e2}")
            raise

def _resolve_chrome_binary() -> str | None:
    # استخدم CHROME_BIN إن وُجد
    env_bin = os.environ.get("CHROME_BIN")
    if env_bin and Path(env_bin).exists():
        return env_bin

    # مسارات شائعة على Ubuntu/Snap
    candidates = [
        "/snap/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None

def login(user: str, password: str):
    print("Starting the browser...")

    options = ChromeOptions()
    # تشغيل بدون واجهة
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # حدّد مسار المتصفح (Chromium من snap في العادة على الوكيل)
    chrome_bin = _resolve_chrome_binary()
    if chrome_bin:
        options.binary_location = chrome_bin
        print(f"Using Chrome binary at: {chrome_bin}")
    else:
        print("[WARN] Could not find a Chrome/Chromium binary on common paths. "
              "If this fails, ensure chromium is installed and/or set CHROME_BIN.")

    driver = _build_driver_with_fallback(options)

    try:
        print("Browser started successfully. Navigating to the demo page to login.")
        driver.get("https://www.saucedemo.com/")

        # عناصر تسجيل الدخول
        user_el = driver.find_element("id", "user-name")
        pass_el = driver.find_element("id", "password")
        btn_el = driver.find_element("id", "login-button")

        user_el.clear(); user_el.send_keys(user)
        pass_el.clear(); pass_el.send_keys(password)
        btn_el.click()

        # انتظار بسيط لانتقال الصفحة
        time.sleep(2)

        # تحقق بسيط من نجاح الدخول
        try:
            driver.find_element("xpath", "//span[text()='Products']")
            login_ok = True
        except NoSuchElementException:
            login_ok = False

        # حفظ لقطة الدليل
        out_dir = Path(__file__).resolve().parent / "evidence"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_png = out_dir / "selenium-log.png"
        driver.save_screenshot(str(out_png))

        if login_ok:
            print(f"[OK] Login succeeded. Screenshot saved to: {out_png}")
        else:
            # التقط أيضاً HTML للمساعدة في التشخيص عند الفشل
            (out_dir / "page.html").write_text(driver.page_source)
            print(f"[FAIL] Login seems to have failed. "
                  f"Screenshot: {out_png} | HTML: {out_dir / 'page.html'}")
            sys.exit(1)

    finally:
        driver.quit()

if __name__ == "__main__":
    # قيَم افتراضية يمكن تغييرها من متغيرات البيئة في الـ Pipeline
    user = os.environ.get("DEMO_USER", "standard_user")
    pwd  = os.environ.get("DEMO_PASS", "secret_sauce")
    login(user, pwd)

#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

USERNAME = input("Username: ")
PASSWORD = input("Password: ")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )

    # Hapus tanda webdriver
    context.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

    page = context.new_page()
    
    print("[→] Membuka Twitter login...")
    page.goto("https://twitter.com/i/flow/login", wait_until="load", timeout=60000)
    time.sleep(8)

    print(f"[i] URL: {page.url}")
    page.fill('input[name="username_or_email"]', USERNAME)
    page.keyboard.press("Enter")
    time.sleep(4)

    page.fill('input[name="password"]', PASSWORD)
    page.keyboard.press("Enter")
    time.sleep(10)

    print(f"[i] URL setelah login: {page.url}")
    elements = page.query_selector_all("[data-testid]")
    for el in elements[:30]:
        print(f"    {el.get_attribute('data-testid')}")

    browser.close()

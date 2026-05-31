#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

USERNAME = input("Username: ")
PASSWORD = input("Password: ")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")
    
    print("[→] Membuka Twitter login...")
    page.goto("https://twitter.com/i/flow/login", wait_until="load", timeout=60000)
    time.sleep(8)

    page.fill('input[name="username_or_email"]', USERNAME)
    page.keyboard.press("Enter")
    time.sleep(4)

    page.fill('input[name="password"]', PASSWORD)
    page.keyboard.press("Enter")
    time.sleep(8)  # tunggu lebih lama

    print(f"[i] URL sekarang: {page.url}")

    # Cek semua input yang ada (mungkin ada verifikasi tambahan)
    inputs = page.query_selector_all("input")
    print(f"[i] Input ditemukan: {len(inputs)}")
    for inp in inputs:
        print(f"    type={inp.get_attribute('type')} name={inp.get_attribute('name')} placeholder={inp.get_attribute('placeholder')}")

    elements = page.query_selector_all("[data-testid]")
    print(f"[i] data-testid ditemukan: {len(elements)}")
    for el in elements[:30]:
        print(f"    {el.get_attribute('data-testid')}")

    browser.close()

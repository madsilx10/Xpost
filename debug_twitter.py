#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")
    
    print("[→] Membuka Twitter login...")
    page.goto("https://twitter.com/i/flow/login", wait_until="load", timeout=60000)
    time.sleep(8)
    
    # Cek semua input yang ada
    inputs = page.query_selector_all("input")
    print(f"[i] Jumlah input ditemukan: {len(inputs)}")
    for inp in inputs:
        print(f"    type={inp.get_attribute('type')} name={inp.get_attribute('name')} autocomplete={inp.get_attribute('autocomplete')} placeholder={inp.get_attribute('placeholder')}")
    
    browser.close()

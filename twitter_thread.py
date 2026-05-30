#!/usr/bin/env python3
"""
Twitter Thread Poster
- Login otomatis ke akun Twitter sendiri
- Baca thread dari thread.txt (pisahkan tiap tweet dengan ---)
- Post sebagai thread berantai
"""

import json
import time
import random
import os
from playwright.sync_api import sync_playwright

# ── Config ───────────────────────────────────────────────────────────────────
ACCOUNTS_FILE = "accounts.json"   # [{"username": "...", "password": "..."}]
THREAD_FILE   = "thread.txt"      # pisahkan tiap tweet dengan ---
DELAY_MIN     = 3                 # detik, jeda antar tweet dalam thread
DELAY_MAX     = 6
# ─────────────────────────────────────────────────────────────────────────────


def load_thread(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    tweets = [t.strip() for t in content.split("---") if t.strip()]
    return tweets


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def human_delay(min_s=DELAY_MIN, max_s=DELAY_MAX):
    time.sleep(random.uniform(min_s, max_s))


def post_thread(username, password, tweets):
    print(f"\n[→] Login sebagai @{username}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 10; Pixel 4) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Mobile Safari/537.36"
            )
        )
        page = context.new_page()

        # ── Login ─────────────────────────────────────────────────────────────
        page.goto("https://twitter.com/i/flow/login", wait_until="networkidle")
        human_delay(2, 4)

        # Username
        page.wait_for_selector('input[autocomplete="username"]', timeout=15000)
        page.fill('input[autocomplete="username"]', username)
        page.keyboard.press("Enter")
        human_delay(1.5, 3)

        # Kadang Twitter minta verifikasi nama/email tambahan
        try:
            extra = page.wait_for_selector(
                'input[data-testid="ocfEnterTextTextInput"]', timeout=5000
            )
            if extra:
                extra.fill(username)
                page.keyboard.press("Enter")
                human_delay(1.5, 3)
        except Exception:
            pass

        # Password
        page.wait_for_selector('input[name="password"]', timeout=15000)
        page.fill('input[name="password"]', password)
        page.keyboard.press("Enter")
        human_delay(3, 5)

        # Pastikan sudah login
        try:
            page.wait_for_selector('[data-testid="SideNav_NewTweet_Button"]', timeout=15000)
            print(f"[✓] Login berhasil: @{username}")
        except Exception:
            print(f"[✗] Login gagal: @{username} — cek username/password atau ada 2FA")
            browser.close()
            return False

        # ── Post Thread ───────────────────────────────────────────────────────
        for i, tweet_text in enumerate(tweets):
            print(f"    [{i+1}/{len(tweets)}] Posting: {tweet_text[:50]}...")

            if i == 0:
                page.click('[data-testid="SideNav_NewTweet_Button"]')
                human_delay(1.5, 2.5)
            else:
                try:
                    page.wait_for_selector('[data-testid="addButton"]', timeout=8000)
                    page.click('[data-testid="addButton"]')
                    human_delay(1, 2)
                except Exception:
                    print("    [!] Tombol 'Add tweet' tidak ditemukan...")
                    pass

            # Tulis tweet
            editor = page.wait_for_selector(
                '[data-testid="tweetTextarea_0"], .public-DraftEditor-content, [role="textbox"]',
                timeout=10000
            )
            editor.click()
            page.keyboard.type(tweet_text, delay=random.randint(30, 80))
            human_delay(1, 2)

        # Tombol Post
        try:
            tweet_all = page.query_selector('[data-testid="tweetButton"]')
            if tweet_all:
                tweet_all.click()
            else:
                page.click('[data-testid="tweetButtonInline"]')
        except Exception:
            page.click('[data-testid="tweetButton"]')

        human_delay(3, 5)
        print(f"[✓] Thread berhasil dipost oleh @{username}!")

        browser.close()
        return True


def main():
    # Load thread
    if not os.path.exists(THREAD_FILE):
        print(f"[✗] File '{THREAD_FILE}' tidak ditemukan!")
        print("     Buat file thread.txt, pisahkan tiap tweet dengan ---")
        print()
        print("     Contoh:")
        print("     Tweet pertama nih")
        print("     ---")
        print("     Lanjutan thread")
        print("     ---")
        print("     Tweet ketiga")
        return

    tweets = load_thread(THREAD_FILE)
    if not tweets:
        print("[✗] thread.txt kosong!")
        return

    print(f"[i] Thread dimuat: {len(tweets)} tweet")

    # Pilih mode
    print("\nMode:")
    print("  1. Input akun manual (1 akun)")
    print("  2. Dari accounts.json")
    mode = input("Pilih [1/2]: ").strip()

    if mode == "1":
        username = input("Username/Email: ").strip()
        password = input("Password: ").strip()
        post_thread(username, password, tweets)

    elif mode == "2":
        if not os.path.exists(ACCOUNTS_FILE):
            print(f"[✗] File '{ACCOUNTS_FILE}' tidak ditemukan!")
            print('     Format: [{"username": "...", "password": "..."}]')
            return

        accounts = load_json(ACCOUNTS_FILE)
        print(f"\n[i] {len(accounts)} akun ditemukan")
        print("  a. Semua akun")
        print("  b. Dari akun ke-N sampai selesai")
        sub = input("Pilih [a/b]: ").strip().lower()

        if sub == "a":
            start = 0
        elif sub == "b":
            start = int(input(f"Mulai dari akun ke- (1-{len(accounts)}): ")) - 1
        else:
            print("Pilihan tidak valid.")
            return

        for i, acc in enumerate(accounts[start:], start=start + 1):
            print(f"\n[{i}/{len(accounts)}] Akun: @{acc['username']}")
            success = post_thread(acc["username"], acc["password"], tweets)
            if success and i < len(accounts):
                jeda = random.uniform(10, 20)
                print(f"    [i] Jeda {jeda:.0f} detik sebelum akun berikutnya...")
                time.sleep(jeda)
    else:
        print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()

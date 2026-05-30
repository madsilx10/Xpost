#!/usr/bin/env python3
"""
Twitter Thread Poster - pakai twikit
- Login otomatis, session disimpen supaya nggak login ulang
- Baca thread dari thread.txt (pisahkan tiap tweet dengan ---)
"""

import asyncio
import json
import time
import random
import os
from twikit import Client

# ── Config ───────────────────────────────────────────────────────────────────
ACCOUNTS_FILE = "accounts.json"   # [{"username": "...", "email": "...", "password": "..."}]
THREAD_FILE   = "thread.txt"      # pisahkan tiap tweet dengan ---
COOKIES_DIR   = "cookies"         # folder simpan session tiap akun
DELAY_MIN     = 3
DELAY_MAX     = 6
# ─────────────────────────────────────────────────────────────────────────────


def load_thread(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return [t.strip() for t in content.split("---") if t.strip()]


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def human_delay():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


async def post_thread(username, email, password, tweets):
    client = Client("en-US")
    cookies_path = os.path.join(COOKIES_DIR, f"{username}.json")
    os.makedirs(COOKIES_DIR, exist_ok=True)

    # Login atau pakai cookies tersimpan
    if os.path.exists(cookies_path):
        print(f"  [i] Pakai session tersimpan: @{username}")
        client.load_cookies(cookies_path)
    else:
        print(f"  [→] Login: @{username}")
        await client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password
        )
        client.save_cookies(cookies_path)
        print(f"  [✓] Login berhasil, session disimpen")

    # Post thread
    reply_to_id = None
    for i, tweet_text in enumerate(tweets):
        print(f"    [{i+1}/{len(tweets)}] Posting: {tweet_text[:60]}...")
        try:
            if reply_to_id:
                tweet = await client.create_tweet(text=tweet_text, reply_to=reply_to_id)
            else:
                tweet = await client.create_tweet(text=tweet_text)
            reply_to_id = tweet.id
            print(f"    [✓] Tweet {i+1} berhasil (ID: {reply_to_id})")
        except Exception as e:
            print(f"    [✗] Gagal tweet {i+1}: {e}")
            return False

        if i < len(tweets) - 1:
            human_delay()

    print(f"  [✓] Thread selesai: @{username}")
    return True


async def main():
    if not os.path.exists(THREAD_FILE):
        print(f"[✗] File '{THREAD_FILE}' tidak ditemukan!")
        print("     Buat thread.txt, pisahkan tiap tweet dengan ---\n")
        print("     Contoh isi thread.txt:")
        print("     Tweet pertama")
        print("     ---")
        print("     Tweet kedua")
        return

    tweets = load_thread(THREAD_FILE)
    if not tweets:
        print("[✗] thread.txt kosong!")
        return

    print(f"[i] Thread dimuat: {len(tweets)} tweet")

    print("\nMode:")
    print("  1. Input akun manual (1 akun)")
    print("  2. Dari accounts.json")
    mode = input("Pilih [1/2]: ").strip()

    if mode == "1":
        username = input("Username: ").strip()
        email    = input("Email: ").strip()
        password = input("Password: ").strip()
        try:
            await post_thread(username, email, password, tweets)
        except Exception as e:
            print(f"[✗] Error: {e}")

    elif mode == "2":
        accounts = load_json(ACCOUNTS_FILE)
        if not accounts:
            print(f"[✗] '{ACCOUNTS_FILE}' tidak ditemukan atau kosong!")
            print('     Format:')
            print('     [{"username": "...", "email": "...", "password": "..."}]')
            return

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
            try:
                await post_thread(acc["username"], acc["email"], acc["password"], tweets)
                if i < len(accounts):
                    jeda = random.uniform(10, 20)
                    print(f"  [i] Jeda {jeda:.0f} detik...")
                    time.sleep(jeda)
            except Exception as e:
                print(f"  [✗] Error @{acc['username']}: {e}")
                continue
    else:
        print("Pilihan tidak valid.")


if __name__ == "__main__":
    asyncio.run(main())

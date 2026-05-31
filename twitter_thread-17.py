#!/usr/bin/env python3
"""
Twitter Thread Poster - pakai auth_token + ct0
- Tanpa perlu login, langsung pakai token dari browser
- Baca thread dari thread.txt (pisahkan tiap tweet dengan ---)
"""

import time
import random
import os
import requests

# ── Config ───────────────────────────────────────────────────────────────────
ACCOUNTS_FILE = "accounts.txt"  # [{"username":"...","auth_token":"...","ct0":"..."}]
THREAD_FILE   = "thread.txt"
DELAY_MIN     = 3
DELAY_MAX     = 6
# ─────────────────────────────────────────────────────────────────────────────


def load_thread(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return [t.strip() for t in content.split("---") if t.strip()]


def load_accounts(path):
    if not os.path.exists(path):
        return []
    accounts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) == 3:
                accounts.append({"username": parts[0], "auth_token": parts[1], "ct0": parts[2]})
    return accounts


def human_delay():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


def post_thread(username, auth_token, ct0, tweets):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "X-Csrf-Token": ct0,
        "Content-Type": "application/json",
        "Origin": "https://x.com",
        "Referer": "https://x.com/home",
    })
    session.cookies.set("auth_token", auth_token, domain=".x.com")
    session.cookies.set("ct0", ct0, domain=".x.com")

    reply_to_id = None

    for i, tweet_text in enumerate(tweets):
        print(f"    [{i+1}/{len(tweets)}] Posting: {tweet_text[:60]}...")

        payload = {
            "variables": {
                "tweet_text": tweet_text,
                "dark_request": False,
                "media": {"media_entities": [], "possibly_sensitive": False},
                "semantic_annotation_ids": []
            },
            "features": {
                "tweetypie_unmention_optimization_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": False,
                "tweet_awards_web_tipping_enabled": False,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "interactive_text_enabled": True,
                "responsive_web_text_conversations_enabled": False,
                "responsive_web_enhance_cards_enabled": False
            },
            "queryId": "SoVnbfCycZ7fERGCwpZkYA"
        }

        if reply_to_id:
            payload["variables"]["reply"] = {
                "in_reply_to_tweet_id": reply_to_id,
                "exclude_reply_user_ids": []
            }

        r = session.post(
            "https://x.com/i/api/graphql/SoVnbfCycZ7fERGCwpZkYA/CreateTweet",
            json=payload
        )

        if r.status_code != 200:
            print(f"    [✗] Gagal: {r.status_code} - {r.text[:200]}")
            return False

        try:
            reply_to_id = r.json()["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
            print(f"    [✓] Tweet {i+1} berhasil (ID: {reply_to_id})")
        except Exception:
            print(f"    [!] Tweet {i+1} mungkin berhasil tapi ID tidak terbaca")

        if i < len(tweets) - 1:
            human_delay()

    print(f"  [✓] Thread selesai: @{username}")
    return True


def main():
    if not os.path.exists(THREAD_FILE):
        print(f"[✗] File '{THREAD_FILE}' tidak ditemukan!")
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
    print("  1. Input token manual (1 akun)")
    print("  2. Dari accounts.json")
    mode = input("Pilih [1/2]: ").strip()

    if mode == "1":
        username   = input("Username: ").strip()
        auth_token = input("auth_token: ").strip()
        ct0        = input("ct0: ").strip()
        post_thread(username, auth_token, ct0, tweets)

    elif mode == "2":
        accounts = load_accounts(ACCOUNTS_FILE)
        if not accounts:
            print(f"[✗] '{ACCOUNTS_FILE}' tidak ditemukan atau kosong!")
            print('     Format:')
            print('     [{"username":"...","auth_token":"...","ct0":"..."}]')
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
            post_thread(acc["username"], acc["auth_token"], acc["ct0"], tweets)
            if i < len(accounts):
                jeda = random.uniform(10, 20)
                print(f"  [i] Jeda {jeda:.0f} detik...")
                time.sleep(jeda)
    else:
        print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()

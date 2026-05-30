#!/usr/bin/env python3
"""
Twitter Thread Poster
- Login otomatis via HTTP request (tanpa browser)
- Simpan token ke file supaya nggak perlu login ulang
- Baca thread dari thread.txt (pisahkan tiap tweet dengan ---)
"""

import json
import time
import random
import os
import requests

# ── Config ───────────────────────────────────────────────────────────────────
ACCOUNTS_FILE = "accounts.json"   # [{"username": "...", "password": "..."}]
THREAD_FILE   = "thread.txt"      # pisahkan tiap tweet dengan ---
TOKENS_FILE   = "tokens.json"     # cache token supaya nggak login ulang
DELAY_MIN     = 3
DELAY_MAX     = 6
# ─────────────────────────────────────────────────────────────────────────────

HEADERS_BASE = {
    "User-Agent": "TwitterAndroid/10.21.0-release.0 (310210000-r-0) ONEPLUS+A6003/9 (OnePlus;ONEPLUS+A6003;OnePlus;OnePlus3;0;;1;2016)",
    "X-Twitter-Client": "TwitterAndroid",
    "X-Twitter-Client-Version": "10.21.0-release.0",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
}

AUTH_TOKEN_BEARER = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"


def load_thread(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return [t.strip() for t in content.split("---") if t.strip()]


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def human_delay(min_s=DELAY_MIN, max_s=DELAY_MAX):
    time.sleep(random.uniform(min_s, max_s))


def get_guest_token():
    r = requests.post(
        "https://api.twitter.com/1.1/guest/activate.json",
        headers={**HEADERS_BASE, "Authorization": AUTH_TOKEN_BEARER},
    )
    r.raise_for_status()
    return r.json()["guest_token"]


def login(username, password):
    print(f"  [→] Login: @{username}")
    session = requests.Session()
    session.headers.update(HEADERS_BASE)
    session.headers.update({"Authorization": AUTH_TOKEN_BEARER})

    # Step 1: guest token
    guest_token = get_guest_token()
    session.headers.update({"X-Guest-Token": guest_token})

    flow_url = "https://api.twitter.com/1.1/onboarding/task.json"

    # Step 2: init login flow
    r = session.post(flow_url, params={"flow_name": "login"}, json={
        "input_flow_data": {"flow_context": {"debug_overrides": {}, "start_location": {"location": "splash_screen"}}},
        "subtask_versions": {}
    })
    r.raise_for_status()
    data = r.json()
    flow_token = data["flow_token"]

    # Step 3: masukkan username
    r = session.post(flow_url, json={
        "flow_token": flow_token,
        "subtask_inputs": [{
            "subtask_id": "LoginEnterUserIdentifierSSO",
            "settings_list": {
                "setting_responses": [{
                    "key": "user_identifier",
                    "response_data": {"text_data": {"result": username}}
                }],
                "link": "next_link"
            }
        }]
    })
    r.raise_for_status()
    data = r.json()
    flow_token = data["flow_token"]

    # Step 4: masukkan password
    r = session.post(flow_url, json={
        "flow_token": flow_token,
        "subtask_inputs": [{
            "subtask_id": "LoginEnterPassword",
            "enter_password": {"password": password, "link": "next_link"}
        }]
    })
    r.raise_for_status()
    data = r.json()
    flow_token = data["flow_token"]

    # Step 5: account duplication check
    r = session.post(flow_url, json={
        "flow_token": flow_token,
        "subtask_inputs": [{
            "subtask_id": "AccountDuplicationCheck",
            "check_logged_in_account": {"link": "AccountDuplicationCheck_false"}
        }]
    })
    r.raise_for_status()

    # Ambil auth_token & ct0 dari cookies
    cookies = session.cookies.get_dict()
    auth_token = cookies.get("auth_token")
    ct0 = cookies.get("ct0")

    if not auth_token:
        raise Exception("Login gagal — auth_token tidak ditemukan. Cek username/password atau ada 2FA.")

    print(f"  [✓] Login berhasil: @{username}")
    return auth_token, ct0


def post_thread(username, auth_token, ct0, tweets):
    session = requests.Session()
    session.headers.update({
        **HEADERS_BASE,
        "Authorization": AUTH_TOKEN_BEARER,
        "Cookie": f"auth_token={auth_token}; ct0={ct0}",
        "X-Csrf-Token": ct0,
        "Content-Type": "application/json",
    })

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
            "https://twitter.com/i/api/graphql/SoVnbfCycZ7fERGCwpZkYA/CreateTweet",
            json=payload
        )

        if r.status_code != 200:
            print(f"    [✗] Gagal posting tweet {i+1}: {r.status_code} {r.text[:200]}")
            return False

        result = r.json()
        try:
            reply_to_id = result["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
        except Exception:
            print(f"    [!] Tidak bisa ambil tweet ID, thread mungkin terputus")

        human_delay(DELAY_MIN, DELAY_MAX)

    print(f"  [✓] Thread selesai dipost oleh @{username}!")
    return True


def get_or_login(username, password, tokens):
    if username in tokens:
        print(f"  [i] Pakai token tersimpan untuk @{username}")
        return tokens[username]["auth_token"], tokens[username]["ct0"]

    auth_token, ct0 = login(username, password)
    tokens[username] = {"auth_token": auth_token, "ct0": ct0}
    save_json(TOKENS_FILE, tokens)
    return auth_token, ct0


def main():
    if not os.path.exists(THREAD_FILE):
        print(f"[✗] File '{THREAD_FILE}' tidak ditemukan!")
        print("     Buat thread.txt, pisahkan tiap tweet dengan ---\n")
        print("     Contoh:")
        print("     Tweet pertama")
        print("     ---")
        print("     Tweet kedua")
        return

    tweets = load_thread(THREAD_FILE)
    if not tweets:
        print("[✗] thread.txt kosong!")
        return

    print(f"[i] Thread dimuat: {len(tweets)} tweet")

    tokens = load_json(TOKENS_FILE)

    print("\nMode:")
    print("  1. Input akun manual (1 akun)")
    print("  2. Dari accounts.json")
    mode = input("Pilih [1/2]: ").strip()

    if mode == "1":
        username = input("Username/Email: ").strip()
        password = input("Password: ").strip()
        try:
            auth_token, ct0 = get_or_login(username, password, tokens)
            post_thread(username, auth_token, ct0, tweets)
        except Exception as e:
            print(f"[✗] Error: {e}")

    elif mode == "2":
        if not os.path.exists(ACCOUNTS_FILE):
            print(f"[✗] File '{ACCOUNTS_FILE}' tidak ditemukan!")
            print('     Format: [{"username": "...", "password": "..."}]')
            return

        accounts = load_json(ACCOUNTS_FILE)
        if isinstance(accounts, dict):
            accounts = list(accounts.values())

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
                auth_token, ct0 = get_or_login(acc["username"], acc["password"], tokens)
                success = post_thread(acc["username"], auth_token, ct0, tweets)
                if success and i < len(accounts):
                    jeda = random.uniform(10, 20)
                    print(f"  [i] Jeda {jeda:.0f} detik...")
                    time.sleep(jeda)
            except Exception as e:
                print(f"  [✗] Error @{acc['username']}: {e}")
                continue
    else:
        print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()

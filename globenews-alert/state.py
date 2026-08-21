"""
이미 이메일로 보낸 기사(guid)를 기록해서 중복 발송을 막는 모듈.
"""
import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_guids.json")
MAX_KEEP = 500


def load_seen():
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen_set):
    trimmed = list(seen_set)[-MAX_KEEP:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False)

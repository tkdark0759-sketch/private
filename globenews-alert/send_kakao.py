"""
카카오톡 "나에게 보내기" API로 메시지를 전송하는 모듈.
"""
import os
import json
import requests

REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
CLIENT_SECRET = os.environ.get("KAKAO_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")


def _refresh_access_token() -> str:
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }
    resp = requests.post(url, data=data, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"토큰 갱신 실패 ({resp.status_code}): {resp.text}")
    return resp.json()["access_token"]


def send_kakao_message(text: str):
    if not REST_API_KEY or not REFRESH_TOKEN:
        print("[카카오톡 전송 스킵] KAKAO_REST_API_KEY / KAKAO_REFRESH_TOKEN 환경변수가 없습니다.")
        return

    try:
        access_token = _refresh_access_token()
    except Exception as e:
        print(f"[카카오톡 토큰 갱신 실패] {e}")
        return

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}

    if len(text) > 1800:
        text = text[:1800] + "\n... (길이 제한으로 일부 생략, 자세한 내용은 이메일 참고)"

    template_object = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": "https://www.globenewswire.com",
            "mobile_web_url": "https://www.globenewswire.com",
        },
    }
    data = {"template_object": json.dumps(template_object, ensure_ascii=False)}

    try:
        resp = requests.post(url, headers=headers, data=data, timeout=15)
        if resp.status_code == 200:
            print("카카오톡 전송 성공")
        else:
            print(f"카카오톡 전송 실패: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[카카오톡 전송 오류] {e}")

"""
카카오 REFRESH_TOKEN을 최초 1회 발급받기 위한 스크립트. 내 PC에서 직접 실행.

1. https://developers.kakao.com 에서 앱 생성
2. [카카오 로그인] 활성화, Redirect URI에 https://localhost.com 등록
3. [동의항목]에서 "카카오톡 메시지 전송(talk_message)" 필수 동의로 설정
4. 아래 REST_API_KEY 를 [앱 키] > REST API 키로 교체
5. pip install requests 후 python get_kakao_token.py 실행
6. 안내대로 브라우저에서 로그인 → 리다이렉트된 URL 전체를 복사해서 붙여넣기
7. 출력되는 REFRESH_TOKEN을 GitHub Secrets(KAKAO_REFRESH_TOKEN)에 등록
"""
import requests
import urllib.parse

REST_API_KEY = "여기에_본인의_REST_API_키_입력"
REDIRECT_URI = "https://localhost.com"


def main():
    auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={REST_API_KEY}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
        "&response_type=code"
        "&scope=talk_message"
    )
    print("아래 주소를 브라우저에 붙여넣어 접속하세요:\n")
    print(auth_url)
    redirected = input("\n리다이렉트된 URL 입력: ").strip()

    parsed = urllib.parse.urlparse(redirected)
    code = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        print("code를 찾을 수 없습니다.")
        return

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    resp = requests.post(token_url, data=data)
    resp.raise_for_status()
    tokens = resp.json()

    print("\nREFRESH_TOKEN:", tokens.get("refresh_token"))


if __name__ == "__main__":
    main()

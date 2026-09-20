"""
완전 무료 번역 모듈.
구글 번역은 GitHub Actions 같은 클라우드 서버 IP를 자주 차단하기 때문에,
서버 요청에 더 관대한 MyMemory 번역 API를 기본으로 사용함 (여전히 무료, API 키 불필요).
"""
import time
from deep_translator import MyMemoryTranslator, GoogleTranslator


def _translate_with_mymemory(text: str) -> str:
    return MyMemoryTranslator(source="auto", target="ko").translate(text[:490])


def _translate_with_google(text: str) -> str:
    return GoogleTranslator(source="auto", target="ko").translate(text[:4500])


def translate_to_korean(text: str, max_retries: int = 2) -> str:
    if not text:
        return "(번역할 내용이 없습니다. 원문 링크를 참고하세요.)"

    for attempt in range(1, max_retries + 1):
        try:
            result = _translate_with_mymemory(text)
            time.sleep(1)
            return result
        except Exception as e:
            print(f"[MyMemory 번역 실패 {attempt}/{max_retries}] {e}")
            time.sleep(3)

    for attempt in range(1, max_retries + 1):
        try:
            result = _translate_with_google(text)
            time.sleep(2)
            return result
        except Exception as e:
            print(f"[구글 번역 실패 {attempt}/{max_retries}] {e}")
            time.sleep(5)

    print("[번역 최종 실패] 모든 번역 시도가 실패했습니다.")
    return "(번역 실패 - 원문 링크를 참고하세요)"

"""
완전 무료 번역 모듈.
GitHub Actions 서버 IP는 구글 번역에서 거의 항상 차단되는 것으로 확인되어,
MyMemory 번역을 기본으로 바로 사용함 (API 키 불필요).
"""
import time
from deep_translator import MyMemoryTranslator


def _translate_with_mymemory(text: str) -> str:
    return MyMemoryTranslator(source="en-GB", target="ko-KR").translate(text[:490])


def translate_to_korean(text: str, max_retries: int = 3) -> str:
    if not text:
        return "(번역할 내용이 없습니다. 원문 링크를 참고하세요.)"

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            result = _translate_with_mymemory(text)
            time.sleep(1)
            return result
        except Exception as e:
            last_error = e
            print(f"[MyMemory 번역 실패 {attempt}/{max_retries}] {e}")
            time.sleep(3)

    print(f"[번역 최종 실패] {last_error}")
    return "(번역 실패 - 원문 링크를 참고하세요)"

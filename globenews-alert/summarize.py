"""
완전 무료 번역 모듈.
1차: 구글 번역(언어 자동감지 지원) 시도
2차: 구글이 막히면 MyMemory 번역(영어 기준 고정, "ko-KR" 코드 사용) 시도
"""
import time
from deep_translator import GoogleTranslator, MyMemoryTranslator


def _translate_with_google(text: str) -> str:
    return GoogleTranslator(source="auto", target="ko").translate(text[:4500])


def _translate_with_mymemory(text: str) -> str:
    return MyMemoryTranslator(source="en-GB", target="ko-KR").translate(text[:490])


def translate_to_korean(text: str, max_retries: int = 2) -> str:
    if not text:
        return "(번역할 내용이 없습니다. 원문 링크를 참고하세요.)"

    for attempt in range(1, max_retries + 1):
        try:
            result = _translate_with_google(text)
            time.sleep(2)
            return result
        except Exception as e:
            print(f"[구글 번역 실패 {attempt}/{max_retries}] {e}")
            time.sleep(5)

    for attempt in range(1, max_retries + 1):
        try:
            result = _translate_with_mymemory(text)
            time.sleep(1)
            return result
        except Exception as e:
            print(f"[MyMemory 번역 실패 {attempt}/{max_retries}] {e}")
            time.sleep(3)

    print("[번역 최종 실패] 모든 번역 시도가 실패했습니다.")
    return "(번역 실패 - 원문 링크를 참고하세요)"

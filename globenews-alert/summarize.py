"""
완전 무료 번역 모듈. 원문 언어를 자동 감지해서 한국어로 번역함.
연속 요청 시 구글 무료 번역이 차단할 수 있어, 실패 시 잠시 대기 후 재시도함.
"""
import time
from deep_translator import GoogleTranslator


def translate_to_korean(text: str, max_retries: int = 3) -> str:
    if not text:
        return "(번역할 내용이 없습니다. 원문 링크를 참고하세요.)"

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            result = GoogleTranslator(source="auto", target="ko").translate(text[:4500])
            time.sleep(2)
            return result
        except Exception as e:
            last_error = e
            print(f"[번역 실패 {attempt}/{max_retries}] {e}")
            time.sleep(5)

    print(f"[번역 최종 실패] {last_error}")
    return "(번역 실패 - 원문 링크를 참고하세요)"

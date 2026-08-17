"""
완전 무료 번역 모듈.
구글 뉴스가 제공하는 영문 스니펫(요약)을 deep-translator로 한국어 번역합니다.
(별도 API 키 불필요)
"""
from deep_translator import GoogleTranslator


def translate_to_korean(text: str) -> str:
    if not text:
        return "(요약할 내용이 없습니다. 원문 링크를 참고하세요.)"
    try:
        return GoogleTranslator(source="en", target="ko").translate(text[:4500])
    except Exception as e:
        print(f"[번역 실패] {e}")
        return f"(번역 실패, 원문: {text})"

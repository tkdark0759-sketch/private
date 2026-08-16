"""
완전 무료 버전: 유료 API 없이 요약 + 한국어 번역을 처리하는 모듈.

- 요약: sumy (LexRank 알고리즘) - 원문에서 핵심 문장 3개를 추출 (API 키 불필요)
- 번역: deep-translator의 GoogleTranslator (무료, API 키 불필요)

주의: 무료 구글 번역은 비공식 방식이라 가끔 요청이 막히거나 실패할 수 있습니다.
      실패 시에는 영어 원문 요약이라도 그대로 보여줍니다.
"""
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from deep_translator import GoogleTranslator

SENTENCE_COUNT = 3  # 추출할 핵심 문장 개수


def _extractive_summary(text: str, sentence_count: int = SENTENCE_COUNT) -> str:
    """긴 영어 본문에서 핵심 문장만 추출 (자체 알고리즘, API 불필요)"""
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    sentences = summarizer(parser.document, sentence_count)
    return " ".join(str(s) for s in sentences)


def _translate_to_korean(text: str) -> str:
    """무료 구글 번역으로 한국어 변환"""
    try:
        # 구글 번역 무료 API는 한 번에 너무 긴 텍스트를 받지 않으므로 4500자로 제한
        return GoogleTranslator(source="en", target="ko").translate(text[:4500])
    except Exception as e:
        print(f"[번역 실패] {e}")
        return text  # 번역 실패 시 영어 원문이라도 반환


def summarize_and_translate(title: str, body_text: str) -> str:
    """기사 제목+본문을 받아 한국어 요약을 반환. 실패 시 안내 문구 반환."""
    if not body_text:
        return "(본문 수집에 실패해 요약을 생략합니다. 원문 링크를 참고하세요.)"

    try:
        eng_summary = _extractive_summary(body_text)
        if not eng_summary:
            eng_summary = body_text[:500]  # 추출 실패 시 앞부분이라도 사용
    except Exception as e:
        print(f"[요약 실패] {e}")
        eng_summary = body_text[:500]

    ko_summary = _translate_to_korean(eng_summary)
    return ko_summary

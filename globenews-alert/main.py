"""
매일 실행되는 메인 스크립트.
1) GlobeNewswire에서 keywords.py에 등록된 키워드 기사를 수집
2) 각 기사 원문을 가져와 Claude API로 한국어 요약/번역
3) 결과를 이메일로 전송

로컬 테스트: python main.py
GitHub Actions에서는 .github/workflows/daily.yml 이 매일 이 스크립트를 실행함
"""
import html as html_lib

from fetch_news import fetch_all, fetch_article_text
from summarize import summarize_and_translate
from send_email import send_email


def build_html(enriched_articles) -> str:
    if not enriched_articles:
        return "<p>오늘은 등록된 키워드 관련 새 기사가 없습니다.</p>"

    parts = [f"<h2>오늘의 GlobeNewswire 뉴스 ({len(enriched_articles)}건)</h2>"]

    for a in enriched_articles:
        title = html_lib.escape(a["title"])
        keyword = html_lib.escape(a["keyword"])
        link = html_lib.escape(a["link"])
        summary_html = html_lib.escape(a["summary_ko"]).replace("\n", "<br>")

        parts.append(f"""
        <div style="margin-bottom:24px; padding-bottom:16px; border-bottom:1px solid #ddd;">
            <div style="font-size:12px; color:#888;">[{keyword}]</div>
            <div style="font-size:16px; font-weight:bold; margin:4px 0;">{title}</div>
            <div style="font-size:14px; line-height:1.6; margin:8px 0;">{summary_html}</div>
            <a href="{link}" style="font-size:13px; color:#1a73e8;">원문 보기 →</a>
        </div>
        """)

    return "\n".join(parts)


def main():
    articles = fetch_all(hours=24)
    print(f"수집된 기사 수: {len(articles)}")

    enriched = []
    for a in articles:
        print(f"처리 중: [{a['keyword']}] {a['title']}")
        body_text = fetch_article_text(a["link"])
        summary_ko = summarize_and_translate(a["title"], body_text)
        enriched.append({**a, "summary_ko": summary_ko})

    html_body = build_html(enriched)
    send_email(subject="오늘의 GlobeNewswire 뉴스 요약", html_body=html_body)


if __name__ == "__main__":
    main()

"""
매일 실행되는 메인 스크립트.
1) 구글 뉴스에서 site:globenewswire.com + 키워드로 관련 기사 검색
2) 구글 뉴스 스니펫을 한국어로 번역
3) 결과를 이메일로 전송
"""
import html as html_lib

from fetch_news import fetch_all
from summarize import translate_to_korean
from send_email import send_email


def build_html(enriched_articles) -> str:
    if not enriched_articles:
        return "<p>오늘은 등록된 키워드 관련 새 기사가 없습니다.</p>"

    parts = [f"<h2>오늘의 뉴스 ({len(enriched_articles)}건)</h2>"]

    for a in enriched_articles:
        title = html_lib.escape(a["title"])
        keyword = html_lib.escape(a["keyword"])
        link = html_lib.escape(a["link"])
        summary_ko = html_lib.escape(a["summary_ko"]).replace("\n", "<br>")

        parts.append(f"""
        <div style="margin-bottom:24px; padding-bottom:16px; border-bottom:1px solid #ddd;">
            <div style="font-size:12px; color:#888;">[{keyword}]</div>
            <div style="font-size:16px; font-weight:bold; margin:4px 0;">{title}</div>
            <div style="font-size:14px; line-height:1.6; margin:8px 0;">{summary_ko}</div>
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
        summary_ko = translate_to_korean(a.get("summary", "") or a["title"])
        enriched.append({**a, "summary_ko": summary_ko})

    html_body = build_html(enriched)
    send_email(subject="오늘의 GlobeNewswire 뉴스 요약", html_body=html_body)


if __name__ == "__main__":
    main()

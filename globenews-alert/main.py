"""
GlobeNewswire 공식 피드에서 키워드가 매칭되는 새 기사를 찾아
한국어로 번역해서 이메일로 보내는 메인 스크립트.
"""
import html as html_lib
import requests
from bs4 import BeautifulSoup

from fetch_news import fetch_matching_articles
from summarize import translate_to_korean
from send_email import send_email
from state import load_seen, save_seen


def fetch_page_body(url: str, max_chars: int = 3000) -> str:
    if not url:
        return ""
    try:
        resp = requests.get(
            url, timeout=15, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        content_type = resp.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        body_text = "\n".join(p for p in paragraphs if p)
        return body_text[:max_chars]
    except Exception as e:
        print(f"[본문 수집 실패] {url} ({e})")
        return ""


def build_html(enriched_articles) -> str:
    parts = [f"<h2>새로운 뉴스 ({len(enriched_articles)}건)</h2>"]
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
            <a href="{link}" style="font-size:12px; color:#888;">원문 링크</a>
        </div>
        """)
    return "\n".join(parts)


def main():
    seen = load_seen()
    matched = fetch_matching_articles()
    print(f"매칭된 기사 수(전체): {len(matched)}")

    new_articles = [a for a in matched if a["guid"] not in seen]
    print(f"그 중 새로운 기사 수: {len(new_articles)}")

    if not new_articles:
        print("새 기사가 없어 메일을 보내지 않습니다.")
        return

    enriched = []
    for a in new_articles:
        print(f"처리 중: [{a['keyword']}] {a['title']}")
        body_text = fetch_page_body(a["link"])
        source_text = body_text or a["description"] or a["title"]
        summary_ko = translate_to_korean(source_text)
        enriched.append({**a, "summary_ko": summary_ko})

    html_body = build_html(enriched)
    send_email(subject=f"[뉴스 알림] 새 기사 {len(enriched)}건", html_body=html_body)

    seen.update(a["guid"] for a in new_articles)
    save_seen(seen)


if __name__ == "__main__":
    main()

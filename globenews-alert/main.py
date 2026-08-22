"""
GlobeNewswire 공식 피드에서 키워드가 매칭되는 새 기사를 찾아
한국어로 번역해서 이메일로 보내는 메인 스크립트.
공식 피드의 description 필드에 기사 전문이 HTML로 포함되어 있어서,
별도로 원문 페이지를 다시 열지 않고 이 description을 바로 사용함.
"""
import re
import html as html_lib
from bs4 import BeautifulSoup

from fetch_news import fetch_matching_articles
from summarize import translate_to_korean
from send_email import send_email
from send_kakao import send_kakao_message
from state import load_seen, save_seen


def strip_html(raw_html: str) -> str:
    """HTML 태그를 제거하고 읽기 좋은 순수 텍스트만 남김"""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "li"])]
    if paragraphs:
        text = "\n".join(p for p in paragraphs if p)
    else:
        text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


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
        plain_text = strip_html(a["description"]) or a["title"]
        summary_ko = translate_to_korean(plain_text)
        enriched.append({**a, "summary_ko": summary_ko})

    html_body = build_html(enriched)
    send_email(subject=f"[뉴스 알림] 새 기사 {len(enriched)}건", html_body=html_body)

    kakao_text = f"[뉴스 알림] 새 기사 {len(enriched)}건\n\n" + "\n\n".join(
        f"[{a['keyword']}] {a['title']}\n{a['summary_ko']}" for a in enriched
    )
    send_kakao_message(kakao_text)

    seen.update(a["guid"] for a in new_articles)
    save_seen(seen)


if __name__ == "__main__":
    main()

"""
Bing 뉴스 RSS를 이용해 'site:globenewswire.com + 키워드' 조합으로
GlobeNewswire에 게재된 관련 기사를 검색하고, 실제 원문 페이지의 본문까지 가져오는 모듈.

(구글 뉴스 RSS는 링크가 암호화되어 실제 주소를 코드로 알아낼 수 없어서
 Bing 뉴스 RSS로 전환 - 이쪽은 링크가 원문 그대로 제공됨)
"""
import re
import requests
import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

from keywords import KEYWORDS

RSS_TEMPLATE = "https://www.bing.com/news/search?q={query}&format=rss"


def _strip_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_page_body(url: str, max_chars: int = 3000) -> str:
    """실제 원문 페이지를 열어 본문 텍스트를 가져옴. PDF/실패 시 빈 문자열 반환."""
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


def fetch_articles_for_keyword(keyword: str, hours: int = 24):
    query = urllib.parse.quote(f'"{keyword}" site:globenewswire.com')
    url = RSS_TEMPLATE.format(query=query)
    feed = feedparser.parse(url)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    results = []

    for entry in feed.entries:
        if not getattr(entry, "published_parsed", None):
            continue

        published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published_dt < cutoff:
            continue

        title = _strip_html(entry.get("title", ""))
        link = entry.get("link", "")

        if "globenewswire.com" not in link:
            continue

        body_text = _fetch_page_body(link)

        results.append({
            "keyword": keyword,
            "title": title,
            "body_text": body_text,
            "link": link,
            "published": published_dt,
        })

    return results


def fetch_all(hours: int = 24):
    all_articles = []
    seen_links = set()

    for kw in KEYWORDS:
        for article in fetch_articles_for_keyword(kw, hours=hours):
            if article["link"] in seen_links:
                continue
            seen_links.add(article["link"])
            all_articles.append(article)

    all_articles.sort(key=lambda a: a["published"], reverse=True)
    return all_articles


if __name__ == "__main__":
    articles = fetch_all()
    if not articles:
        print("최근 24시간 내 매칭되는 기사가 없습니다.")
    for a in articles:
        print(f"[{a['keyword']}] {a['title']}\n  {a['link']}\n  본문 길이: {len(a['body_text'])}\n")

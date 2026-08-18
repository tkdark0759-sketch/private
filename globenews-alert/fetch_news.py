"""
Google News RSS를 이용해 'site:globenewswire.com + 키워드' 조합으로
GlobeNewswire에 게재된 관련 기사를 검색하는 모듈.
"""
import re
import requests
import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone

from keywords import KEYWORDS

RSS_TEMPLATE = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)


def _strip_html(raw_html: str) -> str:
    """구글 뉴스 요약에 섞여 들어오는 HTML 태그를 제거하고 순수 텍스트만 남김"""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _resolve_real_link(google_link: str) -> str:
    """구글 뉴스 중계 링크를 실제로 열어서, 최종적으로 도착하는 원문 주소를 알아냄"""
    if not google_link:
        return google_link
    try:
        resp = requests.get(
            google_link,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        final_url = resp.url
        if "news.google.com" in final_url:
            return google_link
        return final_url
    except Exception as e:
        print(f"[링크 해석 실패] {google_link} ({e})")
        return google_link


def fetch_articles_for_keyword(keyword: str, hours: int = 24):
    """구글 뉴스에서 'site:globenewswire.com {키워드}'로 검색, 최근 hours시간 내 기사만 반환"""
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
        summary = _strip_html(entry.get("summary", ""))
        link = _resolve_real_link(entry.get("link", ""))

        results.append({
            "keyword": keyword,
            "title": title,
            "summary": summary,
            "link": link,
            "published": published_dt,
        })

    return results


def fetch_all(hours: int = 24):
    """등록된 모든 키워드에 대해 기사를 모으고, 링크 기준으로 중복 제거"""
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
        print(f"[{a['keyword']}] {a['title']}\n  {a['link']}\n")

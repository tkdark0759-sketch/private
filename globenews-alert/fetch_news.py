"""
GlobeNewswire에서 keywords.py에 등록된 키워드가 포함된
최근 24시간 이내 보도자료를 가져오는 모듈.
"""
import feedparser
import requests
import urllib.parse
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

from keywords import KEYWORDS

# GlobeNewswire 키워드 검색용 RSS 엔드포인트
# 형식: https://rss.globenewswire.com/RssFeed/Language/EN/Keyword/{키워드}/Max/{개수}
RSS_TEMPLATE = "https://rss.globenewswire.com/RssFeed/Language/EN/Keyword/{keyword}/Max/30"


def fetch_articles_for_keyword(keyword: str, hours: int = 24):
    """특정 키워드로 GlobeNewswire RSS를 조회해서, 최근 hours시간 내 기사만 반환"""
    url = RSS_TEMPLATE.format(keyword=urllib.parse.quote(keyword))
    feed = feedparser.parse(url)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    results = []

    for entry in feed.entries:
        # published_parsed가 없는 경우 방어적으로 스킵
        if not getattr(entry, "published_parsed", None):
            continue

        published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published_dt < cutoff:
            continue

        title = entry.get("title", "")
        summary = entry.get("summary", "")

        # 혹시 검색어와 무관한 결과가 섞여 들어올 수 있으니,
        # 제목이나 요약에 키워드가 실제로 포함됐는지 한 번 더 확인
        haystack = f"{title} {summary}".lower()
        if keyword.lower() not in haystack:
            continue

        results.append({
            "keyword": keyword,
            "title": title,
            "link": entry.get("link", ""),
            "published": published_dt,
        })

    return results


def fetch_article_text(url: str, max_chars: int = 6000) -> str:
    """보도자료 원문 페이지에서 본문 텍스트를 추출 (요약/번역에 사용)"""
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # GlobeNewswire 기사 본문은 보통 <div class="main-body-container"> 계열에 들어있지만,
        # 페이지 구조가 바뀔 수 있으니 실패하면 전체 <article> 또는 <p> 태그들을 폴백으로 사용
        container = soup.select_one(".main-body-container") or soup.find("article") or soup

        paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
        text = "\n".join(p for p in paragraphs if p)

        return text[:max_chars] if text else ""
    except Exception as e:
        print(f"[본문 수집 실패] {url} ({e})")
        return ""


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

    # 최신순 정렬
    all_articles.sort(key=lambda a: a["published"], reverse=True)
    return all_articles


if __name__ == "__main__":
    # 단독 실행 시 테스트용 출력
    articles = fetch_all()
    if not articles:
        print("최근 24시간 내 매칭되는 기사가 없습니다.")
    for a in articles:
        print(f"[{a['keyword']}] {a['title']}\n  {a['link']}\n")

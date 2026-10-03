"""
네 가지 소스를 조합해서 기사를 찾는 모듈:
1) GlobeNewswire 조직 검색 - 회사 자체 뉴스를 정확하게 (전체 기록, 오탐 없음)
2) GlobeNewswire Class Action 피드 - 소송/공지(제3자 언급)를 단어경계 매칭으로
3) Business Wire 전체 피드 - 단어경계 매칭으로 (GlobeNewswire를 안 쓰는 회사 커버)
4) 구글 뉴스 검색 - 회사 자체 뉴스룸, 파트너사 뉴스룸 등 어디에 올라가든 구글이 색인한 것이면 포착
   (단, 구글 뉴스는 링크가 암호화되어 있어 본문 추출은 안 되고, 제목+스니펫만 활용)
"""
import re
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from bs4 import BeautifulSoup

from keywords import KEYWORDS

ORG_SEARCH_URL = "https://www.globenewswire.com/search/organization/{query}"
CLASS_ACTION_FEED_URL = "https://www.globenewswire.com/RssFeed/subjectcode/84-Class%20Action/feedTitle/GlobeNewswire%20-%20Class%20Action"
BUSINESSWIRE_FEED_URL = "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkpaGVlYXg=="
GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
NS = {"dc": "http://dublincore.org/documents/dcmi-namespace/"}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsAlertBot/1.0)"}


def _matches_keyword(haystack: str, keyword: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(keyword) + r"(?![A-Za-z0-9])"
    return re.search(pattern, haystack, re.IGNORECASE) is not None


def _strip_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _request_with_retry(url: str, max_retries: int = 3, timeout: int = 30):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers=HEADERS)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_error = e
            print(f"[요청 실패 {attempt}/{max_retries}] {url} ({e})")
            if attempt < max_retries:
                time.sleep(5)
    print(f"[요청 최종 실패] {url} ({last_error})")
    return None


def fetch_org_articles(keyword: str):
    url = ORG_SEARCH_URL.format(query=quote(keyword.lower()))
    resp = _request_with_retry(url)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    seen_links = set()

    for a in soup.find_all("a", href=re.compile(r"/news-release/\d{4}/\d{2}/\d{2}/")):
        href = a.get("href", "")
        if href.startswith("/"):
            href = "https://www.globenewswire.com" + href
        if href in seen_links:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        seen_links.add(href)

        snippet = ""
        parent = a.find_parent(["li", "div", "article"])
        if parent:
            p = parent.find("p")
            if p:
                snippet = p.get_text(" ", strip=True)

        results.append({
            "keyword": keyword,
            "title": title,
            "description": snippet,
            "contributor": keyword,
            "link": href,
            "guid": href,
        })

    return results


def _text(elem, tag, ns=None):
    found = elem.find(tag, ns) if ns else elem.find(tag)
    return found.text.strip() if found is not None and found.text else ""


def _fetch_and_match_rss(url: str, has_contributor: bool = True):
    resp = _request_with_retry(url)
    if resp is None:
        return []

    root = ET.fromstring(resp.content)
    results = []

    for item in root.findall(".//item"):
        title = _text(item, "title")
        description = _text(item, "description")
        link = _text(item, "link")
        guid = _text(item, "guid") or link
        contributor = _text(item, "dc:contributor", NS) if has_contributor else ""

        haystack = f"{title} {description} {contributor}"

        matched_keyword = None
        for kw in KEYWORDS:
            if _matches_keyword(haystack, kw):
                matched_keyword = kw
                break
        if not matched_keyword:
            continue

        results.append({
            "keyword": matched_keyword,
            "title": title,
            "description": description,
            "contributor": contributor,
            "link": link,
            "guid": guid,
        })

    return results


def fetch_google_news_articles(keyword: str, max_items: int = 10):
    query = quote(f'"{keyword}"')
    url = GOOGLE_NEWS_URL.format(query=query)
    resp = _request_with_retry(url, max_retries=2, timeout=20)
    if resp is None:
        return []

    try:
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"[구글뉴스 파싱 실패] {keyword} ({e})")
        return []

    results = []
    count = 0
    for item in root.findall(".//item"):
        if count >= max_items:
            break
        title = _strip_html(_text(item, "title"))
        description = _strip_html(_text(item, "description"))
        link = _text(item, "link")
        guid = _text(item, "guid") or link

        if not title:
            continue
        count += 1

        results.append({
            "keyword": keyword,
            "title": title,
            "description": description,
            "contributor": "",
            "link": link,
            "guid": guid,
        })

    return results


def fetch_matching_articles():
    all_results = []
    seen_guids = set()

    for kw in KEYWORDS:
        org_items = fetch_org_articles(kw)
        print(f"[조직검색] '{kw}' → {len(org_items)}건")
        for item in org_items:
            if item["guid"] in seen_guids:
                continue
            seen_guids.add(item["guid"])
            all_results.append(item)

    ca_items = _fetch_and_match_rss(CLASS_ACTION_FEED_URL, has_contributor=True)
    print(f"[소송피드] → {len(ca_items)}건")
    for item in ca_items:
        if item["guid"] in seen_guids:
            continue
        seen_guids.add(item["guid"])
        all_results.append(item)

    bw_items = _fetch_and_match_rss(BUSINESSWIRE_FEED_URL, has_contributor=False)
    print(f"[Business Wire] → {len(bw_items)}건")
    for item in bw_items:
        if item["guid"] in seen_guids:
            continue
        seen_guids.add(item["guid"])
        all_results.append(item)

    for kw in KEYWORDS:
        gn_items = fetch_google_news_articles(kw)
        print(f"[구글뉴스] '{kw}' → {len(gn_items)}건")
        for item in gn_items:
            if item["guid"] in seen_guids:
                continue
            seen_guids.add(item["guid"])
            all_results.append(item)

    return all_results


if __name__ == "__main__":
    for a in fetch_matching_articles():
        print(f"[{a['keyword']}] {a['title']}\n  {a['link']}\n")

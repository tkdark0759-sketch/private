"""
세 가지 소스를 조합해서 기사를 찾는 모듈:
1) GlobeNewswire 조직 검색 - 회사 자체 뉴스를 정확하게 (전체 기록, 오탐 없음)
2) GlobeNewswire Class Action 피드 - 소송/공지(제3자 언급)를 단어경계 매칭으로
3) Business Wire 전체 피드 - 단어경계 매칭으로 (Palantir 등 GlobeNewswire를 안 쓰는 회사 커버용)
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
NS = {"dc": "http://dublincore.org/documents/dcmi-namespace/"}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsAlertBot/1.0)"}


def _matches_keyword(haystack: str, keyword: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(keyword) + r"(?![A-Za-z0-9])"
    return re.search(pattern, haystack, re.IGNORECASE) is not None


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


def fetch_matching_articles():
    all_results = []
    seen_guids = set()

    for kw in KEYWORDS:
        for item in fetch_org_articles(kw):
            if item["guid"] in seen_guids:
                continue
            seen_guids.add(item["guid"])
            all_results.append(item)

    for item in _fetch_and_match_rss(CLASS_ACTION_FEED_URL, has_contributor=True):
        if item["guid"] in seen_guids:
            continue
        seen_guids.add(item["guid"])
        all_results.append(item)

    for item in _fetch_and_match_rss(BUSINESSWIRE_FEED_URL, has_contributor=False):
        if item["guid"] in seen_guids:
            continue
        seen_guids.add(item["guid"])
        all_results.append(item)

    return all_results


if __name__ == "__main__":
    for a in fetch_matching_articles():
        print(f"[{a['keyword']}] {a['title']}\n  {a['link']}\n")

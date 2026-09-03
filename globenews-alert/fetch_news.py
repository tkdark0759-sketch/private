"""
두 가지 방식을 조합해서 기사를 찾는 모듈:
1) 회사 자체 뉴스 - GlobeNewswire "조직 검색" 페이지를 직접 조회
   (전체 기록에서 정확한 회사명으로 검색되므로, 오탐도 없고 놓치는 것도 없음)
2) 소송/공지(제3자가 그 회사를 언급하는 경우) - "Class Action" 카테고리 피드에서
   단어 경계를 지켜서 키워드 매칭
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
    url = ORG_SEARCH_URL.format(query=quote(keyword))
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


def fetch_class_action_matches():
    resp = _request_with_retry(CLASS_ACTION_FEED_URL)
    if resp is None:
        return []

    root = ET.fromstring(resp.content)
    results = []

    for item in root.findall(".//item"):
        title = _text(item, "title")
        description = _text(item, "description")
        link = _text(item, "link")
        guid = _text(item, "guid") or link
        contributor = _text(item, "dc:contributor", NS)

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

    for item in fetch_class_action_matches():
        if item["guid"] in seen_guids:
            continue
        seen_guids.add(item["guid"])
        all_results.append(item)

    return all_results


if __name__ == "__main__":
    for a in fetch_matching_articles():
        print(f"[{a['keyword']}] {a['title']}\n  {a['link']}\n")

"""
GlobeNewswire 공식 "Public Companies" RSS 피드(최근 20건)를 가져와서
keywords.py에 등록된 회사명이 제목/요약/기고자(dc:contributor)에 포함된
기사만 걸러내는 모듈.
"""
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from keywords import KEYWORDS

FEED_URL = "https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/GlobeNewswire%20-%20News%20about%20Public%20Companies"
NS = {"dc": "http://dublincore.org/documents/dcmi-namespace/"}


def _text(elem, tag, ns=None):
    found = elem.find(tag, ns) if ns else elem.find(tag)
    return found.text.strip() if found is not None and found.text else ""


def fetch_matching_articles():
    resp = requests.get(FEED_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    results = []
    for item in root.findall(".//item"):
        title = _text(item, "title")
        description = _text(item, "description")
        link = _text(item, "link")
        guid = _text(item, "guid") or link
        pub_date_raw = _text(item, "pubDate")
        contributor = _text(item, "dc:contributor", NS)

        haystack = f"{title} {description} {contributor}".lower()

        matched_keyword = None
        for kw in KEYWORDS:
            if kw.lower() in haystack:
                matched_keyword = kw
                break
        if not matched_keyword:
            continue

        try:
            published_dt = parsedate_to_datetime(pub_date_raw)
        except Exception:
            published_dt = None

        results.append({
            "keyword": matched_keyword,
            "title": title,
            "description": description,
            "contributor": contributor,
            "link": link,
            "guid": guid,
            "published": published_dt,
        })

    return results


if __name__ == "__main__":
    for a in fetch_matching_articles():
        print(f"[{a['keyword']}] {a['title']} ({a['contributor']})\n  {a['link']}\n")

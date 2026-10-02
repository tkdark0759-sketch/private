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

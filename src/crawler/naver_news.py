"""
naver_news.py
네이버 뉴스 검색 API를 통해 어제 날짜 기사를 수집합니다.
API 문서: https://developers.naver.com/docs/serviceapi/search/news/news.md
"""

import logging
from dataclasses import dataclass

import requests

import config

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    url: str
    description: str
    pub_date: str
    source: str = "naver_news"


def _clean_html(text: str) -> str:
    """네이버 API 응답의 HTML 태그 및 이스케이프 제거"""
    import html
    import re
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def fetch_yesterday_articles() -> list[Article]:
    """
    아파트명 + 재건축 키워드 조합으로 네이버 뉴스를 검색하고
    KST 어제 날짜 기사만 필터링하여 반환합니다.
    """
    headers = {
        "X-Naver-Client-Id": config.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": config.NAVER_CLIENT_SECRET,
    }

    results: list[Article] = []
    seen_urls: set[str] = set()

    for keyword in config.SEARCH_KEYWORDS:
        query = f"{config.APARTMENT_NAME} {keyword}"
        params = {
            "query": query,
            "display": config.NAVER_DISPLAY,
            "start": 1,
            "sort": "date",  # 최신순 정렬
        }

        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/news.json",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                pub_date = item.get("pubDate", "")

                # 어제 날짜 기사만 통과
                if not config.is_yesterday_kst(pub_date):
                    continue

                url = item.get("originallink") or item.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                results.append(
                    Article(
                        title=_clean_html(item.get("title", "")),
                        url=url,
                        description=_clean_html(item.get("description", "")),
                        pub_date=pub_date,
                        source="naver_news",
                    )
                )

        except requests.RequestException as e:
            logger.error("네이버 뉴스 API 오류 [%s]: %s", query, e)

    logger.info("뉴스: %d건 수집 (어제 기사)", len(results))
    return results

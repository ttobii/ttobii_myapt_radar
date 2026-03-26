"""
naver_blog.py
네이버 블로그 검색 API를 통해 어제 날짜 포스트를 수집합니다.
API 문서: https://developers.naver.com/docs/serviceapi/search/blog/blog.md
"""

import logging
from dataclasses import dataclass

import requests

import config
from src.crawler.naver_news import Article, _clean_html

logger = logging.getLogger(__name__)


def fetch_yesterday_articles() -> list[Article]:
    """
    아파트명 + 재건축 키워드 조합으로 네이버 블로그를 검색하고
    KST 어제 날짜 포스트만 필터링하여 반환합니다.
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
            "sort": "date",
        }

        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/blog.json",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                pub_date = item.get("postdate", "")  # 블로그는 'postdate' 필드 (YYYYMMDD)

                # 블로그 API는 날짜 포맷이 다름: '20260324'
                if not _is_yesterday_blog_date(pub_date):
                    continue

                url = item.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                results.append(
                    Article(
                        title=_clean_html(item.get("title", "")),
                        url=url,
                        description=_clean_html(item.get("description", "")),
                        pub_date=pub_date,
                        source="naver_blog",
                    )
                )

        except requests.RequestException as e:
            logger.error("네이버 블로그 API 오류 [%s]: %s", query, e)

    logger.info("블로그: %d건 수집 (어제 기사)", len(results))
    return results


def _is_yesterday_blog_date(date_str: str) -> bool:
    """
    블로그 API의 날짜 포맷(YYYYMMDD)이 KST 어제인지 확인합니다.
    예: '20260324'
    """
    yesterday = config.get_yesterday_str(fmt="%Y%m%d")
    return date_str == yesterday

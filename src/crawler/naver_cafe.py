"""
naver_cafe.py
네이버 카페 검색 API를 통해 어제 날짜 게시글을 수집합니다.
API 문서: https://developers.naver.com/docs/serviceapi/search/cafe-article/cafe-article.md

참고: 카페 검색 API는 네이버 검색 API 중 'cafearticle' 타입을 사용합니다.
      일부 비공개 카페 글은 URL 접근이 제한될 수 있습니다.
"""

import logging

import requests

import config
from src.crawler.naver_news import Article, _clean_html

logger = logging.getLogger(__name__)


def fetch_yesterday_articles() -> list[Article]:
    """
    아파트명 + 재건축 키워드 조합으로 네이버 카페를 검색하고
    KST 어제 날짜 게시글만 필터링하여 반환합니다.
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
                "https://openapi.naver.com/v1/search/cafearticle.json",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                pub_date = item.get("postdate", "")  # 카페도 YYYYMMDD 포맷

                if not _is_yesterday_cafe_date(pub_date):
                    continue

                url = item.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # 카페명 추출 (cafename 필드)
                cafe_name = item.get("cafename", "")
                title = _clean_html(item.get("title", ""))
                if cafe_name:
                    title = f"[{cafe_name}] {title}"

                results.append(
                    Article(
                        title=title,
                        url=url,
                        description=_clean_html(item.get("description", "")),
                        pub_date=pub_date,
                        source="naver_cafe",
                    )
                )

        except requests.RequestException as e:
            logger.error("네이버 카페 API 오류 [%s]: %s", query, e)

    logger.info("카페: %d건 수집 (어제 기사)", len(results))
    return results


def _is_yesterday_cafe_date(date_str: str) -> bool:
    """
    카페 API의 날짜 포맷(YYYYMMDD)이 KST 어제인지 확인합니다.
    """
    yesterday = config.get_yesterday_str(fmt="%Y%m%d")
    return date_str == yesterday

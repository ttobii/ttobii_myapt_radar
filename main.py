"""
main.py
apt-radar 진입점.

GitHub Actions에서 `python main.py`로 직접 실행됩니다.
스케줄링은 GitHub Actions cron이 담당하므로 이 파일에는 없습니다.

실행 순서:
  1. 뉴스 / 블로그 / 카페에서 어제 기사 수집
  2. 중복 URL 제거
  3. Claude API로 요약 생성
  4. 텔레그램 발송
"""

import logging
import sys

import config
from src.crawler import naver_blog, naver_cafe, naver_news
from src.crawler.naver_news import Article
from src.notifier import telegram_bot
from src.processor import summarizer

# ── 로깅 설정 ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def deduplicate(articles: list[Article]) -> list[Article]:
    """여러 소스에서 수집된 기사의 URL 중복을 제거합니다."""
    seen: set[str] = set()
    unique: list[Article] = []
    for article in articles:
        if article.url not in seen:
            seen.add(article.url)
            unique.append(article)
    return unique


def main() -> None:
    yesterday = config.get_yesterday_str()
    logger.info("=== apt-radar 실행 시작 | 대상: %s | 날짜: %s ===",
                config.APARTMENT_NAME, yesterday)

    # ── 1. 크롤링 ──────────────────────────────────────────────
    try:
        news_articles    = naver_news.fetch_yesterday_articles()
        blog_articles    = naver_blog.fetch_yesterday_articles()
        cafe_articles    = naver_cafe.fetch_yesterday_articles()
    except Exception as e:
        logger.exception("크롤링 중 예외 발생")
        telegram_bot.send_error_alert(f"크롤링 실패: {e}")
        sys.exit(1)

    all_articles = deduplicate(news_articles + blog_articles + cafe_articles)

    logger.info(
        "수집 완료 | 뉴스: %d건, 블로그: %d건, 카페: %d건 → 중복 제거 후 총 %d건",
        len(news_articles), len(blog_articles), len(cafe_articles), len(all_articles),
    )

    # ── 2. 요약 ────────────────────────────────────────────────
    try:
        message = summarizer.summarize(all_articles)
    except Exception as e:
        logger.exception("요약 생성 중 예외 발생: %s", e)
        alert_sent = telegram_bot.send_error_alert(f"[요약 실패] {type(e).__name__}: {e}")
        if not alert_sent:
            logger.error("텔레그램 오류 알림 발송도 실패했습니다. 에러 내용: %s", e)
        sys.exit(1)

    # ── 3. 텔레그램 발송 ───────────────────────────────────────
    success = telegram_bot.send_message(message)

    if success:
        logger.info("=== 발송 완료 ===")
    else:
        logger.error("텔레그램 발송 실패")
        alert_sent = telegram_bot.send_error_alert("[발송 실패] 요약 메시지 텔레그램 전송에 실패했습니다.")
        if not alert_sent:
            logger.error("텔레그램 오류 알림 발송도 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()

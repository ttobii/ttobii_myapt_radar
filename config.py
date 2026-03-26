"""
config.py
환경변수를 읽어 전역 설정값으로 제공합니다.
GitHub Actions에서는 Secrets로 주입되고,
로컬에서는 .env 파일을 통해 로드됩니다.
"""

import os
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv

# 로컬 실행 시 .env 파일 자동 로드 (GitHub Actions 환경에서는 무시됨)
load_dotenv()


# ── 아파트 설정 ───────────────────────────────────────────────
APARTMENT_NAME: str = os.environ["APARTMENT_NAME"]  # 예: "은마아파트", "잠실주공5단지"

# ── 네이버 Search API ─────────────────────────────────────────
NAVER_CLIENT_ID: str = os.environ["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET: str = os.environ["NAVER_CLIENT_SECRET"]

# ── Claude API ────────────────────────────────────────────────
CLAUDE_API_KEY: str = os.environ["CLAUDE_API_KEY"]
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")

# ── 텔레그램 ──────────────────────────────────────────────────
TELEGRAM_TOKEN: str = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID: str = os.environ["TELEGRAM_CHAT_ID"]

# ── 검색 설정 ─────────────────────────────────────────────────
# 재건축 관련 추가 키워드 (아파트명과 AND 조합으로 검색)
SEARCH_KEYWORDS: list[str] = [
    "재건축",
    "재건축 추진",
    "재건축 심의",
    "재건축 사업",
    "안전진단",
    "정비구역",
    "조합설립",
]

# 네이버 API 한 번 요청당 가져올 결과 수 (최대 100)
NAVER_DISPLAY: int = 10


# ── 날짜 유틸 ─────────────────────────────────────────────────
KST = pytz.timezone("Asia/Seoul")


def get_yesterday_kst() -> datetime:
    """KST 기준 어제 날짜의 datetime 객체를 반환합니다."""
    now_kst = datetime.now(KST)
    return now_kst - timedelta(days=1)


def get_yesterday_str(fmt: str = "%Y-%m-%d") -> str:
    """KST 기준 어제 날짜를 지정한 포맷의 문자열로 반환합니다."""
    return get_yesterday_kst().strftime(fmt)


def is_yesterday_kst(date_str: str) -> bool:
    """
    주어진 날짜 문자열이 KST 어제 날짜인지 확인합니다.
    네이버 API pubDate 포맷 예: 'Mon, 24 Mar 2026 09:00:00 +0900'
    """
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        dt_kst = dt.astimezone(KST)
        yesterday = get_yesterday_kst()
        return dt_kst.date() == yesterday.date()
    except Exception:
        return False

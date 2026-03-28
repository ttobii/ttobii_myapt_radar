"""
telegram_bot.py
텔레그램 Bot API를 통해 메시지를 발송합니다.
python-telegram-bot 라이브러리 대신 requests로 직접 호출하여
비동기 의존성을 최소화합니다.
"""

import logging

import requests

import config

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def send_message(text: str) -> bool:
    """
    텔레그램 채팅(또는 채널)에 메시지를 발송합니다.

    Args:
        text: 발송할 메시지 텍스트 (MarkdownV2 미사용, 일반 텍스트)

    Returns:
        발송 성공 여부
    """
    url = TELEGRAM_API_BASE.format(token=config.TELEGRAM_TOKEN, method="sendMessage")

    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        # parse_mode 제거: 뉴스 제목 등에 포함된 &, *, _ 등 특수문자가
        # Telegram의 Markdown→HTML 변환 과정에서 파싱 오류를 유발할 수 있음
        "disable_web_page_preview": False,  # 링크 미리보기 활성화
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()

        if result.get("ok"):
            logger.info("텔레그램 발송 성공 (message_id: %s)", result["result"]["message_id"])
            return True
        else:
            logger.error("텔레그램 발송 실패: %s", result.get("description"))
            return False

    except requests.RequestException as e:
        logger.error("텔레그램 API 요청 오류: %s", e)
        return False


def send_error_alert(error_msg: str) -> bool:
    """
    실행 중 예외 발생 시 오류 내용을 텔레그램으로 알립니다.
    Markdown 파싱 오류를 방지하기 위해 parse_mode 없이 plain text로 발송합니다.

    Returns:
        발송 성공 여부
    """
    text = (
        f"⚠️ apt-radar 오류 발생\n\n"
        f"{error_msg[:500]}"  # 너무 긴 오류 메시지 자르기
    )
    url = TELEGRAM_API_BASE.format(token=config.TELEGRAM_TOKEN, method="sendMessage")
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        # parse_mode 제거: 에러 메시지에 `, *, _ 등 특수문자가 포함될 수 있어
        # Markdown 파싱 시 400 오류 발생 가능성이 있음
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("오류 알림 텔레그램 발송 성공")
        return True
    except Exception:
        logger.exception("오류 알림 발송도 실패했습니다.")
        return False

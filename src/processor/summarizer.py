"""
summarizer.py
수집된 기사 목록을 Claude API에 전달하여
재건축 관련 핵심 요약과 출처 링크를 생성합니다.
"""

import logging

import anthropic

import config
from src.crawler.naver_news import Article

logger = logging.getLogger(__name__)

# 분할 발송은 telegram_bot.py 에서 처리하므로 여기서는 길이 제한 없음


def summarize(articles: list[Article]) -> str:
    """
    기사 목록을 Claude API로 요약하여 텔레그램 발송용 문자열을 반환합니다.
    기사가 없으면 '소식 없음' 메시지를 반환합니다.
    """
    yesterday = config.get_yesterday_str()

    if not articles:
        return (
            f"🏢 {config.APARTMENT_NAME} 재건축 레이더\n"
            f"📅 {yesterday}\n\n"
            f"어제 새로운 재건축 관련 소식이 없었습니다."
        )

    # Claude에게 전달할 기사 텍스트 조합
    articles_text = _format_articles_for_prompt(articles)

    client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

    prompt = f"""다음은 '{config.APARTMENT_NAME}' 재건축과 관련하여 {yesterday}에 게재된 뉴스/블로그/카페 글들입니다.

{articles_text}

재건축에 대한 용어 정리 
위 내용을 바탕으로 아래 형식에 맞게 한국어로 요약해 주세요:

1. **핵심 요약**: 어제 가장 중요한 재건축 관련 업데이트를 2~4문장으로 간결하게 정리
2. **주요 내용**: 각 기사의 핵심 포인트를 bullet point로 정리 (기사당 1~2줄)
3. **출처**: 각 기사 제목과 URL을 목록으로 나열

재건축과 직접 관련 없는 내용은 제외하고, 실제 진행 상황(안전진단, 조합 설립, 심의 결과 등)에 집중해 주세요.
텔레그램 메시지 형식으로 작성하되, 마크다운은 최소화하고 이모지를 적절히 활용해 주세요.
"""

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        summary_body = message.content[0].text.strip()
    except anthropic.APIError as e:
        logger.error("Claude API 오류: %s", e)
        # API 실패 시 원본 기사 목록을 그대로 발송
        summary_body = _fallback_summary(articles)
    except Exception as e:
        # anthropic.APIError 외의 예외 (TypeError, 인증 오류 등) 처리
        logger.error("Claude API 호출 중 예상치 못한 오류: %s", e)
        summary_body = _fallback_summary(articles)

    header = (
        f"🏢 {config.APARTMENT_NAME} 재건축 레이더\n"
        f"📅 {yesterday} 업데이트\n"
        f"{'─' * 20}\n\n"
    )

    full_message = header + summary_body

    return full_message


def _format_articles_for_prompt(articles: list[Article]) -> str:
    """Claude 프롬프트용 기사 텍스트 포맷"""
    lines = []
    for i, a in enumerate(articles, 1):
        source_label = {"naver_news": "뉴스", "naver_blog": "블로그", "naver_cafe": "카페"}.get(
            a.source, a.source
        )
        lines.append(
            f"[{i}] ({source_label}) {a.title}\n"
            f"    날짜: {a.pub_date}\n"
            f"    내용: {a.description}\n"
            f"    링크: {a.url}\n"
        )
    return "\n".join(lines)


def _fallback_summary(articles: list[Article]) -> str:
    """Claude API 실패 시 기본 포맷으로 기사 목록 반환"""
    lines = ["⚠️ AI 요약에 실패하여 원문 목록을 전달합니다.\n"]
    for a in articles:
        lines.append(f"• {a.title}\n  {a.url}\n")
    return "\n".join(lines)

# apt-radar — CLAUDE.md

AI 어시스턴트가 이 프로젝트를 파악할 때 가장 먼저 읽어야 할 파일입니다.

---

## 프로젝트 목적

특정 아파트 단지의 **재건축 관련 최신 소식**을 매일 자동으로 수집·요약하여 텔레그램으로 전달하는 자동화 파이프라인입니다.

- 평일(월~금) 오전 9시(KST)에 GitHub Actions가 자동 실행
- 네이버 뉴스·블로그·카페에서 **어제 날짜** 기사만 수집 (별도 상태 저장 없음)
- Claude API로 핵심 내용을 요약하고 출처 링크와 함께 텔레그램으로 발송
- 새로운 소식이 없을 때도 "소식 없음" 메시지를 발송하여 정상 동작 여부 확인 가능

---

## 기술 스택

| 역할 | 선택 |
|---|---|
| 스케줄링 | GitHub Actions cron (`0 0 * * 1-5`) |
| 웹 크롤링 | 네이버 Search API (뉴스·블로그·카페) |
| AI 요약 | Anthropic Claude API (`claude-opus-4-6`) |
| 알림 발송 | 텔레그램 Bot API (직접 HTTP 호출) |
| 시크릿 관리 | GitHub Secrets → 런타임 환경변수 주입 |
| 의존성 | `anthropic`, `requests`, `pytz`, `python-dotenv` |

---

## 디렉토리 구조

```
apt-radar/
├── .github/
│   └── workflows/
│       └── daily_check.yml   # GitHub Actions 워크플로우 (cron + secrets 주입)
│
├── src/
│   ├── crawler/
│   │   ├── naver_news.py     # 네이버 뉴스 API → 어제 기사 수집
│   │   ├── naver_blog.py     # 네이버 블로그 API → 어제 포스트 수집
│   │   └── naver_cafe.py     # 네이버 카페 API → 어제 게시글 수집
│   │
│   ├── processor/
│   │   └── summarizer.py     # Claude API로 요약 생성 + 소식 없음 처리
│   │
│   └── notifier/
│       └── telegram_bot.py   # 텔레그램 발송 + 오류 알림
│
├── main.py                   # 진입점: 수집 → 중복제거 → 요약 → 발송
├── config.py                 # 환경변수 파싱 + KST 날짜 유틸
├── requirements.txt
├── .env.example              # 로컬 테스트용 환경변수 템플릿
├── .gitignore                # .env 커밋 방지 포함
└── CLAUDE.md                 # 이 파일
```

---

## 실행 흐름

```
GitHub Actions (평일 UTC 00:00 = KST 09:00)
  │
  ├─ 1. config.py: KST 어제 날짜 계산
  │
  ├─ 2. crawler: 뉴스 + 블로그 + 카페 병렬 수집
  │       └─ 각 소스에서 "어제 날짜" 기사만 반환
  │
  ├─ 3. main.py: URL 기준 중복 제거
  │
  ├─ 4. summarizer.py: Claude API 호출
  │       ├─ 기사 있음 → 핵심 요약 + 출처 링크 생성
  │       └─ 기사 없음 → "소식 없음" 메시지 생성
  │
  └─ 5. telegram_bot.py: 텔레그램 발송
          └─ 실패 시 오류 내용도 텔레그램으로 알림
```

---

## 중복 방지 전략

**별도 저장소(DB·파일)를 사용하지 않습니다.**
네이버 API 쿼리 시 **어제 날짜**로 범위를 고정하는 방식으로 중복을 구조적으로 차단합니다.

- 뉴스/카페: `pubDate` 또는 `postdate` 필드를 `config.is_yesterday_kst()` / `_is_yesterday_*_date()` 로 필터
- 여러 소스에서 동일 URL이 수집될 경우 `main.py`의 `deduplicate()` 에서 제거
- GitHub Actions 환경이 매 실행마다 초기화되어도 동일 결과 보장 (멱등성)

---

## GitHub Secrets 목록

| 이름 | 용도 |
|---|---|
| `APARTMENT_NAME` | 검색 대상 아파트 단지명 (예: `은마아파트`) |
| `NAVER_CLIENT_ID` | 네이버 개발자센터 앱 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 개발자센터 앱 Client Secret |
| `CLAUDE_API_KEY` | Anthropic Console API 키 |
| `TELEGRAM_TOKEN` | @BotFather 발급 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 메시지 수신 채팅/채널 ID |

모든 키는 코드에 직접 기재하지 않으며, 환경변수로만 접근합니다.
`config.py`에서 `os.environ["KEY_NAME"]` 방식으로 읽어 누락 시 즉시 오류가 발생합니다.

---

## 로컬 테스트 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 파일 생성
cp .env.example .env
# .env 파일에 실제 키 값 입력

# 3. 실행
python main.py
```

GitHub Actions의 `workflow_dispatch` 트리거로 수동 실행도 가능합니다.

---

## 검색 키워드 설정

`config.py`의 `SEARCH_KEYWORDS` 리스트에서 관리합니다.
아파트명과 각 키워드를 AND 조합으로 검색합니다.

```python
SEARCH_KEYWORDS = [
    "재건축",
    "재건축 추진",
    "재건축 심의",
    "재건축 사업",
    "안전진단",
    "정비구역",
    "조합설립",
]
```

키워드 추가·삭제는 이 리스트만 수정하면 모든 크롤러에 자동 반영됩니다.

---

## 향후 기능 추가 시 참고사항

**새 크롤링 소스 추가**
`src/crawler/` 아래 새 모듈을 만들고 `fetch_yesterday_articles() -> list[Article]` 인터페이스를 맞춰 구현합니다.
`Article` 데이터클래스는 `naver_news.py`에 정의되어 있습니다.
`main.py`에서 import 후 결과 리스트에 추가합니다.

**요약 프롬프트 수정**
`src/processor/summarizer.py`의 `prompt` 변수를 수정합니다.

**발송 채널 추가 (이메일 등)**
`src/notifier/` 아래 새 모듈을 추가하고 `main.py`에서 호출합니다.

**모니터링 대상 아파트 변경**
GitHub Secrets의 `APARTMENT_NAME` 값만 변경하면 코드 수정 없이 적용됩니다.

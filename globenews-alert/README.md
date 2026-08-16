# GlobeNewswire 키워드 알리미 (완전 무료 · 한국어 요약 · 이메일)

매일 아침 8시(한국시간), GlobeNewswire에서 등록해둔 회사명이 포함된
최근 24시간 이내 보도자료를 찾아 **한국어로 요약**해서 이메일로 보내주는 자동화 스크립트입니다.
**전부 무료 도구로만 구성되어 있어서 별도 비용이 들지 않습니다.**

## 파일 구성
- `keywords.py` — 추적할 회사명/키워드 목록 (여기만 수정하면 됨)
- `fetch_news.py` — GlobeNewswire RSS에서 기사 수집·필터링 + 원문 본문 가져오기
- `summarize.py` — 무료 요약(sumy) + 무료 번역(구글 번역, deep-translator)
- `send_email.py` — Gmail로 결과 발송 (무료)
- `main.py` — 전체를 묶어서 실행하는 진입점
- `.github/workflows/daily.yml` — 매일 자동 실행 스케줄 (GitHub Actions, 무료)

## 왜 무료인가
- **GitHub Actions**: 개인 저장소 기준 매달 2,000분까지 무료 (이 스크립트는 실행마다 1~2분 정도만 씀 → 매일 돌려도 한 달에 30~60분 정도라 여유 있음)
- **요약**: sumy 라이브러리가 서버 호출 없이 로컬(GitHub Actions 안)에서 알고리즘으로 핵심 문장을 추출 — API 키/과금 없음
- **번역**: deep-translator가 구글 번역 웹페이지를 무료로 이용 (비공식 방식이라 가끔 실패할 수 있지만 기본적으로 무료)
- **이메일**: Gmail SMTP는 개인 사용 무료

## 참고: 무료 버전의 한계
- Claude 같은 AI가 "새로 문장을 만들어서" 요약하는 게 아니라, **원문에서 중요해 보이는 문장 3개를 그대로 뽑아 번역**하는 방식이에요.
  그래서 문장이 좀 딱딱하거나, 앞뒤 맥락이 부드럽게 안 이어질 수 있어요 (AI 요약보다는 품질이 낮음).
- 무료 구글 번역(비공식)은 가끔 요청이 막히거나 번역이 실패할 수 있어요. 실패하면 영어 원문이라도 그대로 보여줍니다.
- 나중에 품질을 높이고 싶으시면, `summarize.py`를 Claude API 버전으로 바꿀 수 있어요 (사용량이 적으면 한 달 몇백 원 수준입니다). 필요하시면 말씀해주세요.

## 설정 순서 (딱 2가지만 준비하면 됩니다)

### 1. Gmail 앱 비밀번호 발급
1. Google 계정에 2단계 인증 켜기 (계정 관리 > 보안)
2. https://myaccount.google.com/apppasswords 에서 앱 비밀번호 발급 (16자리)

### 2. GitHub 저장소 만들기 + Secrets 등록
1. github.com에서 무료 계정 만들기 (이미 있으면 생략)
2. 새 저장소 생성 (Private 권장)
3. 이 폴더 안의 모든 파일(`.github` 폴더 포함)을 그 저장소에 업로드
4. 저장소 Settings > Secrets and variables > Actions > "New repository secret"에서 등록:

| Secret 이름 | 값 |
|---|---|
| `GMAIL_ADDRESS` | 보내는 사람 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | 1번에서 발급받은 16자리 앱 비밀번호 |
| `ALERT_TO_EMAIL` | 받을 이메일 주소 (비워두면 GMAIL_ADDRESS 본인에게 발송) |

### 3. 동작 확인
저장소 > Actions 탭 > "Daily GlobeNewswire Alert" 워크플로 선택 > "Run workflow" 버튼으로
수동 실행해서 이메일이 잘 오는지 먼저 테스트해보세요.

문제없이 오면, 이후로는 매일 한국시간 오전 8시에 자동으로 실행됩니다.

## 참고 및 주의사항
- **본문 수집 실패 가능성**: GlobeNewswire 페이지 구조가 바뀌거나 접근이 막히면 본문을 못 가져올 수 있어요.
  이 경우 메일에 "(본문 수집에 실패해 요약을 생략합니다)"라고 표시되고 원문 링크는 정상적으로 옵니다.
- **키워드 매칭**: 검색은 회사명 철자에 민감할 수 있어요. 결과가 잘 안 잡히면
  `keywords.py`에 티커(예: "IREN")와 정식 회사명(예: "AbCellera")을 둘 다 등록해보세요.
- **요약 문장 개수 조절**: `summarize.py`의 `SENTENCE_COUNT` 값을 바꾸면 추출되는 핵심 문장 개수를
  조절할 수 있어요 (기본 3개).

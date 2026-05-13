# ICE_Updater

> 공지사항을 모니터링하여 Telegram으로 알림을 전송하는 자동화 봇

## Overview

대학 홈페이지의 공지사항을 수시로 확인해야 하는 불편함을 해소하기 위해 개발한 자동화 알림 시스템입니다. 
여러 웹사이트를 주기적으로 크롤링하여 새로운 게시글을 감지하고, Google Sheets에 데이터를 저장하며, Telegram을 통해 즉시 알림을 전송합니다.

## Key Features

- **다중 소스 모니터링**: 정보통신공학전공, 컴퓨터학부, SW 사업단, 영대소식 등 6개 소스 동시 모니터링
- **비동기 병렬 처리**: asyncio를 활용한 효율적인 병렬 크롤링 및 데이터 처리
- **스마트 데이터 비교**: Google Sheets 기반 데이터 관리로 신규/변경 게시글 감지
- **실시간 알림**: Telegram Bot API를 통한 즉각적인 푸시 알림
- **서버리스 배포**: AWS Lambda 환경에서 실행 가능한 구조

## Tech Stack

**Language & Framework**
- Python 3.x, asyncio

**Web Scraping**
- aiohttp, BeautifulSoup4

**Data Management**
- Google Sheets API (gspread-asyncio)

**Notification**
- Telegram Bot API

**Deployment**
- AWS Lambda (Serverless)

## Architecture

```
┌─────────────┐
│   Scheduler │ ──┐
└─────────────┘   │
                  ├──► Parser ──► DataProcess ──► Message ──► Telegram
┌─────────────┐   │                    ▲
│  Websites   │ ──┘                    │
│  (6 sources)│                   Google Sheets
└─────────────┘                  (Data Storage)
```

### Workflow

1. **비동기 크롤링**: 6개 웹사이트에서 공지사항 및 게시글 데이터를 병렬로 수집
2. **데이터 비교**: Google Sheets에 저장된 기존 데이터와 비교하여 변경사항 감지
3. **필터링**: 신규 게시글 및 수정된 게시글만 선별
4. **알림 전송**: 선별된 데이터를 Telegram 메시지로 포맷팅하여 전송
5. **데이터 갱신**: Google Sheets에 최신 데이터 저장

## Technical Highlights

### 1. 비동기 병렬 처리
```python
# 6개 소스의 크롤링, 데이터 조회, 비교를 모두 비동기 병렬로 처리
result = await asyncio.gather(
    parser.parser('anno', ICE_URL),
    parser.parser('article', ICE_URL),
    parser.parser('anno', COMPUTER_URL),
    # ... 
)
```

### 2. 유연한 파싱 시스템
- 각 웹사이트의 구조에 맞춘 커스텀 파서 구현
- 공지사항, 일반 게시글, 뉴스 등 다양한 타입 지원

### 3. 중복 감지
- 제목 및 URL 기반 중복 체크
- 수정된 게시글도 감지하여 알림 전송

### 4. 멀티 채널 알림
- 메인 채팅방과 서브 채팅방에 동시 메시지 전송
- 구조화된 메시지 포맷 제공

## Project Structure

```
├── main.py          # 메인 스케줄러 및 워크플로우 관리
├── parser.py        # 웹 크롤링 및 HTML 파싱
├── dataIo.py        # Google Sheets 입출력
├── dataProcess.py   # 데이터 비교 및 필터링 로직
└── msg.py           # Telegram 메시지 생성 및 전송
```

## Performance

- **병렬 처리**: 6개 소스를 순차적으로 처리할 경우 약 6초 소요 → 비동기 병렬 처리로 약 1-2초로 단축
- **효율적인 API 사용**: Google Sheets API 호출 최소화로 할당량 내 안정적 운영
- **서버리스 아키텍처**: AWS Lambda를 통한 비용 효율적 운영

## Lessons Learned

- 비동기 프로그래밍 패턴 및 asyncio 활용 역량 향상
- 웹 크롤링 시 다양한 HTML 구조 파싱 경험
- API 연동 및 외부 서비스 통합 경험
- 서버리스 아키텍처 설계 및 배포 경험

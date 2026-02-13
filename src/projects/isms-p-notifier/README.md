# ISMS-P 자료실 새 글 알림

ISMS-P(한국인터넷진흥원) 자료실의 새 글이 올라오면 팝업 알림으로 알려주는 Python 크롤링 프로그램입니다.

## 주요 기능

- **자동 크롤링**: ISMS-P 자료실 주기적 확인 (기본 30분 간격)
- **새 글 알림**: 새 게시글 감지 시 팝업 알림 표시
- **소리 알림**: 알림과 함께 시스템 알림음 재생
- **중복 방지**: 이미 확인한 게시글은 저장하여 다시 알리지 않음
- **상세 내용**: 새 글의 상세 내용도 함께 확인

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 (선택)

`config.json` 파일에서 설정을 변경할 수 있습니다:

```json
{
  "target_urls": {
    "list_page": "https://isms-p.or.kr/ntcn/rcsrm/selectGnrlVrtlRcsrmList.do"
  },
  "check_interval_minutes": 30,
  "notification": {
    "enabled": true,
    "sound": true,
    "timeout_seconds": 10
  }
}
```

## 사용법

### 1회 실행 (테스트)

```bash
python main.py --once
```

### 주기적 실행 (데몬 모드)

```bash
python main.py
```

### 확인 간격 변경

```bash
# 10분마다 확인
python main.py --interval 10
```

### 디버그 모드

```bash
python main.py --debug
```

## macOS 설정

macOS에서 터미널 알림을 사용하려면 다음 권한이 필요합니다:

1. **시스템 설정 > 개인정보 보호 및 보안 > 알림**
2. 터미널 앱의 알림 권한 활성화

## Linux 설정

Linux에서는 `tkinter`가 필요합니다:

```bash
sudo apt-get install python3-tk
```

## 알림 예시

새 글이 감지되면 다음과 같은 알림이 표시됩니다:

```
┌─────────────────────────────────┐
│  새 글: 2025년 클라우드 보안...  │
├─────────────────────────────────┤
│  세미나 | 2025-06-02             │
│  (정보공유) 2025 SW 공급망       │
│  보안체계 진단 서비스 모집공고   │
│                                 │
│         [ 확인 ]                │
└─────────────────────────────────┘
```

## 파일 구조

```
isms-p-notifier/
├── main.py              # 메인 실행 파일
├── ism_p_crawler.py     # 크롤러 모듈
├── notifier.py          # 알림 모듈
├── storage.py           # 저장소 모듈
├── config.json          # 설정 파일
├── requirements.txt     # 의존성 목록
├── README.md            # 이 파일
├── seen_posts.json      # 확인한 게시글 저장 (자동 생성)
└── isms_p_notifier.log  # 로그 파일 (자동 생성)
```

## 백그라운드 실행

### macOS/Linux (nohup)

```bash
nohup python main.py > /dev/null 2>&1 &
```

### systemd 서비스 등록 (Linux)

`/etc/systemd/system/isms-p-notifier.service`:

```ini
[Unit]
Description=ISMS-P Notifier
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/isms-p-notifier
ExecStart=/usr/bin/python3 /path/to/isms-p-notifier/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable isms-p-notifier
sudo systemctl start isms-p-notifier
```

## 주의사항

- 너무 잦은 요청은 서버에 부담을 줄 수 있으니 확인 간격을 10분 이상으로 설정 권장
- 인증이 필요한 페이지는 크롤링할 수 없음
- 사이트 구조가 변경되면 크롤러 수정 필요

## 라이선스

MIT License

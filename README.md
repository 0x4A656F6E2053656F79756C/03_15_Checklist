# Checklist App - Google Calendar API 연동 가이드

이 문서는 데스크탑 할 일 관리 앱(Checklist App)과 Google Calendar 간의 양방향 동기화를 구현하기 위한 초기 설정 방법을 안내합니다.

## 1단계: Google Cloud Console 설정 및 API 사용 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속하여 로그인합니다.
2. 상단 메뉴에서 **[프로젝트 선택]**을 누르고 **[새 프로젝트]**를 생성합니다. (예: `Checklist-Calendar-Sync`)
3. 프로젝트가 생성되면 선택한 후, 왼쪽 메뉴에서 **[API 및 서비스] > [라이브러리]**로 이동합니다.
4. 검색창에 **"Google Calendar API"**를 검색하고 선택한 뒤 **[사용]** 버튼을 클릭합니다.

## 2단계: OAuth 동의 화면 구성

1. 왼쪽 메뉴에서 **[API 및 서비스] > [OAuth 동의 화면]**으로 이동합니다.
2. User Type을 **[외부(External)]**로 선택하고 **[만들기]**를 누릅니다. (Google Workspace 사용자라면 '내부' 선택 가능)
3. **앱 이름**(예: Checklist App), **사용자 지원 이메일**, **개발자 연락처 정보** 등 필수 항목만 입력하고 [저장 후 계속]을 누릅니다.
4. '범위(Scopes)' 단계는 그대로 두고 [저장 후 계속]을 누릅니다.
5. '테스트 사용자' 단계에서 **[사용자 추가]**를 누르고 본인의 구글 계정 이메일을 등록한 후 [저장 후 계속]을 누릅니다.

## 3단계: 사용자 인증 정보(Credentials) 발급

1. 왼쪽 메뉴에서 **[API 및 서비스] > [사용자 인증 정보]**로 이동합니다.
2. 상단의 **[+ 사용자 인증 정보 만들기] > [OAuth 클라이언트 ID]**를 선택합니다.
3. 애플리케이션 유형을 **[데스크톱 앱]**으로 선택하고, 이름(예: `Checklist Desktop Client`)을 입력한 뒤 **[만들기]**를 누릅니다.
4. 생성 완료 창이 뜨면 **[JSON 다운로드]** 버튼을 클릭합니다.
5. 다운로드한 파일의 이름을 `credentials.json`으로 변경한 뒤, **`checklist.py` 파일이 있는 동일한 폴더(루트 디렉토리)**에 저장합니다.

> **주의:** `credentials.json` 파일과 향후 생성될 `token.json` 파일은 개인 보안 정보이므로 Github 등에 절대 커밋하지 마세요. (`.gitignore`에 추가 필수)

## 4단계: 파이썬 환경 설정

터미널(또는 명령 프롬프트)을 열고 구글 API 통신을 위한 필수 파이썬 라이브러리를 설치합니다.

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
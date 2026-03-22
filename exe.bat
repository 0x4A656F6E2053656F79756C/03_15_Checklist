@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ===================================================
echo   Checklist App EXE 빌드를 시작합니다. (--onefile)
echo ===================================================

:: PyInstaller 설치 여부 확인 및 설치
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller가 설치되어 있지 않아 설치를 진행합니다...
    pip install pyinstaller
)

:: 이전 빌드 잔재 삭제 (깔끔한 빌드를 위해)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 빌드 명령 실행
:: --onefile: 파일 하나로 병합
:: --noconsole: 실행 시 검은색 터미널 창이 뜨지 않도록 설정 (GUI 전용)
:: --name: 생성될 exe 파일 이름 지정
:: --clean: 빌드 전 캐시 삭제
pyinstaller --noconsole --onefile --clean --name "MyChecklist" checklist.py

echo.
echo ===================================================
echo   빌드가 완료되었습니다! 
echo   dist 폴더 안의 MyChecklist.exe를 확인하세요.
echo ===================================================
pause
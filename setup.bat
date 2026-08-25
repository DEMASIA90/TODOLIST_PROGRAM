@echo off
setlocal
cd /d "%~dp0"

echo [1/2] PyQt6 설치
py -m pip install -r requirements.txt
if errorlevel 1 (
    python -m pip install -r requirements.txt
)

echo.
echo [2/2] 설치 완료
echo start_todo.bat을 실행하면 앱이 시작됩니다.
pause

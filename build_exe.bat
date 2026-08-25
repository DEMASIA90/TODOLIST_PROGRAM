@echo off
setlocal
cd /d "%~dp0"

py -m pip install pyinstaller PyQt6
if errorlevel 1 python -m pip install pyinstaller PyQt6

pyinstaller --noconfirm --clean --windowed --name AutoTodoDesktop main.py
if errorlevel 1 (
    echo 빌드 실패
    pause
    exit /b 1
)

echo.
echo EXE 생성 완료:
echo %~dp0dist\AutoTodoDesktop\AutoTodoDesktop.exe
echo.
echo 참고: PyInstaller 기본 onedir 구조이므로 dist\AutoTodoDesktop 폴더 전체를 유지하세요.
pause

@echo off
setlocal
cd /d "%~dp0"

if exist "dist\AutoTodoDesktop\AutoTodoDesktop.exe" (
    start "" "%~dp0dist\AutoTodoDesktop\AutoTodoDesktop.exe"
    exit /b 0
)

if exist "AutoTodoDesktop.exe" (
    start "" "%~dp0AutoTodoDesktop.exe"
    exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0main.py"
    exit /b 0
)

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw "%~dp0main.py"
    exit /b 0
)

echo Python launcher를 찾지 못했습니다.
echo setup.bat을 먼저 실행하거나 Python 3.10+를 설치하세요.
pause

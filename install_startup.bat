@echo off
setlocal
cd /d "%~dp0"

set "TARGET=%~dp0start_todo.bat"
set "LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AutoTodoDesktop.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%LINK%'); $sc.TargetPath = '%TARGET%'; $sc.WorkingDirectory = '%~dp0'; $sc.WindowStyle = 7; $sc.Save()"

if exist "%LINK%" (
    echo 시작프로그램 등록 완료:
    echo %LINK%
) else (
    echo 시작프로그램 등록 실패
)
pause

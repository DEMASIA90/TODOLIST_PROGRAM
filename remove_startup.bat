@echo off
setlocal
set "LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AutoTodoDesktop.lnk"
if exist "%LINK%" del /q "%LINK%"
echo 시작프로그램 등록을 제거했습니다.
pause

@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo Auto Todo Desktop - Windows standalone build
echo ==========================================

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 빌드 PC에는 Python이 필요합니다.
    echo 대상 PC에는 Python이 필요하지 않습니다.
    echo 로컬 빌드 대신 GitHub Actions를 사용하면 빌드 PC에도 설치할 필요가 없습니다.
    pause
    exit /b 1
)

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

if exist dist_onedir rmdir /s /q dist_onedir
if exist dist_portable rmdir /s /q dist_portable
if exist build_onedir rmdir /s /q build_onedir
if exist build_portable rmdir /s /q build_portable
if exist Output rmdir /s /q Output

echo.
echo [1/3] 설치형 payload 생성...
pyinstaller --noconfirm --clean --windowed --name AutoTodoDesktop --distpath dist_onedir --workpath build_onedir main.py
if errorlevel 1 goto :fail

echo.
echo [2/3] 단일 Portable EXE 생성...
pyinstaller --noconfirm --clean --windowed --onefile --name AutoTodoDesktop_Portable --distpath dist_portable --workpath build_portable main.py
if errorlevel 1 goto :fail

echo.
echo [3/3] Setup.exe 생성...
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo [ERROR] Inno Setup 6가 없습니다.
    echo https://jrsoftware.org/isdl.php 에서 설치 후 다시 실행하세요.
    echo 또는 GitHub Actions 자동 빌드를 사용하세요.
    pause
    exit /b 1
)

"%ISCC%" installer.iss
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo BUILD SUCCESS
echo 설치파일: Output\AutoTodoDesktop_Setup.exe
echo 포터블:   dist_portable\AutoTodoDesktop_Portable.exe
echo ==========================================
pause
exit /b 0

:fail
echo.
echo [ERROR] 빌드에 실패했습니다.
pause
exit /b 1

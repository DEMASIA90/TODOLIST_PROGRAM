# Auto Todo Desktop — Standalone Windows Edition

이 버전은 **설치 대상 PC에 Python / pip / PyQt6가 없어도 실행**할 수 있도록 빌드할 수 있습니다.

## 최종 사용자에게 줄 파일

### 1) 권장: 설치파일
`AutoTodoDesktop_Setup.exe`

- Python 설치 불필요
- PyQt6 설치 불필요
- pip 설치 불필요
- 필요한 Python Runtime / Qt DLL 포함
- 설치 중 `Windows 로그인 시 자동 실행`을 선택 가능
- 기본값은 자동 실행 사용
- 사용자 권한으로 `%LOCALAPPDATA%\Programs\AutoTodoDesktop`에 설치되므로 일반적으로 관리자 권한 불필요

### 2) 무설치 버전
`AutoTodoDesktop_Portable.exe`

- 파일 하나만 복사해서 실행
- Python 및 라이브러리 불필요
- 다만 Windows 시작프로그램 등록은 설치형보다 수동 관리가 필요

## GitHub Actions로 빌드 — 가장 간단한 방법

이 폴더 전체를 GitHub 저장소에 올리면 `.github/workflows/build-windows-installer.yml`이 Windows 서버에서 자동 빌드합니다.

1. GitHub 저장소에 파일 업로드/Push
2. 저장소의 `Actions` 탭 이동
3. `Build Windows Standalone Installer` 선택
4. `Run workflow`
5. 빌드 완료 후 Artifacts에서 아래 2개 다운로드
   - `AutoTodoDesktop-Windows-Installer`
   - `AutoTodoDesktop-Windows-Portable`

로컬 PC에 Python이나 Inno Setup을 설치하지 않아도 **GitHub 서버가 빌드**합니다.

## 로컬 Windows PC에서 직접 빌드

빌드 PC에만 아래가 필요합니다.

- Python 3.10+
- Inno Setup 6

`build_standalone_windows.bat` 실행

완료 결과:
- `Output\AutoTodoDesktop_Setup.exe`
- `dist_portable\AutoTodoDesktop_Portable.exe`

**설치 대상 PC에는 위 빌드 도구가 전혀 필요하지 않습니다.**

## 데이터 저장

사용자의 TODO DB는 프로그램 설치 폴더가 아니라:

`%LOCALAPPDATA%\AutoTodoDesktop\todo.db`

에 저장됩니다.

따라서 앱을 업데이트하거나 재설치해도 DB를 별도로 삭제하지 않는 한 기존 데이터가 유지됩니다.

## 자동 실행

설치파일에서는 `Windows 로그인 시 자동 실행`이 기본 선택되어 있습니다.

설치 완료 후에는 Windows 시작프로그램에 바로가기가 생성됩니다.
앱 창을 닫으면 시스템 트레이에서 계속 실행됩니다.

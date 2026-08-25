# Standalone 설치 지원

Python이 없는 PC용 배포 방법은 `README_STANDALONE.md`를 참고하세요.

# Auto Todo Desktop

Windows용 PyQt6 TODO / Project 런처입니다.

## 주요 기능

- 진행 중 / 완료 탭
- 할 일 추가, 수정, 삭제
- 시작일 기본값 = 오늘
- 마감일 및 D-Day 자동 계산
- 진척도 0~100% 업데이트
- 무제한 계층형 세부항목(Tree)
- 웹 URL / 로컬 파일 / 로컬 폴더 연결
- `Project 열기` 버튼으로 바로 실행
- 완료 처리 시 완료 탭으로 자동 이동
- 선택적으로 연결된 로컬 파일/폴더 자체를 지정한 완료 폴더로 실제 이동
- 완료 항목을 다시 진행 중으로 복원
- 검색
- 창을 닫으면 시스템 트레이에서 계속 실행
- Windows 로그인 시 자동 실행 등록 배치 포함
- 데이터는 `%LOCALAPPDATA%\AutoTodoDesktop\todo.db` 에 SQLite로 저장

## 처음 실행

1. Python 3.10 이상 설치
2. `setup.bat` 실행
3. `start_todo.bat` 실행

## Windows 시작 시 자동 실행

`install_startup.bat` 을 한 번 실행하세요.

해제하려면 `remove_startup.bat` 을 실행하세요.

## EXE로 빌드

`build_exe.bat` 실행 후:

`dist\AutoTodoDesktop\AutoTodoDesktop.exe`

가 생성됩니다. PyInstaller onedir 방식이므로 `dist\AutoTodoDesktop` 폴더 전체를 유지하세요.

## 실제 파일 자동 이동 기능 주의

할 일 편집 창에서:

`완료 시 연결된 로컬 파일/폴더를 완료 폴더로 이동`

을 체크하면 할 일을 완료할 때 실제 파일/폴더가 이동합니다.

이 옵션을 체크하지 않으면 파일 시스템에는 아무 변경도 하지 않고,
앱 내부에서만 항목이 `완료` 탭으로 이동합니다.

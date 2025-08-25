@echo off
chcp 65001 > nul
echo ========================================
echo 📄 마크다운 변환기 설치 및 실행 도구
echo ========================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python을 먼저 설치해주세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 설치 확인됨

REM Install required packages
echo.
echo 📦 필요한 패키지를 설치하는 중...
pip install -r requirements_python.txt
if errorlevel 1 (
    echo ⚠️ 일부 패키지 설치에 실패했지만 계속 진행합니다.
)

echo.
echo 🎯 사용 방법:
echo 1. 마크다운 파일을 이 폴더에 넣으세요
echo 2. 아래 명령어를 사용하세요:
echo.
echo    기본 사용: python markdown_converter_python.py your_file.md
echo    Pandoc 버전: python markdown_converter.py your_file.md
echo.
echo 📋 현재 폴더의 .md 파일들:
dir *.md /b 2>nul
if errorlevel 1 (
    echo    (현재 폴더에 .md 파일이 없습니다)
)

echo.
echo 💡 테스트 파일로 시작해보세요:
echo    python markdown_converter_python.py test_input.md
echo.
pause 
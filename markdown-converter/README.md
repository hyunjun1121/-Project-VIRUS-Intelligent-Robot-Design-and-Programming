# 📄 마크다운 변환기 (Markdown Converter)

LLM의 출력에서 자주 발생하는 이스케이프된 볼드 텍스트(`\*\*`)를 올바른 마크다운 볼드 텍스트(`**`)로 변환하고, 깔끔한 PDF와 DOCX 파일로 내보내는 도구입니다.

## 🎯 주요 기능

- **이스케이프 문제 해결**: `\*\*텍스트\*\*` → `**텍스트**`로 자동 변환
- **다양한 출력 형식**: PDF, DOCX 파일로 내보내기
- **한글 지원**: 한글 폰트 및 인코딩 완벽 지원
- **명령줄 인터페이스**: 간편한 CLI 도구
- **배치 처리**: 여러 파일 동시 처리 가능

## 🔧 설치 및 요구사항

### 1. Python 환경
- Python 3.6 이상

### 2. Pandoc 설치 (필수)
PDF 및 DOCX 변환을 위해 pandoc이 필요합니다.

#### Windows
1. [Pandoc 공식 사이트](https://pandoc.org/installing.html#windows)에서 설치 파일 다운로드
2. 설치 후 환경변수 PATH에 추가 확인

#### macOS
```bash
brew install pandoc
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install pandoc
```

### 3. LaTeX 엔진 설치 (PDF 변환용)
PDF 변환을 위해 LaTeX 엔진이 필요합니다.

#### Windows
- [MiKTeX](https://miktex.org/) 또는 [TeX Live](https://www.tug.org/texlive/) 설치

#### macOS
```bash
brew install --cask mactex-no-gui
```

#### Ubuntu/Debian
```bash
sudo apt-get install texlive-xetex
```

## 🚀 사용법

### 기본 사용법
```bash
python markdown_converter.py input.md
```

### 출력 디렉토리 지정
```bash
python markdown_converter.py input.md -o output_folder
```

### 특정 형식만 변환
```bash
# PDF만 생성
python markdown_converter.py input.md -f pdf

# DOCX만 생성
python markdown_converter.py input.md -f docx

# 둘 다 생성 (기본값)
python markdown_converter.py input.md -f pdf docx
```

### 옵션 설명
- `-o, --output`: 출력 디렉토리 지정 (기본값: 입력 파일과 같은 디렉토리)
- `-f, --formats`: 출력 형식 선택 (pdf, docx 중 선택, 기본값: pdf docx)

## 📋 사용 예시

### 1. 테스트 파일로 실습
제공된 테스트 파일을 사용해보세요:

```bash
python markdown_converter.py test_input.md
```

실행 결과:
- `test_input_fixed.md`: 수정된 마크다운 파일
- `test_input.pdf`: PDF 파일
- `test_input.docx`: DOCX 파일

### 2. 실제 사용 시나리오
```bash
# ChatGPT 답변을 저장한 파일 변환
python markdown_converter.py chatgpt_response.md -o ./converted_files

# 여러 파일 처리 (배치 스크립트 작성)
for file in *.md; do
    python markdown_converter.py "$file" -o ./output
done
```

## 🔍 변환 예시

### 변환 전 (문제가 있는 텍스트)
```markdown
이것은 \*\*제대로 표시되지 않는 볼드 텍스트\*\*입니다.
\*\*중요한 정보\*\*가 볼드체로 표시되어야 합니다.
```

### 변환 후 (올바른 텍스트)
```markdown
이것은 **제대로 표시되지 않는 볼드 텍스트**입니다.
**중요한 정보**가 볼드체로 표시되어야 합니다.
```

## 🛠️ 기술적 세부사항

### 정규표현식 패턴
이 도구는 다음과 같은 정규표현식을 사용해 이스케이프된 텍스트를 찾습니다:
```python
text = re.sub(r'\\?\*\\?\*(.+?)\\?\*\\?\*', r'**\1**', text)
```

### 지원하는 변환 패턴
- `\*\*텍스트\*\*` → `**텍스트**`
- `\*텍스트\*` → `*텍스트*`
- 기타 이스케이프된 마크다운 문법

## 🚨 문제 해결

### pandoc을 찾을 수 없음
```
❌ pandoc이 설치되지 않았습니다.
```
**해결책**: pandoc을 설치하고 PATH 환경변수에 추가

### PDF 변환 실패
```
❌ PDF 변환 중 오류 발생
```
**해결책**: LaTeX 엔진(XeLaTeX) 설치 확인

### 한글 폰트 문제
**해결책**: 시스템에 NanumGothic 폰트가 설치되어 있는지 확인

## 🔧 두 가지 버전 제공

### 1. Pandoc 버전 (markdown_converter.py)
- **장점**: 고품질 PDF/DOCX 변환, 다양한 출력 옵션
- **단점**: Pandoc과 LaTeX 엔진 설치 필요
- **권장**: 전문적인 문서 작성이 필요한 경우

### 2. Python 라이브러리 버전 (markdown_converter_python.py)
- **장점**: 별도 프로그램 설치 불필요, Python만 있으면 실행 가능
- **단점**: 상대적으로 제한적인 스타일링
- **권장**: 간단한 변환이나 설치가 제한된 환경

## 🚀 빠른 시작 (Windows)

1. `install_and_run.bat` 파일을 실행
2. 필요한 패키지가 자동으로 설치됩니다
3. 안내에 따라 마크다운 파일을 변환하세요

## 📁 파일 구조
```
markdown-converter/
├── markdown_converter.py        # Pandoc 버전 (고품질)
├── markdown_converter_python.py # Python 라이브러리 버전 (간편)
├── requirements.txt             # Pandoc 버전 의존성
├── requirements_python.txt      # Python 버전 의존성
├── install_and_run.bat         # Windows 설치 도구
├── test_input.md               # 테스트용 샘플 파일
└── README.md                   # 사용법 안내
```

## 🤝 기여하기

버그 리포트나 기능 제안은 이슈로 등록해 주세요. Pull Request도 환영합니다!

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 
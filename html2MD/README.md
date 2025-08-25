# HTML to Markdown 변환기

HTML 파일이나 웹페이지를 깔끔한 Markdown 형식으로 변환하는 도구입니다.

## 🚀 주요 기능

- **파일 변환**: HTML 파일을 Markdown 파일로 변환
- **배치 변환**: 여러 HTML 파일을 한 번에 변환
- **웹 변환**: 웹 URL의 HTML을 직접 가져와서 변환
- **자동 정리**: 출력 파일들을 `./output/` 폴더에 자동 정리
- **인코딩 최적화**: 깨진 글자 없는 완벽한 한글/다국어 지원
- **정리 기능**: 불필요한 태그 제거 및 깔끔한 Markdown 생성
- **병렬 처리**: 빠른 배치 변환을 위한 멀티스레딩 지원

## 📦 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 필요한 라이브러리

- `beautifulsoup4`: HTML 파싱
- `markdownify`: HTML to Markdown 변환
- `lxml`: 빠른 XML/HTML 파싱
- `requests`: 웹 페이지 가져오기 (웹 변환용)

## 🛠️ 사용법

### 1. 단일 HTML 파일 변환

기본 사용 (자동으로 `./output/` 폴더에 저장):
```bash
python html_to_markdown.py input.html
```

출력 파일 지정:
```bash
python html_to_markdown.py input.html -o custom_output.md
```

### 2. 여러 HTML 파일 일괄 변환

현재 디렉토리의 모든 HTML 파일 변환 (자동으로 `./output/` 폴더에 저장):
```bash
python batch_converter.py ./html_files
```

특정 출력 디렉토리 지정:
```bash
python batch_converter.py ./html_files -o ./custom_markdown_files
```

하위 디렉토리 제외:
```bash
python batch_converter.py ./html_files --no-recursive
```

### 3. 웹 페이지 변환

기본 사용 (자동으로 `./output/` 폴더에 저장):
```bash
python web_converter.py https://example.com
```

출력 파일 지정:
```bash
python web_converter.py https://example.com -o custom_name.md
```

## 💻 프로그래밍 방식 사용

### 기본 사용법

```python
from html_to_markdown import HTMLToMarkdown

converter = HTMLToMarkdown()

# HTML 문자열 변환
html = "<h1>제목</h1><p>내용입니다.</p>"
markdown = converter.convert_string(html)
print(markdown)

# HTML 파일 변환
output_file = converter.convert_file("input.html", "output.md")
```

### 고급 설정

```python
from html_to_markdown import HTMLToMarkdown

converter = HTMLToMarkdown(
    strip_tags=['script', 'style', 'meta'],  # 제거할 태그
    convert_links=True,                       # 링크 변환 여부
    heading_style="ATX"                       # 헤딩 스타일
)
```

### 배치 변환

```python
from batch_converter import BatchConverter

batch = BatchConverter(max_workers=4)
results = batch.convert_directory(
    input_dir="./html_files",
    output_dir="./markdown_files",
    recursive=True
)

print(f"성공: {results['success']}개, 실패: {results['failed']}개")
```

### 웹 변환

```python
from web_converter import WebConverter

web_conv = WebConverter(timeout=30)
markdown = web_conv.convert_url_to_markdown(
    "https://example.com",
    output_file="example.md"
)
```

## ⚙️ 옵션 설명

### HTML to Markdown 변환기 옵션

- `strip_tags`: 제거할 HTML 태그 목록 (기본값: `['script', 'style', 'meta', 'link']`)
- `convert_links`: 링크 변환 여부 (기본값: `True`)
- `heading_style`: 헤딩 스타일
  - `"ATX"`: `# 제목` 형식 (기본값)
  - `"UNDERLINED"`: 언더라인 형식

### 배치 변환기 옵션

- `max_workers`: 동시 처리할 작업자 수 (기본값: 4)
- `recursive`: 하위 디렉토리 포함 여부 (기본값: True)

### 웹 변환기 옵션

- `timeout`: 요청 타임아웃 시간 (기본값: 30초)
- `max_retries`: 최대 재시도 횟수 (기본값: 3)

## 📁 출력 예시

### 입력 HTML
```html
<!DOCTYPE html>
<html>
<head>
    <title>예시 페이지</title>
</head>
<body>
    <h1>메인 제목</h1>
    <p>이것은 <strong>중요한</strong> 내용입니다.</p>
    <ul>
        <li>항목 1</li>
        <li>항목 2</li>
    </ul>
    <a href="https://example.com">링크</a>
</body>
</html>
```

### 출력 Markdown
```markdown
# 메인 제목

이것은 **중요한** 내용입니다.

- 항목 1
- 항목 2

[링크](https://example.com)
```

## 🔧 문제 해결

### 인코딩 문제
한글이 깨져서 나올 경우, HTML 파일의 인코딩을 확인하세요. 대부분의 경우 UTF-8로 저장하면 해결됩니다.

### 메모리 사용량
매우 큰 HTML 파일을 처리할 때는 메모리 사용량이 높을 수 있습니다. 이런 경우 파일을 작은 부분으로 나누어 처리하는 것을 권장합니다.

### 네트워크 오류
웹 변환 시 네트워크 오류가 발생하면 타임아웃 값을 늘리거나 재시도 횟수를 조정해보세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요. Pull Request도 환영합니다! 
# 빠른 시작 가이드

논문 평가 자동화 시스템을 5분 안에 시작하는 방법입니다.

## 🚀 1단계: 설치

```bash
# 1. 저장소 클론 또는 다운로드 후 디렉토리 이동
cd paper-review-automation

# 2. 자동 설정 스크립트 실행
python setup.py
```

## 🔑 2단계: API 키 설정

### 필수: OpenAI API 키

1. [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키 발급
2. `.env` 파일 편집:

```bash
OPENAI_API_KEY=sk-proj-your-api-key-here
```

### 선택사항: 플랫폼 API 키

게시하고 싶은 플랫폼의 API 키를 추가로 설정하세요:

**Medium (추천)**
```bash
MEDIUM_TOKEN=your_medium_integration_token
```

**GitHub Pages**
```bash
GITHUB_TOKEN=your_github_token
GITHUB_REPO=yourusername/your-blog-repo
```

## 🧪 3단계: 테스트

```bash
# 실제 게시 없이 테스트
python main.py --text "AI와 자연어처리" "이 논문은 혁신적인 접근법을 제시합니다..." --dry-run
```

성공하면 `output/` 폴더에 생성된 마크다운 파일을 확인할 수 있습니다.

## 📄 4단계: 실제 사용

### arXiv 논문 처리
```bash
python main.py --arxiv 2301.12345 --platforms medium
```

### 직접 텍스트 입력
```bash
python main.py --text "논문 제목" "논문 전체 내용..." --platforms medium github_pages
```

### PDF 파일 처리
```bash
python main.py --pdf ./my_paper.pdf --platforms medium
```

## 📊 결과 확인

- **생성된 파일**: `output/` 폴더
- **게시 결과**: 콘솔 출력 및 세션 보고서
- **로그**: `logs/` 폴더

## ⚠️ 주의사항

1. **OpenAI 사용량**: API 호출 시 비용이 발생합니다
2. **플랫폼 정책**: 각 플랫폼의 이용약관을 준수하세요
3. **Reddit 주의**: 스팸으로 간주될 수 있으므로 신중하게 사용
4. **윤리적 사용**: 실제 논문의 가치를 정확히 평가하는 용도로만 사용

## 🆘 문제 해결

### 자주 발생하는 오류

**"OpenAI API 키 오류"**
- `.env` 파일의 API 키 확인
- OpenAI 계정의 크레딧 잔액 확인

**"모듈을 찾을 수 없음"**
```bash
pip install -r requirements.txt
```

**"권한 오류" (GitHub/Medium)**
- API 토큰의 권한 설정 확인
- 토큰 만료 여부 확인

### 로그 확인
```bash
# Windows
type logs\paper_review_*.log

# Linux/Mac
tail -f logs/paper_review_*.log
```

## 📞 도움이 필요하면

1. `README.md`의 상세 가이드 확인
2. `config/config.yaml`에서 설정 조정
3. `example_papers.json`으로 일괄 처리 테스트

---

**🎉 축하합니다! 이제 AI 기반 논문 평가 시스템을 사용할 준비가 되었습니다.**
# PubMed Abstract 추출기

PubMed ID 리스트에서 논문의 abstract를 추출하여 TSV 파일로 저장하는 도구입니다.

## 설치

먼저 필요한 패키지들을 설치합니다:

```bash
pip install -r requirements.txt
```

## 사용법

### 기본 사용법

```bash
python extract_pubmed_abstracts.py example_pubmed_ids.txt
```

### 고급 옵션

```bash
# 출력 파일명 지정
python extract_pubmed_abstracts.py pubmed_ids.txt --output my_abstracts.tsv

# 배치 크기 조정 (기본: 1000, 최대: 1000)
python extract_pubmed_abstracts.py pubmed_ids.txt --batch-size 500

# 이메일 주소 지정 (NCBI 요구사항)
python extract_pubmed_abstracts.py pubmed_ids.txt --email your@email.com

# 모든 옵션 함께 사용
python extract_pubmed_abstracts.py pubmed_ids.txt \
  --output results.tsv \
  --batch-size 500 \
  --email your@email.com
```

## 입력 파일 형식

PubMed ID가 한 줄에 하나씩 저장된 텍스트 파일:

```
17284678
15531828
11791095
10708056
```

## 출력 형식

TSV (Tab-Separated Values) 파일:

```
pub_id	abstract
17284678	Eimeria tenella is an intracellular protozoan parasite...
15531828	To study the occurrence of nosocomial diarrhea in pediatric wards...
```

## 주요 기능

- **배치 처리**: 60K+ 논문도 처리 가능 (NCBI 제한에 따라 1000개씩 배치 처리)
- **에러 처리**: 실패한 논문 ID 추적 및 보고
- **진행 상황 표시**: 실시간 처리 상황 확인
- **자동 대기**: NCBI 서버 부하 방지를 위한 자동 대기
- **UTF-8 인코딩**: 다국어 abstract 지원

## 참고사항

- NCBI의 사용 정책에 따라 한 번에 최대 1000개의 논문만 요청할 수 있습니다.
- 대량 처리 시 NCBI 서버 부하 방지를 위해 배치 간 0.5초 대기합니다.
- Abstract가 없는 논문의 경우 제목(ArticleTitle)을 대신 저장합니다.

## 문제 해결

### BioPython 설치 오류
```bash
# Windows
pip install --upgrade pip
pip install biopython

# macOS/Linux
pip3 install --upgrade pip
pip3 install biopython
```

### 네트워크 오류
- 인터넷 연결을 확인하세요
- 방화벽이나 프록시 설정을 확인하세요
- NCBI 서버가 일시적으로 접근 불가능할 수 있습니다

### 메모리 부족
- 배치 크기를 줄여보세요 (예: --batch-size 100)
- 대량 처리 시 여러 번에 나누어 실행하세요 
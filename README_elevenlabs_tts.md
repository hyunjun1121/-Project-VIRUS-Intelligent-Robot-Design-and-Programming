# ElevenLabs Text-to-Speech Generator 🎤

최신 ElevenLabs API를 사용하여 텍스트를 고품질 오디오로 변환하는 Python 도구입니다.

## 🚀 특징

- **최신 ElevenLabs Python SDK 사용** ([공식 문서](https://elevenlabs.io/docs/api-reference/introduction))
- **다양한 음성 옵션** (여성/남성, 다양한 억양)
- **3가지 품질 모델** (최고 품질, 저지연, 균형잡힌)
- **명령줄 인터페이스** 및 **대화형 모드**
- **자동 재생** 및 **파일 저장**
- **커스터마이징 가능한 출력 포맷**

## 📦 설치

### 1. 필수 패키지 설치
```bash
pip install elevenlabs python-dotenv
```

### 2. API 키 설정
ElevenLabs에서 API 키를 발급받고 `.env` 파일에 저장:

```bash
# .env 파일
ELEVENLABS_API_KEY=your_api_key_here
```

API 키는 [ElevenLabs 대시보드](https://elevenlabs.io/docs/api-reference/authentication)에서 발급받을 수 있습니다.

## 🎯 사용법

### 기본 사용법
```bash
# 단순 텍스트 변환
python elevenlabs_tts.py "안녕하세요! ElevenLabs로 만든 음성입니다."

# 음성과 모델 지정
python elevenlabs_tts.py "Hello World" --voice rachel --model flash_v2.5

# 파일명 지정
python elevenlabs_tts.py "테스트 음성" --output my_audio.mp3
```

### 대화형 모드
```bash
python elevenlabs_tts.py --interactive
```

### 음성 목록 확인
```bash
python elevenlabs_tts.py --list-voices
```

### 특정 음성 정보 확인
```bash
python elevenlabs_tts.py --voice-info rachel
```

## 🎤 사용 가능한 음성

| 음성명    | 성별 | 억양      | Voice ID |
|-----------|------|-----------|----------|
| rachel    | 여성 | 미국      | 21m00Tcm4TlvDq8ikWAM |
| dave      | 남성 | 영국      | CYw3kZ02Hs0563khs1Fj |
| sarah     | 여성 | 미국      | EXAVITQu4vr4xnSDxMaL |
| antoni    | 남성 | 미국      | ErXwobaYiN019PkySvjV |
| josh      | 남성 | 미국      | TxGEqnHWrfWFTfGW9XjX |
| fin       | 남성 | 아일랜드  | D38z5RcWu1voky8WS1ja |

## 🤖 사용 가능한 모델

| 모델명          | 특징                    | 지연시간  | 품질 |
|----------------|-------------------------|-----------|------|
| multilingual_v2 | 최고 품질, 29개 언어    | 보통      | ⭐⭐⭐⭐⭐ |
| flash_v2.5     | 초저지연, 32개 언어     | 75ms      | ⭐⭐⭐⭐ |
| turbo_v2.5     | 균형잡힌 품질과 속도    | 250-300ms | ⭐⭐⭐⭐ |

## 📁 출력 포맷

| 포맷명      | 설명                | 파일 크기 | 품질 |
|-------------|---------------------|-----------|------|
| mp3_high    | 고품질 MP3 (44.1kHz/128kbps) | 보통     | ⭐⭐⭐⭐⭐ |
| mp3_medium  | 중간 품질 MP3 (44.1kHz/64kbps)  | 작음     | ⭐⭐⭐⭐ |
| mp3_low     | 저품질 MP3 (22.05kHz/32kbps) | 매우 작음 | ⭐⭐⭐ |
| wav         | WAV 형식 (44.1kHz)  | 큼       | ⭐⭐⭐⭐⭐ |

## 📋 명령줄 옵션

```bash
python elevenlabs_tts.py [텍스트] [옵션]

위치 인수:
  text                  변환할 텍스트

옵션:
  -h, --help           도움말 메시지
  -v, --voice VOICE    사용할 음성 (기본값: rachel)
  -m, --model MODEL    사용할 모델 (기본값: multilingual_v2)
  -f, --format FORMAT  출력 포맷 (기본값: mp3_high)
  -o, --output OUTPUT  출력 파일명
  --no-play            생성 후 자동 재생 하지 않음
  --list-voices        사용 가능한 음성 목록 출력
  --voice-info VOICE   특정 음성의 정보 출력
  -i, --interactive    대화형 모드
```

## 💡 사용 예시

### 1. 기본 사용
```bash
python elevenlabs_tts.py "안녕하세요, 반갑습니다!"
```

### 2. 다른 음성으로 변환
```bash
python elevenlabs_tts.py "Hello, how are you?" --voice josh
```

### 3. 저지연 모델 사용 (실시간 애플리케이션용)
```bash
python elevenlabs_tts.py "실시간 응답입니다" --model flash_v2.5
```

### 4. WAV 포맷으로 저장
```bash
python elevenlabs_tts.py "고품질 오디오" --format wav --output speech.wav
```

### 5. 재생 없이 파일만 저장
```bash
python elevenlabs_tts.py "파일로만 저장" --no-play --output silent.mp3
```

## 🔧 Python 코드에서 사용

```python
from elevenlabs_tts import ElevenLabsTTS

# TTS 객체 생성
tts = ElevenLabsTTS()

# 텍스트를 음성으로 변환
output_file = tts.text_to_speech(
    text="안녕하세요! 프로그래밍으로 생성한 음성입니다.",
    voice="rachel",
    model="multilingual_v2",
    output_format="mp3_high",
    play_audio=True
)

print(f"오디오 파일 생성됨: {output_file}")
```

## 🌍 지원 언어

ElevenLabs는 **32개 언어**를 지원합니다:
- 영어 (미국, 영국, 호주, 캐나다)
- 한국어, 일본어, 중국어
- 독일어, 프랑스어, 스페인어, 이탈리아어
- 포르투갈어, 네덜란드어, 러시아어
- 그 외 다수...

## ⚠️ 주의사항

1. **API 키 필수**: ElevenLabs API 키가 필요합니다
2. **인터넷 연결**: API 호출을 위해 인터넷 연결이 필요합니다
3. **사용량 제한**: API 요금제에 따라 월간 사용량 제한이 있습니다
4. **저작권**: 생성된 오디오의 상업적 사용은 유료 플랜에서만 가능합니다

## 🔗 참고 링크

- [ElevenLabs 공식 문서](https://elevenlabs.io/docs/api-reference/introduction)
- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [음성 라이브러리](https://elevenlabs.io/docs/capabilities/voices)
- [모델 정보](https://elevenlabs.io/docs/get-started/models)

## 📄 라이선스

이 도구는 MIT 라이선스 하에 제공됩니다. ElevenLabs API 사용은 해당 서비스의 이용약관을 따릅니다. 
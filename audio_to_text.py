# ===================================================
# LEGACY BACKUP FILE - NOT USED IN CURRENT SYSTEM
# ===================================================
# This file uses Whisper API for speech-to-text conversion.
# The current system now uses direct audio processing 
# with gpt-4o-mini-audio-preview-2024-12-17 model
# in LLM_conversation.py and LLM_function.py
# ===================================================

import os
import io
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import keyboard           # pip install keyboard
import openai
from dotenv import load_dotenv  # pip install python-dotenv
from function import process_voice_text  # 기능 구현.py에서 함수 임포트

# ——————————————————————————————
# 1) 환경 변수에 OpenAI API 키 설정
# ——————————————————————————————
load_dotenv()  # .env 파일에서 환경 변수 로드
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하거나 직접 키를 설정해주세요.")

# OpenAI 클라이언트 초기화
client = openai.OpenAI()

# ——————————————————————————————
# 2) 녹음/변환 설정
# ——————————————————————————————
SAMPLE_RATE = 16000    # Whisper 권장 샘플링 레이트
CHANNELS = 1           # 모노
KEY = "space"          # 녹음 제어 키

frames = []
recording = False

# ——————————————————————————————
# 3) 스트림 콜백: recording이 True일 때만 데이터 수집
# ——————————————————————————————
def audio_callback(indata, frames_count, time_info, status):
    global frames
    if status:
        print(f"⚠️ 녹음 경고: {status}")
    if recording:
        frames.append(indata.copy())

# ——————————————————————————————
# 4) 마이크 스트림 열기
# ——————————————————————————————
stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    callback=audio_callback
)
stream.start()
print("🚀 스트림 열림. 스페이스바를 눌러 녹음을 시작하세요.")

# ——————————————————————————————
# 5) 메인 루프: 키 입력 감지 → 녹음 → Whisper 전송
# ——————————————————————————————
try:
    while True:
        # 스페이스바 누르면 녹음 시작
        if keyboard.is_pressed(KEY) and not recording:
            recording = True
            frames.clear()
            print("⏺️ 녹음 시작… (키에서 손 떼면 전송)")

        # 키에서 손 떼면 녹음 종료 & Whisper API 호출
        if recording and not keyboard.is_pressed(KEY):
            recording = False
            print("⏹️ 녹음 종료. Whisper에 전송 중…")

            # (1) numpy 배열로 합치기
            audio_data = np.concatenate(frames, axis=0)

            # (2) BytesIO에 WAV로 저장
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, audio_data, SAMPLE_RATE,
                     format="WAV", subtype="PCM_16")
            
            # 파일 이름 지정 (확장자 인식을 위해 필요)
            wav_buffer.name = "audio.wav"
            
            wav_buffer.seek(0)

            # (3) Whisper API 호출
            try:
                resp = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=wav_buffer,
                    response_format="text",
                    language="en"
                )
                converted_text = resp.strip()
                print(f"[{time.strftime('%H:%M:%S')}] 변환 결과:")
                print(converted_text)

                # 텍스트 변환 성공 시 GPT 처리 실행
                if converted_text:
                    print("\n🔄 GPT로 텍스트 처리 중...")
                    process_voice_text(converted_text)

            except Exception as e:
                print("❌ 변환 오류:", e)

            print("\n🔄 다음 녹음을 위해 스페이스바를 눌러주세요.\n")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n🔌 종료합니다.")
    stream.stop()
    stream.close()

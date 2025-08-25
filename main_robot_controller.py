from multiprocessing import process
import os
import io
import queue
import time
import json
from typing import Any
import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
import openai
import threading
import pygame
# Import the modules needed for the complete system
from LLM_function import process_voice_text as process_for_commands, process_voice_audio as process_for_audio_commands
from LLM_conversation import process_voice_text as process_for_conversation, process_voice_audio as process_for_audio_conversation
from text_to_audio import text_to_speech
from client_vlm_parallel_alt import main as run_vlm_alt

try:
    from pi_exercise import main as run_spike
    SPIKE_AVAILABLE = True
    print("✅ SPIKE robot control available")
except ImportError as e:
    print(f"⚠️ SPIKE robot control unavailable: {e}")
    SPIKE_AVAILABLE = False
    def run_spike(command):
        print(f"🤖 [SIMULATION] Would execute robot command: {command}")

# Load environment variables for API keys
load_dotenv()
api_lock = threading.Lock()
sound_lock = threading.Lock()

def convert_audio_to_text_via_api(audio_data, sample_rate):
    """Converts audio data to text using OpenAI's Whisper API."""
    global client # 전역 OpenAI 클라이언트 사용

    if audio_data is None or len(audio_data) == 0:
        print("❌ No audio data to transcribe.")
        return None

    try:
        wav_buffer = io.BytesIO()
        # Whisper API는 다양한 오디오 형식을 지원하지만, WAV가 일반적입니다.
        # LLM_function.py/LLM_conversation.py 에서 사용된 PCM_U8을 유지하여 파일 크기를 줄입니다.
        sf.write(wav_buffer, audio_data, sample_rate, format="WAV", subtype="PCM_U8")
        wav_buffer.name = "audio_for_stt.wav" # 파일 이름 명시 (API 일부에서 필요할 수 있음)
        wav_buffer.seek(0)

        print(f"📤 Uploading audio ({len(wav_buffer.getvalue())/1024:.1f}KB) to Whisper API...")
        
        # client.audio.transcriptions.create는 파일 객체를 직접 받습니다.
        response = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=wav_buffer, # wav_buffer는 BytesIO 객체이므로 파일처럼 동작합니다.
            response_format="text",
            language="en" # 영어로 고정 (필요시 변경 가능)
        )
        
        # Whisper API 응답은 텍스트 문자열 자체입니다 (response_format="text"인 경우).
        transcribed_text = response.strip() if response else None
        return transcribed_text
    except Exception as e:
        print(f"❌ Whisper API transcription error: {e}")
        return None

class MultiThreadManager:
    def __init__(self):
        self.vlm_thread = None
        self.vlm_result = None
        self.vlm_complete = threading.Event()
        
        self.conversation_thread = None
        self.conversation_result = None
        self.conversation_complete = threading.Event()
        
        # self.face_thread = None
        # self.face_result = None
        # self.face_complete = threading.Event()
        
        self.lock = threading.Lock()
    def start_vlm_processing(self):
        with self.lock:
            if self.vlm_thread is None or not self.vlm_thread.is_alive():
                self.vlm_complete.clear()
                self.vlm_thread = threading.Thread(
                    target=self._run_vlm,
                    daemon=True
                )
                self.vlm_thread.start()
            else:
                print("[VLM] Processing already running")
    def _run_vlm(self):
        try:
            result = run_vlm_alt(mode="image")
            with self.lock:
                self.vlm_result = result
        except Exception as e:
            print(f"VLM error: {e}")
            with self.lock:
                self.vlm_result = None
        finally:
            self.vlm_complete.set()
    def get_vlm_result(self, timeout=30):
        finished = self.vlm_complete.wait(timeout)
        with self.lock:
            return self.vlm_result if finished else None
    def start_text_conversation_processing(self, transcribed_text, vlm_result):
        with self.lock:
            if self.conversation_thread is None or not self.conversation_thread.is_alive():
                self.conversation_complete.clear()
                self.conversation_thread = threading.Thread(
                    target=self._run_text_conversation,
                    args = [transcribed_text, vlm_result],
                    daemon=True
                )
                self.conversation_thread.start()
            else:
                print("[Conversation] Processing already running")
    def _run_text_conversation(self, transcribed_text, vlm_result):
        result = False
        try:
            with api_lock:
                conversation_response_text = process_for_conversation(
                    transcribed_text,
                    additional_prompt=f"[Image/Video Description]: {vlm_result}"
                )
            
            if conversation_response_text:
                print("\n🔊 Converting response to speech...")
                response_file_path = text_to_speech(
                    text=conversation_response_text,
                    voice_id=VOICE_ID,
                    output_filename=RESPONSE_AUDIO_FILE
                )
                result = True
                
                if response_file_path and os.path.exists(response_file_path):
                    print(f"Conversational audio response saved to {RESPONSE_AUDIO_FILE}")
                    # Try to play the audio response
                    try:
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(response_file_path)
                        pygame.mixer.music.play()
                        print("🔊 Playing response audio...")
                        while pygame.mixer.music.get_busy():
                            pygame.time.Clock().tick(10)
                    except ImportError:
                        print(f"Audio saved to {RESPONSE_AUDIO_FILE}. Install pygame to enable autoplay.")
                    except Exception as e:
                        print(f"Error playing audio: {e}")
            else:
                print("⚠️ No conversational response generated.")
                
            with self.lock:
                self.conversation_result = result
        except Exception as e:
            print(f"Conversation (text input) error: {e}")
            with self.lock:
                self.conversation_result = False
        finally:
            self.conversation_complete.set()
    def get_conversation_result(self, timeout=30):
        finished = self.conversation_complete.wait(timeout)
        with self.lock:
            return self.conversation_result if finished else None
    # def start_converation_processing(self, audio_data, vlm_result):
    #     def _converation_wrapper():
    #         self.conversation_running.set()
    #         try:
    #             with api_lock:
    #                 conversation_response = process_for_audio_conversation(
    #                 audio_data,
    #                 SAMPLE_RATE,
    #                 additional_prompt=f"[Image/Video Description]: {vlm_result}"
    #                 )
    #             if conversation_response:
    #                 print("\n🔊 Converting response to speech...")
    #                 text_to_speech(
    #                     text=conversation_response,
    #                     voice_id=VOICE_ID,
    #                     output_filename=OUTPUT_AUDIO_FILE
    #                 )
    #                 # Optionally play the audio response
    #                 try:
    #                     print("pygame start")
    #                     # pygame.mixer.init()
    #                     # pygame.mixer.music.load(OUTPUT_AUDIO_FILE)
    #                     # pygame.mixer.music.play()
    #                     print("pypgame end")
    #                     # while pygame.mixer.music.get_busy():
    #                     #     pygame.time.Clock().tick(10)
    #                 except ImportError:
    #                     print(f"Audio saved to {OUTPUT_AUDIO_FILE}. Install pygame to enable autoplay.")
    #         finally:
    #             print("conversation end")
    #             self.conversation_running.clear()
    #     self.conversation_thread = threading.Thread(target=_converation_wrapper, daemon=True)
    #     self.conversation_thread.start()
    # def start_face_processing(self):
    #     with self.lock:
    #         if self.face_thread is None or not self.face_thread.is_alive():
    #             self.face_complete.clear()
    #             self.face_thread = threading.Thread(
    #                 target=self._run_face,
    #                 daemon=True
    #             )
    #             self.face_thread.start()
    #         else:
    #             print("[face] Processing already running")
    # def _run_face(self):
    #     try:
    #         with self.lock:
    #             self.face_result = run_face_alt(mode="image")
    #     except Exception as e:
    #         print(f"face error: {e}")
    #         with self.lock:
    #             self.face_result = None
    #     finally:
    #         self.face_complete.set()
    # def get_face_result(self, timeout=30):
    #     finished = self.face_complete.wait(timeout)
    #     with self.lock:
    #         return self.face_result if finished else None




manager = MultiThreadManager()
# Check if OpenAI API key is available
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key is not set. Please check your .env file.")

# Initialize OpenAI client
client = openai.OpenAI()

# Audio recording settings - Optimized for Raspberry Pi
SAMPLE_RATE = 8000     # Reduced from 16000 for faster upload (still decent quality)
CHANNELS = 1           # Mono
VOICE_ID = "ErXwobaYiN019PkySvjV"    # Voice ID for ElevenLabs - antoni (남성, 미국 억양)
WAIT_AUDIO_FILE = "wait.mp3"  # Fixed wait message file
RESPONSE_AUDIO_FILE = "response.mp3"  # Response audio file (generated by text_to_audio.py)
OUTPUT_AUDIO_FILE = "out.mp3"
# 소리 감지 설정 - Raspberry Pi optimized
THRESHOLD_DB = -35     # 녹음 시작을 위한 임계 데시벨 (적절한 값으로 조정 필요)
SILENCE_THRESHOLD_DB = -35  # 녹음 종료를 위한 임계 데시벨 (적절한 값으로 조정 필요)
SILENCE_DURATION = 1.0  # 녹음 종료를 위한 침묵 지속 시간(초) - 빠른 응답을 위해 1초로 단축
# MAX_RECORDING_DURATION = None  # 최대 녹음 시간 제한 없음

frames = []
recording = False
recording_start_time = None  # 녹음 시작 시간 추적 - 추가
silence_start_time = None
last_db_print_time = 0  # 데시벨 출력 제한을 위한 마지막 출력 시간
last_countdown_time = 0  # 카운트다운 출력 제한을 위한 마지막 출력 시간
DB_PRINT_INTERVAL = 0.5  # 데시벨 출력 간격(초)
COUNTDOWN_PRINT_INTERVAL = 0.2  # 카운트다운 출력 간격(초)
recording_completed = False  # 녹음 완료 플래그 (녹음만 중단하고 이후 처리는 계속함)
processing_audio = False
def calculate_db(audio_data):
    """오디오 데이터의 데시벨 레벨 계산"""
    if len(audio_data) == 0:
        return -np.inf
    # RMS 값 계산
    rms = np.sqrt(np.mean(np.square(audio_data)))
    # RMS를 dB로 변환 (0 dB 기준은 최대 가능 진폭 1.0)
    if rms > 0:
        db = 20 * np.log10(rms)
    else:
        db = -np.inf
    return db
record_count = 0
def audio_callback(indata, frames_count, time_info, status):
    """Callback function for audio stream"""
    global frames, recording, recording_start_time, silence_start_time, last_db_print_time, last_countdown_time, recording_completed, record_count,manager, api_lock, processing_audio
    if status:
        print(f"⚠️ Recording warning: {status}")
    
    # 이미 녹음이 완료되었으면 데이터 수집하지 않음
    if recording_completed:
        return
    
    # 현재 오디오 데이터의 데시벨 레벨 계산
    current_db = calculate_db(indata)
    
    # 현재 시간
    current_time = time.time()
    
    # 일정 간격으로 현재 데시벨 출력
    if current_time - last_db_print_time >= DB_PRINT_INTERVAL:
        db_status = ""
        if current_db > THRESHOLD_DB:
            db_status = "🔊 ACTIVE"
        elif current_db < SILENCE_THRESHOLD_DB:
            db_status = "🔈 SILENT"
        else:
            db_status = "🔉 NORMAL"
        
        print(f"🎤 Sound level: {current_db:.1f} dB {db_status}")
        last_db_print_time = current_time
    
    # 녹음 중이 아닐 때, 임계값 이상이면 녹음 시작
    if not recording and current_db > THRESHOLD_DB:
        recording = True
        frames.clear()
        silence_start_time = None
        recording_start_time = current_time
        record_count=0
        print(f"\n⏺️ Recording started automatically (detected {current_db:.2f} dB > threshold {THRESHOLD_DB} dB)...")

        # Trigger image or video upload via client_vlm_parallel_alt
        

        # Start a thread pool executor to upload image or video and get result
        # executor = concurrent.futures.ThreadPoolExecutor()
        # future_vlm = executor.submit(run_vlm_alt, mode="image")  # or "video"
        # vlm_thread = threading.Thread(
        #     target = lambda: vlm_result_queue.put(run_vlm_alt(mode="image")),
        #     daemon=True
        # )
        # vlm_thread.start()
        manager.start_vlm_processing()
    # 녹음 중일 때
    if recording:
        frames.append(indata.copy())
        record_count+=1
        # 최대 녹음 시간 제한 없음으로 변경 - 주석 처리
        # recording_duration = current_time - recording_start_time
        # if recording_duration >= MAX_RECORDING_DURATION:
        #     recording = False
        #     recording_completed = True
        #     print(f"\n⏹️ Recording ended automatically (max duration {MAX_RECORDING_DURATION} seconds reached).")
        #     process_recorded_audio()
        #     return
        
        # 임계값 이하의 소리가 감지되면 침묵 시간 체크 시작/업데이트
        if current_db < SILENCE_THRESHOLD_DB:
            if silence_start_time is None:
                silence_start_time = current_time
                print(f"\n⏸️ Silence detected ({current_db:.2f} dB < threshold {SILENCE_THRESHOLD_DB} dB)")
            
            # 침묵 경과 시간
            elapsed_silence = current_time - silence_start_time
            # 종료까지 남은 시간
            remaining_time = SILENCE_DURATION - elapsed_silence
            
            # 일정 간격으로 카운트다운 출력
            if current_time - last_countdown_time >= COUNTDOWN_PRINT_INTERVAL and remaining_time > 0:
                print(f"⏱️ Recording will end in: {remaining_time:.1f} seconds...")
                last_countdown_time = current_time
            
            # 침묵 시간이 임계값을 넘으면 녹음 종료
            if elapsed_silence >= SILENCE_DURATION:
                recording = False
                recording_completed = True  # 녹음 완료 플래그 설정 (더 이상 오디오 입력을 받지 않음)
                processing_audio = True
                print(f"\n⏹️ Recording ended automatically (silence for {SILENCE_DURATION} seconds).")
                processing_thread = threading.Thread(
                    target=process_recorded_audio_async,
                    daemon=True
                )
                processing_thread.start()
        else:
            # 소리가 다시 임계값 이상이 되면 침묵 타이머 초기화
            if silence_start_time is not None:
                print(f"🔊 Voice detected again ({current_db:.2f} dB > {SILENCE_THRESHOLD_DB} dB) - Silence timer reset")
                silence_start_time = None
def process_recorded_audio_async():
    """비동기로 녹음된 오디오 처리"""
        # Play wait.mp3 before processing
    global processing_audio, recording_completed
    
    try:
        process_recorded_audio()
    finally:
        # 처리 완료 후 플래그 리셋
        processing_audio = False
        recording_completed = False
        print("\n🎤 Ready for next recording...")
def process_recorded_audio():
    """녹음된 오디오 처리"""
    global frames
    
    if not frames:  # Skip if no audio was recorded
        print("No audio recorded. Try again.")
        return
    
    print("\n🔄 Processing recorded audio...")
    print("🔊 Playing wait message...")
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(WAIT_AUDIO_FILE)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except ImportError:
        print(f"⚠️ pygame not installed. Cannot play {WAIT_AUDIO_FILE}")
    print("\n⏳ Waiting for VLM (Vision Language Model) result...")
    vlm_result = manager.get_vlm_result(timeout=40)
    if vlm_result:
        print(f"🎯 VLM analysis complete: {vlm_result[:100]}..." if len(vlm_result) > 100 else f"🎯 VLM analysis complete: {vlm_result}")
    else:
        print("⚠️ VLM processing timeout or failed")
    
    # Convert audio data to numpy array
    print("\n📊 Preparing audio data for transcription...")
    audio_data = np.concatenate(frames, axis=0)

    # 1. Convert audio to text using Whisper API
    print("\n🎙️ Converting speech to text using Whisper API...")
    transcribed_text = convert_audio_to_text_via_api(audio_data, SAMPLE_RATE)

    if transcribed_text:
        print(f"✅ Transcribed text: \"{transcribed_text}\"")

        # 2. Start conversation processing using the transcribed text (threaded)
        #    This will handle the conversational response and TTS.
        print("\n🤖 Generating VIRUS conversational response (async thread)...")
        manager.start_text_conversation_processing(transcribed_text, vlm_result)

        # 3. Process command interpretation using the transcribed text (synchronous here)
        print("⚙️ Interpreting robot commands...")
        command_response_json = None
        with api_lock: # Ensure API calls are thread-safe
            try:
                # Use process_for_commands (from LLM_function, expects text)
                command_response_json = process_for_commands( # 여기가 process_for_commands 여야 합니다.
                    transcribed_text,
                    additional_prompt=f"[Image/Video Description]: {vlm_result}"
                )
                print(f"→ Robot command generated: {command_response_json}")
            except Exception as e:
                print(f"❌ Command processing error: {e}")
                command_response_json = None
    else:
        print("⚠️ No transcribed text available for command processing")
        
    if command_response_json:
        print(f"\n🤖 Executing robot command sequence...")
        try:
            run_spike(command_response_json)
            print("✅ Robot command executed successfully")
        except Exception as e:
            print(f"❌ Robot command execution error: {e}")
    else:
        print("ℹ️ No robot command to execute")
    print("\n⏳ Waiting for conversational response to complete...")
    conversation_completed = manager.get_conversation_result(timeout = 40)
    if conversation_completed:
        print("✅ Conversational response completed")
    else:
        print("⚠️ Conversational response timeout or failed")
        
    print("\n✅ All processing completed. Ready for next command...")
    frames.clear()


def process_complete_interaction():
    """Main function to handle the complete interaction flow"""
    global processing_audio, recording_completed, recording
    processing_audio = False
    recording_completed = False
    recording = False
    # Create and start the audio stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        callback=audio_callback
    )
    stream.start()
    print("\n🚀 VIRUS System initialized successfully!")
    print("🎤 Voice detection active - speak to trigger recording")
    print(f"📊 Recording triggers at >{THRESHOLD_DB} dB, stops after {SILENCE_DURATION}s of silence <{SILENCE_THRESHOLD_DB} dB")
    
    try:
        # 프로그램이 계속 실행되도록 무한 루프 유지
        while True:
            time.sleep(0.1)  # 시스템 부하 방지용 약간의 지연
    
    except KeyboardInterrupt:
        print("\n🔌 Shutting down system.")
    finally:
        # Clean up resources

        if 'stream' in locals():
            stream.stop()
            stream.close()

if __name__ == "__main__":
    # Display welcome message
    print("=" * 50)
    print("VIRUS COMBAT ROBOT CONTROL SYSTEM")
    print("Versatile, Intelligent Robotic Unit for Strategy")
    print("=" * 50)
    print("Ready for voice commands - System features:")
    print(f"  • Voice threshold: {THRESHOLD_DB} dB (auto-start)")
    print(f"  • Silence detection: {SILENCE_DURATION}s below {SILENCE_THRESHOLD_DB} dB (auto-stop)")
    print(f"  • Audio format: {SAMPLE_RATE}Hz, 8-bit mono (optimized for Raspberry Pi)")
    print("  • Parallel processing: Vision analysis + Speech recognition + Response generation")
    print("  • Continuous operation: Automatically ready for next command after processing")
    print("\nPress Ctrl+C to exit anytime.")
    print("=" * 50)
    
    # Start the interaction loop
    process_complete_interaction() 

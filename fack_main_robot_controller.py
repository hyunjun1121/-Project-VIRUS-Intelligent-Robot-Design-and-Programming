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
#import pygame
# Import the modules needed for the complete system
from LLM_function import process_voice_text as process_for_commands, process_voice_audio as process_for_audio_commands
from LLM_conversation import process_voice_text as process_for_conversation, process_voice_audio as process_for_audio_conversation
from text_to_audio import text_to_speech
from client_vlm_parallel_alt import main as run_vlm_alt
import json

from bt import BT
from client_face_parallel import main as run_face_alt
class MultiThreadManagerfaces:
	def __init__(self):
		self.face_thread = None
		self.face_result = None
		self.face_complete = threading.Event()
		self.face_lock = threading.Lock()

	def start_face_processing(self):
		"""
		face_area 모드로 run_face_alt를 백그라운드에서 실행.
		이미 실행 중이면 재실행하지 않음.
		"""
		with self.face_lock:
			if self.face_thread is None or not self.face_thread.is_alive():
				self.face_complete.clear()
				self.face_thread = threading.Thread(
					target=self._run_face,
					daemon=True
				)
				self.face_thread.start()
			else:
				print("[face] Processing already running")

	def _run_face(self):
		"""
		실제로 face 처리 함수(run_face_alt)를 호출하고 결과를 self.face_result에 저장.
		완료 플래그(face_complete)를 마지막에 세팅.
		"""
		try:
			# lock을 사용해 동시 접근 방지
			with self.face_lock:
				self.face_result = run_face_alt(mode="image")
		except Exception as e:
			print(f"[face] Error during processing: {e}")
			with self.face_lock:
				self.face_result = None
		finally:
			# face 처리 완료 신호
			self.face_complete.set()

	def get_face_result(self, timeout=30):
		"""
		face 처리가 끝날 때까지 최대 timeout 초 대기. 
		완료되면 JSON 문자열(self.face_result)을 반환, 
		타임아웃이 나면 None을 반환.
		"""
		finished = self.face_complete.wait(timeout)
		with self.face_lock:
			return self.face_result if finished else None

# -----------------------------------------------------
# HubController: Bluetooth 연결 및 명령 전송 관리
# -----------------------------------------------------
class HubController:
	def __init__(self, hub_id, address):
		self.hub_id = hub_id
		self.address = address
		self.sock = None
		self.lock = threading.Lock()
		self.bt = BT()
		self._connect()

	def _connect(self):
		"""
		BT.connect(address)를 호출하여 self.sock에 소켓 할당.
		실패 시 self.sock은 None으로 남음.
		"""
		print(f"[{self.hub_id}] 연결 시도...")
		try:
			self.sock = self.bt.connect(self.address)
			print(f"[{self.hub_id}] 연결 성공!")
		except Exception as e:
			print(f"[{self.hub_id}] 연결 실패: {e}")
			self.sock = None

	def send_single_command(self, cmd_json_str):
		"""
		단일 명령(cmd_json_str: JSON 문자열)을 Bluetooth 소켓으로 전송하고,
		'<<<<<<suc>>>>>>' 응답이 올 때까지 대기.
		"""
		if not cmd_json_str:
			# 빈 문자열, None 등 넘어오면 아무것도 안 하고 True 반환
			return True

		with self.lock:
			try:
				# JSON 문자열 뒤에 '\n' 붙여 전송 
				self.sock.send((cmd_json_str + "\n").encode("utf-8"))

				# 응답 버퍼에 '<<<<<<suc>>>>>>' 토큰이 나올 때까지 대기
				buf = b""
				while b"<<<<<<suc>>>>>>" not in buf:
					chunk = self.sock.recv(4096)
					if not chunk:
						# 연결이 끊기면 break
						break
					buf += chunk

				print(f"[{self.hub_id}] 실행 완료: {cmd_json_str}")
				return True

			except Exception as e:
				print(f"[{self.hub_id}] 오류 발생: {e}")
				return False

# -----------------------------------------------------
# 샘플 명령(JSON 문자열) (하드코딩된 예시)
# -----------------------------------------------------
SAMPLE_COMMANDS = {
	"hub1": '[ [ { "cmd": "move",     "val": 30 },  { "cmd": "rotate_x", "val": 20 } ] ]',
	"hub2": '[ [ { "cmd": "shoot",    "val":  1 },  { "cmd": "rotate_y", "val": 20 } ] ]'
}
# try:
#     from pi_exercise import main as run_spike
#     SPIKE_AVAILABLE = True
#     print("✅ SPIKE robot control available")
# except ImportError as e:
#     print(f"⚠️ SPIKE robot control unavailable: {e}")
#     SPIKE_AVAILABLE = False
#     def run_spike(command):
#         print(f"🤖 [SIMULATION] Would execute robot command: {command}")

# Load environment variables for API keys
load_dotenv()
api_lock = threading.Lock()
sound_lock = threading.Lock()

# 사용자 정의 응답 사전 설정
PREDEFINED_RESPONSES = {
	# LLM_function.py 응답 (로봇 명령)
	"commands": {
		"default": """[
[{"cmd": "move", "val": 100}]
]""",
		"hello": """[
[{"cmd": "steer", "val": 90}],
[{"cmd": "move", "val": 50}]
]""",
		"attack": """[
[{"cmd": "rotate_x", "val": 45}],
[{"cmd": "shoot", "val": 0}]
]""",
		"retreat": """[
[{"cmd": "move", "val": -100}]
]"""
	},
	
	# LLM_conversation.py 응답 (대화)
	"conversation": {
		"default": "Affirmative. I am VIRUS, ready for your command.",
		"hello": "Hello operator. VIRUS combat unit online and ready for deployment.",
		"attack": "Target acquired. Engaging hostile elements.",
		"retreat": "Tactical withdrawal initiated. Moving to safe position."
	},
	
	# VLM 응답 (이미지 분석)
	"vlm": {
		"default": "The environment appears to be a standard indoor area with no immediate threats or obstacles.",
		"person": "I detect one human figure standing approximately 3 meters ahead. No visible weapons or hostile intent.",
		"empty": "The area is clear of any human presence or significant objects.",
		"obstacle": "There appears to be furniture and various obstacles in the path ahead. Recommend cautious navigation."
	}
}

# 현재 선택된 응답 (키 저장)
CURRENT_SELECTIONS = {
	"commands": "default",
	"conversation": "default",
	"vlm": "default"
}
hub1 = HubController("hub1", "E0:FF:F1:59:8E:6A")
hub2 = HubController("hub2", "E0:FF:F1:58:52:A2")

# 2) face 처리 매니저 생성
face_mgr = MultiThreadManagerfaces()
def fake_convert_audio_to_text_via_api(audio_data, sample_rate):
	"""실제 Whisper API 대신 사용자가 입력한 텍스트를 반환합니다."""
	print("\n🎭 [FAKE] 실제 음성 변환 대신 사용자 입력을 사용합니다.")
	
	# 사용자 입력 요청
	print("\n🔤 텍스트 입력 (가상 음성 명령):")
	user_input = input("> ")
	
	# 특수 명령어 처리 (선택 변경)
	if user_input.startswith("/set"):
		try:
			_, category, selection = user_input.split(" ", 2)
			if category in CURRENT_SELECTIONS and selection in PREDEFINED_RESPONSES[category]:
				CURRENT_SELECTIONS[category] = selection
				print(f"✅ {category} 응답이 '{selection}'으로 설정되었습니다.")
			else:
				print(f"❌ 유효하지 않은 카테고리 또는 선택: {category} - {selection}")
				print(f"유효한 옵션: {list(PREDEFINED_RESPONSES.keys())} - {PREDEFINED_RESPONSES[category].keys() if category in PREDEFINED_RESPONSES else '없음'}")
		except ValueError:
			print("❌ 명령 형식 오류. 예: /set commands attack")
			print("가능한 명령:")
			for category, options in PREDEFINED_RESPONSES.items():
				print(f"  /set {category} [{' | '.join(options.keys())}]")
		return user_input
	
	# 사용자가 아무것도 입력하지 않으면 default 응답 사용을 안내
	if user_input.strip() == "":
		print("✅ 빈 입력이 감지되었습니다. 기본(default) 응답을 사용합니다.")
	
	return user_input

class MultiThreadManager:
	def __init__(self):
		self.vlm_thread = None
		self.vlm_result = None
		self.vlm_complete = threading.Event()
		
		self.conversation_thread = None
		self.conversation_result = None
		self.conversation_complete = threading.Event()
		
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
			# 실제 VLM 대신 미리 정의된 응답 사용
			print("\n🎭 [FAKE] 실제 VLM 분석 대신 미리 정의된 응답을 사용합니다.")
			selected_vlm = CURRENT_SELECTIONS["vlm"]
			result = PREDEFINED_RESPONSES["vlm"][selected_vlm]
			time.sleep(1)  # 잠시 지연하여 처리 중인 것처럼 보이게 함
			
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
			# 실제 LLM 호출 대신 미리 정의된 응답 사용
			print("\n🎭 [FAKE] 실제 LLM 대신 미리 정의된 대화 응답을 사용합니다.")
			selected_conversation = CURRENT_SELECTIONS["conversation"]
			conversation_response_text = PREDEFINED_RESPONSES["conversation"][selected_conversation]
			
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

# 가짜 process_for_commands 함수 (LLM_function.py 대체)
def fake_process_for_commands(text, additional_prompt=""):
	"""LLM_function.py의 process_voice_text 대체 함수"""
	print("\n🎭 [FAKE] 실제 LLM 대신 미리 정의된 명령 응답을 사용합니다.")
	selected_commands = CURRENT_SELECTIONS["commands"]
	return PREDEFINED_RESPONSES["commands"][selected_commands]

# 가짜 process_for_conversation 함수 (LLM_conversation.py 대체)
def fake_process_for_conversation(text, additional_prompt=""):
	"""LLM_conversation.py의 process_voice_text 대체 함수"""
	print("\n🎭 [FAKE] 실제 LLM 대신 미리 정의된 대화 응답을 사용합니다.")
	selected_conversation = CURRENT_SELECTIONS["conversation"]
	return PREDEFINED_RESPONSES["conversation"][selected_conversation]

manager = MultiThreadManager()

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
SILENCE_DURATION = 2.0  # 녹음 종료를 위한 침묵 지속 시간(초) - 빠른 응답을 위해 1초로 단축

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
	global frames, recording, recording_start_time, silence_start_time, last_db_print_time, last_countdown_time, recording_completed, record_count, manager, api_lock, processing_audio
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

		manager.start_vlm_processing()  # VLM 처리 활성화
		
	# 녹음 중일 때
	if recording:
		frames.append(indata.copy())
		record_count+=1
		
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
	manager.start_vlm_processing()  # VLM 처리 활성화
	vlm_result = manager.get_vlm_result(timeout=40)
	if vlm_result:
		print(f"🎯 VLM analysis complete: {vlm_result[:100]}..." if len(vlm_result) > 100 else f"🎯 VLM analysis complete: {vlm_result}")
	else:
		print("⚠️ VLM processing timeout or failed")
	
	# Convert audio data to numpy array
	print("\n📊 Preparing audio data for transcription...")
	audio_data = np.concatenate(frames, axis=0)

	# 1. Convert audio to text using Whisper API (가짜 함수로 대체)
	print("\n🎙️ Converting speech to text (사용자 입력으로 대체됨)...")
	transcribed_text = fake_convert_audio_to_text_via_api(audio_data, SAMPLE_RATE)

	if transcribed_text and not transcribed_text.startswith("/set"):
		print(f"✅ 입력된 텍스트: \"{transcribed_text}\"")

		# 2. Start conversation processing using the transcribed text (threaded)
		print("\n🤖 Generating VIRUS conversational response (async thread)...")
		manager.start_text_conversation_processing(transcribed_text, vlm_result)

		# 3. Process command interpretation using the transcribed text
		print("⚙️ Interpreting robot commands...")
		command_response_json = None
		try:
			# 실제 process_for_commands 대신 가짜 함수 사용
			command_response_json = fake_process_for_commands(
				transcribed_text,
				additional_prompt=f"[Image/Video Description]: {vlm_result}"
			)
			print(f"→ Robot command generated: {command_response_json}")
		except Exception as e:
			print(f"❌ Command processing error: {e}")
			command_response_json = None
	else:
		if not transcribed_text:
			print("⚠️ No transcribed text available for command processing")
		else:
			print("⚠️ 설정 명령이 입력되었습니다. 명령 처리를 건너뜁니다.")
		
	if command_response_json and not transcribed_text.startswith("/set"):
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
	
	# 자동 녹음 대신 사용자 입력 프롬프트 표시
	print("\n🎭 [FAKE] 실제 음성 입력 대신 키보드 입력을 받습니다.")
	print("현재 모든 카테고리는 'default' 응답을 사용하도록 설정되어 있습니다.")
	print("명령을 입력하려면 Enter 키를 누르세요.")
	
	while True:
		try:
			choice = input("\n🎤 Enter 키를 눌러 기본 명령 실행 또는 '/set'으로 응답 변경 (종료: Ctrl+C): ")
			
			# '/set' 명령어가 아닐 경우 바로 default 응답 실행
			if not choice.startswith('/set'):
				frames.clear()  # 프레임 초기화
				frames.append(np.zeros((1000, 1), dtype=np.float32))  # 더미 오디오 데이터
				
				# '/set' 명령어 없이 바로 default 응답 사용
				if choice.strip() == '':
					print("\n✅ 기본(default) 응답을 사용합니다.")
					process_recorded_audio()
				else:
					# 사용자가 텍스트를 입력한 경우 해당 텍스트로 처리
					frames.clear()
					frames.append(np.zeros((1000, 1), dtype=np.float32))
					process_recorded_audio()
			else:
				# '/set' 명령어 처리 유지
				try:
					_, category, selection = choice.split(" ", 2)
					if category in CURRENT_SELECTIONS and selection in PREDEFINED_RESPONSES[category]:
						CURRENT_SELECTIONS[category] = selection
						print(f"✅ {category} 응답이 '{selection}'으로 설정되었습니다.")
					else:
						print(f"❌ 유효하지 않은 카테고리 또는 선택: {category} - {selection}")
						print(f"유효한 옵션: {list(PREDEFINED_RESPONSES.keys())} - {PREDEFINED_RESPONSES[category].keys() if category in PREDEFINED_RESPONSES else '없음'}")
				except ValueError:
					print("❌ 명령 형식 오류. 예: /set commands attack")
					print_help()
		except KeyboardInterrupt:
			print("\n🔌 Shutting down system.")
			break

def print_help():
	"""사용 가능한 명령어와 설정 옵션을 출력합니다."""
	print("\n" + "=" * 50)
	print("🔧 가짜 VIRUS 시스템 명령어")
	print("=" * 50)
	print("일반 텍스트를 입력하면 명령으로 처리됩니다.")
	print("\n특수 명령어:")
	print("  /set [category] [selection] - 응답 유형 설정")
	print("  예: /set commands attack")
	
	print("\n사용 가능한 카테고리 및 선택 옵션:")
	for category, options in PREDEFINED_RESPONSES.items():
		print(f"  {category}: {', '.join(options.keys())}")
	
	print("\n현재 설정:")
	for category, selection in CURRENT_SELECTIONS.items():
		print(f"  {category}: {selection}")
	print("=" * 50)

def run_spike(llmcmd='[[ { "cmd": "shoot",    "val":  0 }]]'):
	# 1) 허브 컨트롤러 두 개 생성
	

	# 3) 연결 확인
	if not hub1.sock or not hub2.sock:
		print("연결 실패! 프로그램을 종료합니다.")
		return

	# 4) 사용자 입력 또는 인자로 받은 llmcmd 사용
	if llmcmd:
		cmd_input = llmcmd.strip()
	else:
		cmd_input = input("명령 입력 (엔터 시 샘플 명령 사용): ").strip()
		if not cmd_input:
			# 엔터만 쳤을 때, 두 허브용 샘플 명령을 묶어서 보낸다는 가정
			# (실제 애플리케이션 논리에 맞게 수정 가능)
			# 예를 들어, 샘플을 "hub1→hub2"로 동일하게 보내려면 다음과 같이:
			cmd_input = SAMPLE_COMMANDS["hub1"]

	# 5) JSON 파싱
	try:
		# cmd_input은 예: '[ [ {...} ], [ {...} ] ]' 형태여야 함
		# 최상위 객체가 리스트(list)이어야 for문이 정상 동작
		parsed_cmd_list = json.loads(cmd_input)
		if not isinstance(parsed_cmd_list, list):
			raise ValueError("최상위 JSON 객체가 리스트가 아닙니다.")
	except Exception as e:
		print(f"JSON 파싱 오류: {e}")
		return

	# 6) 명령 순차 처리
	try:
		for single_cmd in parsed_cmd_list:
			# single_cmd는 이제 Python 리스트 자료구조: [ { "cmd": "...", "val": ... }, ... ]
			if not isinstance(single_cmd, list):
				print(f"잘못된 명령 형식: {single_cmd} (리스트가 아님)")
				continue

			# 6-1) 이 명령 블록에 "shoot, val=0" 조건이 있는지 검사
			is_shoot_zero = False
			for cmd_dict in single_cmd:
				cmd_name = cmd_dict.get("cmd")
				cmd_val  = cmd_dict.get("val")

				# JSON에서 val이 문자열로 왔을 수도 있으므로 int 변환 시도
				try:
					val_int = int(cmd_val)
				except:
					val_int = None

				if cmd_name == "shoot" and val_int == 0:
					is_shoot_zero = True
					break

			# 6-2) "shoot val=0" 이면 face 처리 시작
			if is_shoot_zero:
				face_mgr.start_face_processing()
				result = face_mgr.get_face_result(timeout=10)
				if result is None:
					print("[face] 결과를 얻지 못했습니다. 기본 shoot 커맨드만 전송합니다.")
					# 예: 아무 대상 지정 없이 허브에 shoot=1 전송
					fallback_json = json.dumps([{"cmd": "shoot", "val": 1}])
					t1 = threading.Thread(target=hub1.send_single_command, args=(fallback_json,))
					t2 = threading.Thread(target=hub2.send_single_command, args=(fallback_json,))
					t1.start(); t2.start()
					t1.join(timeout = 15); t2.join(timeout = 15)
				else:
					# face_result가 JSON 문자열이라고 가정
					"""try:
						face_list = json.loads(result)
						# face_list는 [ { "label": "...", "center": [x, y] }, ... ] 형태
					except Exception as e:
						print(f"[face] result JSON 파싱 오류: {e}\n raw result: {result}")
						face_list = []"""

					# 예: "label == 'enemy'" 인 것만 처리
					for detect in result:
						r = detect.get("label") 
						if r == "enemy" or r == "Jeoung":
							center = detect.get("center", [0, 0])
							x, y = center[0], center[1]

							# 픽셀 좌표를 각도로 변환
							# 화면 중앙을 (320, 240)으로 보고, 상대 좌표 계산
							rel_x = 320 - x  # 중앙으로부터의 x 거리
							rel_y = 240 - y  # 중앙으로부터의 y 거리
							
							# 화각을 기준으로 각도 계산 (예: 수평 60도, 수직 45도 시야각 가정)
							# 1픽셀당 각도 = 시야각 / 해상도
							angle_x = (rel_x * 60) / 1000  # 수평각: ±30도
							angle_y = (rel_y * 45) / 500  # 수직각: ±22.5도

							# 회전 명령 전송 (한번만 회전)
							rotation_cmd = json.dumps([
								{"cmd": "rotate_x", "val": angle_x},
								{"cmd": "rotate_y", "val": angle_y}
							])
							shoot_cmd = json.dumps([{"cmd": "shoot", "val": 1}])
							return_cmd = json.dumps([
								{"cmd": "rotate_x", "val": -angle_x},
								{"cmd": "rotate_y", "val": -angle_y}
							])

							# 1. 타겟 방향으로 회전
							t1 = threading.Thread(target=hub1.send_single_command, args=(rotation_cmd,))
							t2 = threading.Thread(target=hub2.send_single_command, args=(rotation_cmd,))
							t1.start(); t2.start()
							t1.join(timeout = 15); t2.join(timeout = 15)

							# 2. 발사
							t1 = threading.Thread(target=hub1.send_single_command, args=(shoot_cmd,))
							t2 = threading.Thread(target=hub2.send_single_command, args=(shoot_cmd,))
							t1.start(); t2.start()
							t1.join(timeout = 15); t2.join(timeout = 15)

							# 3. 원위치로 복귀
							time.sleep(0.5)  # 발사 동작이 완료될 때까지 잠시 대기
							t1 = threading.Thread(target=hub1.send_single_command, args=(return_cmd,))
							t2 = threading.Thread(target=hub2.send_single_command, args=(return_cmd,))
							t1.start(); t2.start()
							t1.join(timeout = 15); t2.join(timeout = 15)
							
							# 첫 번째 enemy만 처리하고 종료
							break
					# 만약 적(enemy)이 한 명도 안 잡혔으면, 기본 shoot만 보내도 됨
					# if not any(d.get("label") == "enemy" for d in result):
					#     fallback_json = json.dumps([{"cmd": "shoot", "val": 1}])
					#     t1 = threading.Thread(target=hub1.send_single_command, args=(fallback_json,))
					#     t2 = threading.Thread(target=hub2.send_single_command, args=(fallback_json,))
					#     t1.start(); t2.start()
					#     t1.join(); t2.join()

			# 6-3) "shoot val=0"이 아니면, 단순히 이 명령 블록 자체를 허브들로 전송
			else:
				# single_cmd는 Python 리스트 객체이므로, 반드시 JSON 문자열로 직렬화
				json_payload = json.dumps(single_cmd)
				t1 = threading.Thread(target=hub1.send_single_command, args=(json_payload,))
				t2 = threading.Thread(target=hub2.send_single_command, args=(json_payload,))
				t1.start(); t2.start()
				t1.join(timeout = 15); t2.join(timeout = 15)
	except KeyboardInterrupt:
		print("\n프로그램 강제 종료.")

if __name__ == "__main__":
	# Display welcome message
	print("=" * 50)
	print("가짜 VIRUS COMBAT ROBOT CONTROL SYSTEM")
	print("Versatile, Intelligent Robotic Unit for Strategy")
	print("=" * 50)
	print("이 시스템은 실제 LLM/VLM 대신 사용자가 미리 정의한 응답을 사용합니다.")
	print("엔터키만 누르면 바로 기본(default) 응답이 실행됩니다.")
	print("응답을 변경하고 싶으면 다음 명령을 사용하세요: /set [category] [selection]")
	print("예: /set commands attack")
	print("   /set conversation hello")
	print("   /set vlm person")
	print("\n현재 설정된 응답:")
	for category, selection in CURRENT_SELECTIONS.items():
		print(f"  - {category}: {selection}")
	print("\n사용 가능한 선택지 목록을 보려면 다음을 입력하세요: /help")
	print("=" * 50)
	
	# Start the interaction loop
	process_complete_interaction()

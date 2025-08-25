#!/usr/bin/env python3
"""
ElevenLabs Text-to-Speech Generator
==================================
사용자가 지정한 텍스트를 ElevenLabs API를 사용하여 고품질 오디오로 변환합니다.

Requirements:
    pip install elevenlabs python-dotenv

Usage:
    python elevenlabs_tts.py "텍스트를 여기에 입력하세요"
    또는
    python elevenlabs_tts.py  # 대화형 모드
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save

class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech 클래스"""
    
    # 추천 음성 옵션
    POPULAR_VOICES = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",      # 여성, 미국 억양
        "dave": "CYw3kZ02Hs0563khs1Fj",        # 남성, 영국 억양  
        "fin": "D38z5RcWu1voky8WS1ja",         # 남성, 아일랜드 억양
        "sarah": "EXAVITQu4vr4xnSDxMaL",       # 여성, 미국 억양
        "antoni": "ErXwobaYiN019PkySvjV",      # 남성, 미국 억양
        "josh": "TxGEqnHWrfWFTfGW9XjX",        # 남성, 미국 억양
        "arnold": "VR6AewLTigWG4xSOukaG",      # 남성, 미국 억양
        "adam": "pNInz6obpgDQGcFmaJgB",        # 남성, 미국 억양
        "sam": "yoZ06aMxZJJ28mfd3POQ",         # 남성, 미국 억양
        "bella": "EXAVITQu4vr4xnSDxMaL",       # 여성, 미국 억양
    }
    
    # 사용 가능한 모델
    MODELS = {
        "multilingual_v2": "eleven_multilingual_v2",    # 최고 품질 (기본값)
        "flash_v2.5": "eleven_flash_v2_5",              # 저지연 (75ms)
        "turbo_v2.5": "eleven_turbo_v2_5",              # 균형 잡힌 품질과 속도
    }
    
    # 출력 포맷
    OUTPUT_FORMATS = {
        "mp3_high": "mp3_44100_128",      # 고품질 MP3 (기본값)
        "mp3_medium": "mp3_44100_64",     # 중간 품질 MP3
        "mp3_low": "mp3_22050_32",        # 저품질 MP3 (빠름)
        "wav": "pcm_44100",               # WAV 형식
    }

    def __init__(self, api_key: str = None):
        """
        ElevenLabsTTS 초기화
        
        Args:
            api_key (str): ElevenLabs API 키. None이면 환경변수에서 로드
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ElevenLabs API 키가 필요합니다. "
                ".env 파일에 ELEVENLABS_API_KEY를 설정하거나 매개변수로 전달하세요."
            )
        
        self.client = ElevenLabs(api_key=self.api_key)
        print("✅ ElevenLabs 클라이언트 초기화 완료")

    def list_voices(self):
        """사용 가능한 음성 목록 출력"""
        try:
            response = self.client.voices.get_all()
            print("\n🎤 사용 가능한 음성:")
            print("-" * 60)
            
            for voice in response.voices:
                labels = [label.name for label in voice.labels.values()] if voice.labels else []
                category = voice.category if hasattr(voice, 'category') else 'Unknown'
                
                print(f"• {voice.name:<15} | ID: {voice.voice_id}")
                print(f"  └─ Category: {category}, Labels: {', '.join(labels) or 'None'}")
                
        except Exception as e:
            print(f"❌ 음성 목록 로드 오류: {e}")

    def text_to_speech(
        self, 
        text: str, 
        voice: str = "antoni",
        model: str = "multilingual_v2", 
        output_file: str = None,
        play_audio: bool = True
    ):
        """
        텍스트를 음성으로 변환
        
        Args:
            text (str): 변환할 텍스트
            voice (str): 사용할 음성 (이름 또는 ID)
            model (str): 사용할 모델
            output_file (str): 저장할 파일명 (없으면 자동 생성)
            play_audio (bool): 생성 후 자동 재생 여부
        
        Returns:
            str: 생성된 오디오 파일 경로
        """
        try:
            # 음성 ID 확인
            voice_id = self.POPULAR_VOICES.get(voice.lower(), voice)
            
            # 모델 ID 확인
            model_id = self.MODELS.get(model.lower(), model)
            
            # 출력 포맷 고정 (고품질 MP3)
            output_format = "mp3_high"
            format_string = self.OUTPUT_FORMATS[output_format]
            
            print(f"🔄 텍스트를 음성으로 변환 중...")
            print(f"  📝 텍스트: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            print(f"  🎤 음성: {voice} ({voice_id})")
            print(f"  🤖 모델: {model} ({model_id})")
            print(f"  📁 포맷: {output_format} ({format_string}) - 고품질 고정")
            
            # 텍스트를 음성으로 변환 (속도 조절 추가)
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format=format_string,
                voice_settings={
                    "stability": 1,
                    "similarity_boost": 1,
                    "style": 0,
                    "use_speaker_boost": True,
                    "speed": 0.7
                }
            )
            
            # 출력 파일명 고정
            if not output_file:
                output_file = "wait.mp3"
            
            # 파일 저장
            output_path = Path(output_file)
            save(audio, str(output_path))
            
            print(f"✅ 오디오 파일 생성 완료: {output_path.absolute()}")
            
            # 자동 재생
            if play_audio:
                try:
                    print("🔊 오디오 재생 중...")
                    play(audio)
                except Exception as e:
                    print(f"⚠️ 오디오 재생 실패: {e}")
                    print("💡 해결방법:")
                    print("  - Windows: winget install ffmpeg")
                    print("  - 또는 pygame 사용: pip install pygame")
                    print("파일이 저장되었으므로 수동으로 재생하실 수 있습니다.")
            
            return str(output_path.absolute())
            
        except Exception as e:
            print(f"❌ 오디오 생성 오류: {e}")
            return None

    def get_voice_info(self, voice_name: str):
        """특정 음성의 정보 출력"""
        voice_id = self.POPULAR_VOICES.get(voice_name.lower(), voice_name)
        
        try:
            voice = self.client.voices.get(voice_id)
            print(f"\n🎤 음성 정보: {voice.name}")
            print(f"  📋 ID: {voice_id}")
            print(f"  🏷️ Category: {getattr(voice, 'category', 'Unknown')}")
            
            if hasattr(voice, 'labels') and voice.labels:
                labels = [label.name for label in voice.labels.values()]
                print(f"  🔖 Labels: {', '.join(labels)}")
            
            if hasattr(voice, 'description') and voice.description:
                print(f"  📝 Description: {voice.description}")
                
        except Exception as e:
            print(f"❌ 음성 정보 로드 오류: {e}")


def main():
    """메인 함수"""
    # 미리 정의된 wait.mp3용 대기 메시지
    DEFAULT_WAIT_TEXT = "Processing your request, please wait..."

    parser = argparse.ArgumentParser(
        description="ElevenLabs Text-to-Speech Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python elevenlabs_tts.py                              # 자동으로 wait.mp3 생성
  python elevenlabs_tts.py "안녕하세요! 이것은 테스트입니다."
  python elevenlabs_tts.py "Hello World" --voice antoni --model flash_v2.5
  python elevenlabs_tts.py --list-voices
  python elevenlabs_tts.py --interactive
  (출력 포맷은 고품질 MP3로 고정됨)
        """
    )
    
    parser.add_argument("text", nargs="?", help="변환할 텍스트 (없으면 자동으로 wait.mp3 생성)")
    parser.add_argument("--voice", "-v", default="antoni",
                       help="사용할 음성 (기본값: antoni)")
    parser.add_argument("--model", "-m", default="multilingual_v2",
                       help="사용할 모델 (기본값: multilingual_v2)")
    parser.add_argument("--output", "-o", help="출력 파일명")
    parser.add_argument("--no-play", action="store_true",
                       help="생성 후 자동 재생 하지 않음")
    parser.add_argument("--list-voices", action="store_true",
                       help="사용 가능한 음성 목록 출력")
    parser.add_argument("--voice-info", help="특정 음성의 정보 출력")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="대화형 모드")
    
    args = parser.parse_args()
    
    try:
        tts = ElevenLabsTTS()
        
        # 음성 목록 출력
        if args.list_voices:
            tts.list_voices()
            return
        
        # 음성 정보 출력
        if args.voice_info:
            tts.get_voice_info(args.voice_info)
            return
        
        # 대화형 모드
        if args.interactive:
            print("🎤 ElevenLabs TTS 대화형 모드")
            print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
            print("-" * 50)
            
            while True:
                text = input("\n📝 변환할 텍스트를 입력하세요: ").strip()
                
                if text.lower() in ['quit', 'exit', '종료']:
                    print("👋 프로그램을 종료합니다.")
                    break
                
                if not text:
                    print("❌ 텍스트를 입력해주세요.")
                    continue
                
                tts.text_to_speech(
                    text=text,
                    voice=args.voice,
                    model=args.model,
                    output_file=args.output,
                    play_audio=not args.no_play
                )
            return
        
        # 단일 변환
        if args.text:
            tts.text_to_speech(
                text=args.text,
                voice=args.voice,
                model=args.model,
                output_file=args.output,
                play_audio=not args.no_play
            )
        else:
            # 텍스트가 없으면 자동으로 wait.mp3 생성
            print("🎤 자동으로 wait.mp3 생성 중...")
            print(f"📝 미리 정의된 대기 메시지: '{DEFAULT_WAIT_TEXT}'")
            tts.text_to_speech(
                text=DEFAULT_WAIT_TEXT,
                voice=args.voice,
                model=args.model,
                output_file=args.output or "wait.mp3",  # 명시적으로 wait.mp3 지정
                play_audio=not args.no_play
            )
                
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
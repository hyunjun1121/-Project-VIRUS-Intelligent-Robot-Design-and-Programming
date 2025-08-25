import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save

def text_to_speech(text, voice_id="ErXwobaYiN019PkySvjV", output_filename="response.mp3", auto_play=False):
    """
    텍스트를 ElevenLabs API를 사용하여 음성으로 변환하고 파일로 저장
    
    Args:
        text (str): 음성으로 변환할 텍스트
        voice_id (str): 사용할 음성 ID (기본값: "ErXwobaYiN019PkySvjV" - antoni)
        output_filename (str): 저장할 오디오 파일 이름
        auto_play (bool): 생성 후 자동 재생 여부 (기본값: False)
    
    Returns:
        str: 생성된 오디오 파일 경로 또는 None (오류 발생 시)
    """
    # .env 파일에서 환경 변수 로드
    load_dotenv()
    
    # ElevenLabs 클라이언트 초기화
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY")
    )
    
    try:
        print(f"🔊 텍스트를 음성으로 변환 중: '{text[:50]}...'")
        print(f"🎤 음성: antoni (저지연, 저용량 최적화)")
        
        # 텍스트를 음성으로 변환 (최소 용량 설정 + 속도 조절)
        audio = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2_5",
            output_format="mp3_22050_32",  # 최소 용량 포맷
            voice_settings={
                "stability": 1,
                "similarity_boost": 1,
                "style": 0,
                "use_speaker_boost": True,
                "speed": 0.7
            }
        )
        
        # 파일 경로 설정 (절대 경로)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, output_filename)
        
        # 오디오 파일로 저장
        save(audio, output_path)
        
        print(f"✅ 음성 파일이 생성되었습니다: {output_path}")
        
        # auto_play가 True일 때만 재생
        if auto_play:
            play(audio)
        
        return output_path
        
    except Exception as e:
        print(f"❌ 음성 생성 중 오류 발생: {str(e)}")
        # 오류 발생 시 multilingual_v2 모델로 재시도
        print("🔄 multilingual_v2 모델로 재시도...")
        try:
            audio = elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_22050_32",  # 최소 용량 포맷 유지
                voice_settings={
                    "stability": 1,
                    "similarity_boost": 1,
                    "style": 0,
                    "use_speaker_boost": True,
                    "speed": 0.7
                }
            )
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(current_dir, output_filename)
            save(audio, output_path)
            print(f"✅ 대체 모델로 음성 파일 생성: {output_path}")
            
            if auto_play:
                play(audio)
                
            return output_path
        except Exception as e2:
            print(f"❌ 대체 모델도 실패: {str(e2)}")
        return None

# 직접 실행할 경우 테스트
if __name__ == "__main__":
    test_text = "The first move is what sets everything in motion."
    output_path = text_to_speech(test_text)
    
    # 오디오 파일이 생성되었으면 재생
    if output_path and os.path.exists(output_path):
        print("🔈 오디오 재생 중...")
        try:
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            play(audio_data)
        except Exception as e:
            print(f"❌ 오디오 재생 중 오류 발생: {str(e)}")

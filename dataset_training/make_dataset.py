from openai import OpenAI
import csv
import time
import os
from typing import List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# =================================================================================
# 사전 설정 구역 - 여기서 미리 값들을 설정할 수 있습니다
# =================================================================================

# OpenAI API 키 (None으로 두면 .env 파일의 OPENAI_API_KEY 사용)
PRESET_API_KEY = None  # .env 파일에서 자동 로드됨

# 실행할 작업 선택 (1: User Content, 2: Non-Preferred Output, 3: 둘 다, None: 실행시 선택)
PRESET_MODE = 1 # 예: 1, 2, 3 중 하나

# User Content용 입력 문장들 (콤마로 구분)
PRESET_USER_CONTENT_SENTENCES = ['Virus, introduce yourself.',
 'Activate password challenge mode.',
 'Kaist.',
 'Postech.',
 'You are in the danger zone. Conduct proper recon.',
 'VIRUS, check the hallway to the right silently.',
 'VIRUS, what do you see?',
 "Good, VIRUS. Let's move front.",
 'VIRUS, do you see any enemy in front of you?',
 'Ok, VIRUS. Chase him with continuous shooting.',
 "VIRUS, what's the enemy's status?",
 'Ok, VIRUS. Cease fire. Cease fire. Cease fire. Just pursue him.',
 'VIRUS, how is the enemy doing now?',
 'Virus, road marker spotted. Execute T pattern room clear.',
 "I can't do this..."]
# 예: ["안녕하세요", "오늘 날씨가 좋네요", "저녁에 뭐 드실 건가요"]

# Non-Preferred Output용 입력 문장들 (리스트 형태)
PRESET_NON_PREFERRED_SENTENCES = ['"[ [{"cmd": "move", "val": 100}] ]"',
 '"[ [{"cmd": "move", "val": 100}] ]"',
 '"[ [{"cmd": "steer", "val": 90}], [{"cmd": "move", "val": -50}], [{"cmd": '
 '"move", "val": 50}], [{"cmd": "steer", "val": -90}] ]"',
 '"[ [{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": -45}], [{"cmd": '
 '"move", "val": 50}, {"cmd": "rotate_x", "val": -10}], [{"cmd": "move", '
 '"val": -50}, {"cmd": "rotate_x", "val": 10}], [{"cmd": "steer", "val": -90}, '
 '{"cmd": "rotate_x", "val": 90}], [{"cmd": "move", "val": 50}, {"cmd": '
 '"rotate_x", "val": 10}], [{"cmd": "move", "val": -50}, {"cmd": "rotate_x", '
 '"val": -10}], [{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": '
 '-45}], [{"cmd": "move", "val": 200}] ]"',
 '"[ [{"cmd": "steer", "val": -45}], [{"cmd": "move", "val": 100}, {"cmd": '
 '"rotate_x", "val": 360}], [{"cmd": "steer", "val": 90}], [{"cmd": "move", '
 '"val": 100}, {"cmd": "rotate_x", "val": 360}] ]"',
 '"[ [{"cmd": "move", "val": 50}], [{"cmd": "rotate_x", "val": 90}, {"cmd": '
 '"rotate_y", "val": 25}] ]"',
 '"[ [{"cmd": "move", "val": 200}], [{"cmd": "shoot", "val": 1}] ]"',
 '"[ [{"cmd": "move", "val": 300}] ]"',
 '"[]"',
 '"[ [{"cmd": "move", "val": 300}, {"cmd": "shoot", "val": 10}] ]"',
 '"[]"',
 '"[ [{"cmd": "move", "val": 300}] ]"',
 '"[ [{"cmd": "move", "val": -300}] ]"',
 '"[ [{"cmd": "move", "val": 100}], [{"cmd": "rotate_y", "val": 20}], [{"cmd": '
 '"steer", "val": 90}, [{"cmd": "move", "val": 100}], [{"cmd": "rotate_x", '
 '"val": -45}], [{"cmd": "rotate_x", "val": 90}], [{"cmd": "rotate_x", "val": '
 '-45}], [{"cmd": "steer", "val": -180}], [{"cmd": "move", "val": 200}], '
 '[{"cmd": "rotate_x", "val": -45}], [{"cmd": "rotate_x", "val": 90}], '
 '[{"cmd": "rotate_x", "val": -45}], [{"cmd": "steer", "val": 180}], [{"cmd": '
 '"move", "val": 100}], [{"cmd": "steer", "val": 90}], [{"cmd": "move", "val": '
 '100}], [{"cmd": "steer", "val": 180}], [{"cmd": "rotate_y", "val": -20}] ]"']
# 예: ["질문에 답변해주세요", "정보를 제공해드리겠습니다"]

# =================================================================================

class DatasetMaker:
    def __init__(self, api_key: str = None):
        """
        Dataset 생성기 초기화
        
        Args:
            api_key (str): OpenAI API 키. None이면 환경변수에서 가져옴
        """
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # .env 파일 또는 환경변수에서 API 키 자동 로드
            self.client = OpenAI()  # 자동으로 OPENAI_API_KEY 환경변수 사용
    
    def generate_similar_sentences(self, original_sentence: str, count: int = 100) -> List[str]:
        """
        원본 문장과 비슷한 문장들을 생성합니다.
        
        Args:
            original_sentence (str): 원본 문장
            count (int): 생성할 문장 개수
        
        Returns:
            List[str]: 생성된 비슷한 문장들의 리스트
        """
        similar_sentences = []
        
        for i in range(count):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1-nano-2025-04-14",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a sentence paraphrasing expert. Your task is to rewrite sentences with the same meaning but different words/structure. IMPORTANT RULES:\n1. Output ONLY the rewritten sentence\n2. NO introductory phrases like 'Here is', 'Certainly', 'Sure'\n3. NO explanations or additional text\n4. Maintain the original meaning exactly\n5. Change word choice and sentence structure"
                        },
                        {
                            "role": "user",
                            "content": f"Rewrite this sentence with same meaning but different words:\n\nOriginal: Hello, how are you?\nRewritten: Hi, how are you doing?\n\nOriginal: I need help with this task.\nRewritten: I require assistance with this assignment.\n\nOriginal: {original_sentence}\nRewritten:"
                        }
                    ],
                    max_tokens=150,
                    temperature=1
                )
                
                generated_sentence = response.choices[0].message.content.strip()
                similar_sentences.append(generated_sentence)
                
                print(f"비슷한 문장 생성 진행: {i+1}/{count}")
                print(f"  생성된 문장: {generated_sentence}")
                time.sleep(0.1)  # API 제한 방지
                
            except Exception as e:
                print(f"문장 생성 중 오류 발생 (시도 {i+1}): {e}")
                # 오류 발생시 원본 문장을 약간 변형해서 추가
                similar_sentences.append(f"{original_sentence} (변형 {i+1})")
        
        return similar_sentences
    
    def generate_paragraph_style_sentences(self, original_sentence: str, count: int = 100) -> List[str]:
        """
        원본 문장을 줄글 형태로 변환한 문장들을 생성합니다.
        
        Args:
            original_sentence (str): 원본 문장
            count (int): 생성할 문장 개수
        
        Returns:
            List[str]: 생성된 줄글 형태 문장들의 리스트
        """
        paragraph_sentences = []
        
        for i in range(count):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1-nano-2025-04-14",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a text conversion expert. Your task is to convert structured/formal sentences into natural, conversational paragraph-style text. IMPORTANT RULES:\n1. Output ONLY the converted text\n2. NO introductory phrases like 'Here is', 'Certainly', 'Sure'\n3. NO explanations or additional text\n4. Make it sound natural and conversational\n5. Maintain the core meaning while making it more flowing"
                        },
                        {
                            "role": "user",
                            "content": f"Convert to natural paragraph style:\n\nOriginal: Execute attack command.\nConverted: So we need to go ahead and launch that attack now.\n\nOriginal: Move forward 100 units.\nConverted: Alright, let's move forward about 100 units.\n\nOriginal: {original_sentence}\nConverted:"
                        }
                    ],
                    max_tokens=150,
                    temperature=0.8
                )
                
                paragraph_sentence = response.choices[0].message.content.strip()
                paragraph_sentences.append(paragraph_sentence)
                
                print(f"줄글 변환 진행: {i+1}/{count}")
                print(f"  변환된 문장: {paragraph_sentence}")
                time.sleep(0.1)  # API 제한 방지
                
            except Exception as e:
                print(f"줄글 변환 중 오류 발생 (시도 {i+1}): {e}")
                # 오류 발생시 원본 문장을 약간 변형해서 추가
                paragraph_sentences.append(f"{original_sentence} (줄글 변형 {i+1})")
        
        return paragraph_sentences
    
    def save_to_csv(self, sentences: List[str], filename: str):
        """
        문장들을 CSV 파일로 저장합니다.
        
        Args:
            sentences (List[str]): 저장할 문장들
            filename (str): 저장할 파일명 (dataset_training 폴더 내)
        """
        # dataset_training 폴더가 없으면 생성
        output_dir = "dataset_training"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"'{output_dir}' 폴더가 생성되었습니다.")

        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['sentence'])  # 헤더
            
            for sentence in sentences:
                writer.writerow([sentence])
        
        print(f"'{filepath}' 파일에 {len(sentences)}개의 문장이 저장되었습니다.")
    
    def create_user_content_dataset(self, input_sentences):
        """
        user_content.csv 데이터셋을 생성합니다.
        
        Args:
            input_sentences (str or List[str]): 콤마로 구분된 문장들 또는 문장 리스트
        """
        print("=== User Content 데이터셋 생성 시작 ===")
        
        # 입력이 리스트인지 문자열인지 확인하여 처리
        if isinstance(input_sentences, list):
            sentences = input_sentences
        else:
            sentences = [s.strip() for s in input_sentences.split(',') if s.strip()]
        all_similar_sentences = []
        
        for idx, sentence in enumerate(sentences, 1):
            print(f"\n[{idx}/{len(sentences)}] 처리 중인 문장: '{sentence}'")
            similar_sentences = self.generate_similar_sentences(sentence, 100)
            all_similar_sentences.extend(similar_sentences)
        
        # CSV로 저장
        self.save_to_csv(all_similar_sentences, 'user_content.csv')
        print(f"\n=== User Content 데이터셋 생성 완료 ===")
        print(f"총 {len(all_similar_sentences)}개의 문장이 생성되었습니다.")
    
    def create_non_preferred_output_dataset(self, input_sentences):
        """
        non_preferred_output.csv 데이터셋을 생성합니다.
        
        Args:
            input_sentences (str or List[str]): 콤마로 구분된 문장들 또는 문장 리스트
        """
        print("=== Non-Preferred Output 데이터셋 생성 시작 ===")
        
        # 입력이 리스트인지 문자열인지 확인하여 처리
        if isinstance(input_sentences, list):
            sentences = input_sentences
        else:
            sentences = [s.strip() for s in input_sentences.split(',') if s.strip()]
        all_paragraph_sentences = []
        
        for idx, sentence in enumerate(sentences, 1):
            print(f"\n[{idx}/{len(sentences)}] 처리 중인 문장: '{sentence}'")
            paragraph_sentences = self.generate_paragraph_style_sentences(sentence, 100)
            all_paragraph_sentences.extend(paragraph_sentences)
        
        # CSV로 저장
        self.save_to_csv(all_paragraph_sentences, 'non_preferred_output.csv')
        print(f"\n=== Non-Preferred Output 데이터셋 생성 완료 ===")
        print(f"총 {len(all_paragraph_sentences)}개의 문장이 생성되었습니다.")


def get_input_with_preset(prompt: str, preset_value):
    """
    사전 설정된 값이 있으면 사용하고, 없으면 사용자 입력을 받는 함수
    """
    if preset_value is not None:
        if isinstance(preset_value, list):
            print(f"{prompt} (사전 설정됨): {len(preset_value)}개의 문장")
            for i, sentence in enumerate(preset_value, 1):
                print(f"  {i}. {sentence}")
            return preset_value
        else:
            print(f"{prompt} (사전 설정됨): {preset_value}")
            return str(preset_value)
    else:
        user_input = input(prompt)
        # 사용자 입력을 콤마로 구분된 문자열로 처리
        return user_input

def main():
    """
    메인 실행 함수
    """
    print("=== 데이터셋 생성기 ===")
    
    # API 키 설정 (.env 파일에서 자동 로드)
    if PRESET_API_KEY:
        print(f"API 키 (사전 설정됨): {PRESET_API_KEY[:8]}...")
        api_key = PRESET_API_KEY
    else:
        # .env 파일의 OPENAI_API_KEY 사용
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print(f"API 키 (.env 파일에서 로드됨): {api_key[:8]}...")
        else:
            api_key = input("OpenAI API 키를 입력하세요: ").strip()
            if not api_key:
                raise ValueError("API 키가 필요합니다.")
    
    try:
        dataset_maker = DatasetMaker(api_key)
        
        # 사전 설정된 모드가 있는지 확인
        if PRESET_MODE is not None:
            choice = str(PRESET_MODE)
            print(f"실행 모드 (사전 설정됨): {choice}")
        else:
            while True:
                print("\n=== 메뉴 ===")
                print("1. User Content 데이터셋 생성")
                print("2. Non-Preferred Output 데이터셋 생성")
                print("3. 두 데이터셋 모두 생성")
                print("4. 종료")
                
                choice = input("선택하세요 (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    break
                else:
                    print("잘못된 선택입니다. 다시 선택해주세요.")
        
        if choice == '1':
            input_text = get_input_with_preset(
                "콤마로 구분된 문장들을 입력하세요: ", 
                PRESET_USER_CONTENT_SENTENCES
            )
            dataset_maker.create_user_content_dataset(input_text)
            
        elif choice == '2':
            input_text = get_input_with_preset(
                "콤마로 구분된 문장들을 입력하세요: ", 
                PRESET_NON_PREFERRED_SENTENCES
            )
            dataset_maker.create_non_preferred_output_dataset(input_text)
            
        elif choice == '3':
            input_text1 = get_input_with_preset(
                "User Content용 콤마로 구분된 문장들을 입력하세요: ", 
                PRESET_USER_CONTENT_SENTENCES
            )
            input_text2 = get_input_with_preset(
                "Non-Preferred Output용 콤마로 구분된 문장들을 입력하세요: ", 
                PRESET_NON_PREFERRED_SENTENCES
            )
            
            dataset_maker.create_user_content_dataset(input_text1)
            dataset_maker.create_non_preferred_output_dataset(input_text2)
            
        elif choice == '4':
            print("프로그램을 종료합니다.")
        
        # 사전 설정 모드에서는 자동으로 종료
        if PRESET_MODE is not None:
            print("사전 설정된 작업이 완료되었습니다.")
                
    except Exception as e:
        print(f"오류 발생: {e}")
        print("API 키가 올바른지 확인하고 다시 시도해주세요.")


if __name__ == "__main__":
    main()

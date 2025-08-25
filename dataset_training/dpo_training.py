import os
from openai import OpenAI
from dotenv import load_dotenv
import time

# .env 파일에서 환경 변수 로드
load_dotenv()

def get_openai_api_key():
    """OpenAI API 키를 환경 변수에서 가져오거나 사용자에게 입력을 요청합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")
        api_key = input("OpenAI API 키를 입력하세요: ").strip()
        if not api_key:
            raise ValueError("API 키가 제공되지 않았습니다. 스크립트를 종료합니다.")
    else:
        print(f"OpenAI API 키 로드됨 (끝 4자리): ...{api_key[-4:]}")
    return api_key

def upload_training_file(client: OpenAI, filepath: str) -> str | None:
    """학습 파일을 OpenAI에 업로드하고 파일 ID를 반환합니다."""
    if not os.path.exists(filepath):
        print(f"오류: 학습 파일 '{filepath}'를 찾을 수 없습니다.")
        return None
    
    try:
        print(f"'{filepath}' 파일 업로드 중...")
        with open(filepath, "rb") as f:
            response = client.files.create(
                file=f,
                purpose="fine-tune"
            )
        print(f"파일 업로드 성공. 파일 ID: {response.id}")
        return response.id
    except Exception as e:
        print(f"파일 업로드 중 오류 발생: {e}")
        return None

def create_sft_fine_tuning_job(client: OpenAI, training_file_id: str, model: str = "gpt-4.1-nano-2025-04-14") -> dict | None:
    """Supervised Fine-Tuning (SFT) 작업을 생성하고 작업 정보를 반환합니다."""
    try:
        print(f"SFT 파인튜닝 작업 생성 중 (모델: {model}, 학습 파일 ID: {training_file_id})...")
        job = client.fine_tuning.jobs.create(
            training_file=training_file_id,
            model=model
            # SFT는 기본 방식이므로 method 파라미터 명시적 지정 불필요
        )
        print(f"SFT 파인튜닝 작업 생성 성공. 작업 ID: {job.id}, 상태: {job.status}")
        return job
    except Exception as e:
        print(f"SFT 파인튜닝 작업 생성 중 오류 발생: {e}")
        return None

def monitor_job_status(client: OpenAI, job_id: str):
    """파인튜닝 작업 상태를 주기적으로 확인합니다."""
    print(f"\n작업 ID '{job_id}' 상태 모니터링 시작...")
    try:
        while True:
            job_status = client.fine_tuning.jobs.retrieve(job_id)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 작업 상태: {job_status.status}")
            if job_status.status in ["succeeded", "failed", "cancelled"]:
                print(f"작업이 최종 상태 '{job_status.status}'에 도달했습니다.")
                if job_status.fine_tuned_model:
                    print(f"파인튜닝된 모델 ID: {job_status.fine_tuned_model}")
                if job_status.error:
                    print(f"오류 정보: {job_status.error}")
                break
            time.sleep(60)  # 60초마다 상태 확인
    except Exception as e:
        print(f"작업 상태 모니터링 중 오류 발생: {e}")

if __name__ == "__main__":
    training_data_filepath = os.path.join("dataset_training", "sft_dataset.jsonl") # SFT 데이터 파일 사용
    
    try:
        api_key = get_openai_api_key()
        client = OpenAI(api_key=api_key)
        
        # 1. 학습 파일 업로드
        training_file_id = upload_training_file(client, training_data_filepath)
        
        if training_file_id:
            # 2. SFT 파인튜닝 작업 생성
            # 원하는 모델을 여기서 수정할 수 있습니다.
            sft_job = create_sft_fine_tuning_job(
                client,
                training_file_id,
                model="gpt-4.1-nano-2025-04-14" # SFT 문서 예시 모델
            )
            
            if sft_job:
                # 3. 작업 상태 모니터링 (선택 사항)
                monitor_job_status(client, sft_job.id)
                
    except ValueError as ve:
        print(f"입력 오류: {ve}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

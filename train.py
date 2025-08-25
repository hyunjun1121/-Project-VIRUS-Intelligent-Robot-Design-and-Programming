# train.py
import os
import pickle
import numpy as np
import time
from tqdm import tqdm
from deepface import DeepFace

# 설정
DB_PATH         = "know_face"       # 얼굴 이미지 폴더
EMBEDDINGS_PATH = "embeddings.pkl"  # 저장할 피클 파일
MODEL_NAME      = "VGG-Face"
DETECTOR_BACKEND= "opencv"
ENFORCE_DETECT  = False             # 강제 검출 비활성화

all_embeddings = {}

# 통계 정보 초기화
total_people = 0
total_images = 0
successful_images = 0
skipped_formats = 0
failed_images = 0

print(f"[시작] 얼굴 학습을 시작합니다...")
start_time = time.time()

# 모든 폴더 목록 구하기 (진행 표시용)
person_folders = [p for p in os.listdir(DB_PATH) if os.path.isdir(os.path.join(DB_PATH, p))]
print(f"[정보] {len(person_folders)}명의 폴더를 발견했습니다.")

# 각 사람(폴더)마다
for person_idx, person in enumerate(person_folders):
    person_dir = os.path.join(DB_PATH, person)
    print(f"\n[진행] {person_idx+1}/{len(person_folders)} - '{person}' 처리 중...")
    
    # 해당 인물의 이미지 목록 가져오기
    img_files = [f for f in os.listdir(person_dir) if os.path.isfile(os.path.join(person_dir, f))]
    print(f"   - {len(img_files)}개 이미지 파일 발견")
    total_images += len(img_files)
    total_people += 1

    embeddings = []
    # 폴더 내 모든 이미지 처리
    for img_idx, img_name in enumerate(img_files):
        # Skip unsupported file formats (e.g., .heic)
        if not img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            print(f"   - [{img_idx+1}/{len(img_files)}] 건너뜀: 지원되지 않는 형식: {img_name}")
            skipped_formats += 1
            continue
        img_path = os.path.join(person_dir, img_name)
        
        print(f"   - [{img_idx+1}/{len(img_files)}] 처리 중: {img_name}", end="", flush=True)
        try:
            # 한 장씩 embedding 생성
            rep = DeepFace.represent(
                img_path=img_path,
                model_name=MODEL_NAME,
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=ENFORCE_DETECT
            )
            # DeepFace.represent 은 리스트 형태로 결과 반환
            rep_dict = rep[0]  # 첫 번째 얼굴의 표현
            
            if 'embedding' in rep_dict:
                vector = rep_dict['embedding']
            elif 'representation' in rep_dict:
                vector = rep_dict['representation']
            else:
                print(f" - 실패: 임베딩 벡터를 찾을 수 없음")
                failed_images += 1
                continue
                
            # NumPy 배열로 변환
            vector = np.array(vector)
            embeddings.append(vector)
            successful_images += 1
            print(f" - 성공: {len(vector)} 차원 벡터 추출")
        except Exception as e:
            print(f" - 실패: {str(e)}")
            failed_images += 1

    if embeddings:
        all_embeddings[person] = embeddings
        print(f"   ==> '{person}' 처리 완료: {len(embeddings)}/{len(img_files)} 이미지 성공")
    else:
        print(f"   ==> '{person}' 처리 실패: 유효한 임베딩을 추출할 수 없었습니다")

# 디스크에 저장
print(f"\n[저장] 임베딩을 디스크에 저장합니다...")
with open(EMBEDDINGS_PATH, "wb") as f:
    pickle.dump(all_embeddings, f)

elapsed_time = time.time() - start_time

# 요약 정보 출력
print("\n" + "="*50)
print(f"[완료] 학습 결과 요약:")
print(f"  • 처리 시간: {elapsed_time:.1f}초")
print(f"  • 처리된 폴더: {total_people}명")
print(f"  • 총 이미지 수: {total_images}개")
print(f"  • 성공한 이미지: {successful_images}개")
print(f"  • 건너뛴 형식: {skipped_formats}개")
print(f"  • 실패한 이미지: {failed_images}개")
print(f"  • 저장 위치: {os.path.abspath(EMBEDDINGS_PATH)}")
print("="*50)

"""
데이터 수집 스크립트: 얼굴 이미지 데이터셋 수집
- 웹캠을 통한 실시간 수집
- 기존 이미지 파일에서 얼굴 추출
"""
import os
import cv2
import time
import argparse
import numpy as np
from datetime import datetime
import mediapipe as mp
import shutil
from tqdm import tqdm

def create_directory(directory):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"디렉토리 생성: {directory}")

def collect_face_data(person_name, num_images=300, output_dir="data/raw"):
    """웹캠을 사용하여 얼굴 데이터 수집"""
    # 디렉토리 생성
    person_dir = os.path.join(output_dir, person_name)
    create_directory(person_dir)
    
    # 카메라 설정
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return False
    
    # Face detector 초기화 (MediaPipe 사용)
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils
    face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
    
    count = 0
    print(f"{person_name}의 얼굴 이미지 수집을 시작합니다. 총 {num_images}장을 수집합니다.")
    print("카메라를 보고 다양한 표정과 각도로 얼굴을 움직여주세요.")
    
    # 이미지 수집 시작
    while count < num_images:
        ret, frame = cap.read()
        if not ret:
            print("카메라에서 프레임을 가져올 수 없습니다.")
            break
        
        # 화면 좌우 반전 (거울 효과)
        frame = cv2.flip(frame, 1)
        
        # RGB 변환 (MediaPipe는 RGB 형식 사용)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)
        
        # 얼굴이 감지되면 저장
        if results.detections:
            for detection in results.detections:
                # 얼굴 바운딩 박스 그리기
                mp_drawing.draw_detection(frame, detection)
                
                # 바운딩 박스 좌표 추출
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                
                # 상대 좌표를 절대 좌표로 변환
                xmin = int(bbox.xmin * w)
                ymin = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # 바운딩 박스에 여유 공간 추가
                padding = int(min(width, height) * 0.1)  # 10% 패딩
                xmin = max(0, xmin - padding)
                ymin = max(0, ymin - padding)
                width = min(w - xmin, width + 2 * padding)
                height = min(h - ymin, height + 2 * padding)
                
                # 얼굴 영역 추출
                face_img = frame[ymin:ymin+height, xmin:xmin+width]
                
                if face_img.size > 0:  # 얼굴 영역이 유효한지 확인
                    # 파일 이름 생성 (타임스탬프 추가)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"{person_name}_{timestamp}_{count}.jpg"
                    filepath = os.path.join(person_dir, filename)
                    
                    # 이미지 저장
                    cv2.imwrite(filepath, face_img)
                    count += 1
                    print(f"\r진행 상황: {count}/{num_images} 완료", end="")
            
        # 프레임에 정보 표시
        cv2.putText(frame, f"Captured: {count}/{num_images}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 화면 표시
        cv2.imshow("Face Data Collection", frame)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(0.05)
    
    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n{person_name}의 얼굴 이미지 {count}장이 {person_dir}에 저장되었습니다.")
    return True

def process_existing_images(person_name, input_dir, output_dir="data/raw", min_faces=50):
    """
    기존 이미지 파일에서 얼굴을 감지하고 처리
    
    Args:
        person_name: 인물 이름
        input_dir: 이미지 파일이 있는 디렉토리
        output_dir: 출력 디렉토리
        min_faces: 최소 필요 얼굴 수
    """
    # 디렉토리 생성
    person_dir = os.path.join(output_dir, person_name)
    create_directory(person_dir)
    
    # Face detector 초기화 (MediaPipe 사용)
    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
    
    # 이미지 파일 찾기
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    # 입력 디렉토리가 파일인 경우
    if os.path.isfile(input_dir):
        ext = os.path.splitext(input_dir)[1].lower()
        if ext in image_extensions:
            image_files.append(input_dir)
    else:
        # 디렉토리 내 모든 이미지 파일 찾기
        for root, _, files in os.walk(input_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in image_extensions:
                    image_files.append(os.path.join(root, file))
    
    if not image_files:
        print(f"이미지 파일을 찾을 수 없습니다: {input_dir}")
        return False
    
    print(f"{len(image_files)}개의 이미지 파일을 찾았습니다.")
    print(f"{person_name}의 얼굴 추출을 시작합니다.")
    
    # 얼굴 추출
    count = 0
    for img_path in tqdm(image_files):
        try:
            # 이미지 읽기
            img = cv2.imread(img_path)
            if img is None:
                print(f"이미지를 읽을 수 없습니다: {img_path}")
                continue
            
            # RGB 변환
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 얼굴 감지
            results = face_detection.process(rgb_img)
            
            # 얼굴이 감지되면 저장
            if results.detections:
                for i, detection in enumerate(results.detections):
                    # 바운딩 박스 좌표 추출
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = img.shape
                    
                    # 상대 좌표를 절대 좌표로 변환
                    xmin = int(bbox.xmin * w)
                    ymin = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # 바운딩 박스에 여유 공간 추가
                    padding = int(min(width, height) * 0.2)  # 20% 패딩
                    xmin = max(0, xmin - padding)
                    ymin = max(0, ymin - padding)
                    width = min(w - xmin, width + 2 * padding)
                    height = min(h - ymin, height + 2 * padding)
                    
                    # 얼굴 영역 추출
                    face_img = img[ymin:ymin+height, xmin:xmin+width]
                    
                    if face_img.size > 0:  # 얼굴 영역이 유효한지 확인
                        # 파일 이름 생성
                        base_name = os.path.basename(img_path)
                        filename = f"{person_name}_{base_name.split('.')[0]}_{i}.jpg"
                        filepath = os.path.join(person_dir, filename)
                        
                        # 이미지 저장
                        cv2.imwrite(filepath, face_img)
                        count += 1
            else:
                # 얼굴이 감지되지 않은 경우, 전체 이미지를 저장
                base_name = os.path.basename(img_path)
                filename = f"{person_name}_{base_name}"
                filepath = os.path.join(person_dir, filename)
                
                # 이미지 복사
                shutil.copy(img_path, filepath)
                print(f"얼굴이 감지되지 않았지만 이미지를 복사했습니다: {img_path}")
                
        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {img_path}, {e}")
    
    print(f"\n{person_name}의 얼굴 이미지 {count}개가 {person_dir}에 저장되었습니다.")
    
    # 최소 필요 얼굴 수 체크
    if count < min_faces:
        print(f"경고: 추출된 얼굴 수({count})가 권장 최소 수({min_faces})보다 적습니다.")
        print("얼굴 인식 모델의 성능이 저하될 수 있습니다.")
    
    return count > 0

def import_existing_images(person_name, input_dir, output_dir="data/raw"):
    """
    기존 얼굴 이미지 파일을 데이터셋으로 가져오기
    
    Args:
        person_name: 인물 이름
        input_dir: 이미지 파일이 있는 디렉토리
        output_dir: 출력 디렉토리
    """
    # 디렉토리 생성
    person_dir = os.path.join(output_dir, person_name)
    create_directory(person_dir)
    
    # 이미지 파일 찾기
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp','.JPG','.JPEG','.PNG','.BMP']
    image_files = []
    
    # 입력 디렉토리가 파일인 경우
    if os.path.isfile(input_dir):
        ext = os.path.splitext(input_dir)[1].lower()
        if ext in image_extensions:
            image_files.append(input_dir)
    else:
        # 디렉토리 내 모든 이미지 파일 찾기
        for root, _, files in os.walk(input_dir):
            for file in tqdm(files):
                ext = os.path.splitext(file)[1].lower()
                if ext in image_extensions:
                    image_files.append(os.path.join(root, file))
    
    if not image_files:
        print(f"이미지 파일을 찾을 수 없습니다: {input_dir}")
        return False
    
    print(f"{len(image_files)}개의 이미지 파일을 찾았습니다.")
    print(f"{person_name}의 이미지 가져오기를 시작합니다.")
    
    # 이미지 복사
    count = 0
    for img_path in tqdm(image_files):
        try:
            # 파일 이름 생성
            base_name = os.path.basename(img_path)
            filename = f"{person_name}_{base_name}"
            filepath = os.path.join(person_dir, filename)
            
            # 이미지 복사
            shutil.copy(img_path, filepath)
            count += 1
                
        except Exception as e:
            print(f"이미지 복사 중 오류 발생: {img_path}, {e}")
    
    print(f"\n{person_name}의 이미지 {count}개가 {person_dir}에 저장되었습니다.")
    return count > 0

def main():
    parser = argparse.ArgumentParser(description="얼굴 이미지 데이터 수집 도구")
    parser.add_argument("--name", required=True, help="수집할 사람의 이름")
    parser.add_argument("--mode", choices=["webcam", "process", "import"], default="webcam",
                      help="수집 모드 (webcam: 웹캠 사용, process: 기존 이미지에서 얼굴 추출, import: 기존 얼굴 이미지 가져오기)")
    parser.add_argument("--input", help="이미지 파일 또는 디렉토리 경로 (process 모드나 import 모드에서 사용)")
    parser.add_argument("--count", type=int, default=300, help="웹캠 모드에서 수집할 이미지 수 (기본값: 300)")
    parser.add_argument("--output", default="data/raw", help="출력 디렉토리 (기본값: data/raw)")
    parser.add_argument("--min_faces", type=int, default=50, help="추출할 최소 얼굴 수 (기본값: 50)")
    
    args = parser.parse_args()
    
    # 출력 디렉토리 생성
    create_directory(args.output)
    
    # 모드에 따라 다른 함수 실행
    if args.mode == "webcam":
        # 웹캠을 통한 데이터 수집
        collect_face_data(args.name, args.count, args.output)
    elif args.mode == "process":
        # 기존 이미지에서 얼굴 추출
        if not args.input:
            print("process 모드에서는 --input 인자가 필요합니다.")
            return
        process_existing_images(args.name, args.input, args.output, args.min_faces)
    elif args.mode == "import":
        # 기존 얼굴 이미지 가져오기
        if not args.input:
            print("import 모드에서는 --input 인자가 필요합니다.")
            return
        import_existing_images(args.name, args.input, args.output)

if __name__ == "__main__":
    main()
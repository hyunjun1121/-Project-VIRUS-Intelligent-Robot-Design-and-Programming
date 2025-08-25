import cv2
import numpy as np
import os
import shutil
from deepface import DeepFace
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AllyImagePreprocessor:
    def __init__(self, input_dir='ally_images', output_dir='ally_images_process', 
                 img_size=(224, 224), detector_backend='retinaface'):
        """
        아군 이미지 전처리 시스템 초기화
        
        Parameters:
        - input_dir: 원본 아군 이미지 디렉토리
        - output_dir: 전처리된 이미지 저장 디렉토리
        - img_size: 출력 이미지 크기 (width, height)
        - detector_backend: 얼굴 탐지 백엔드
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.img_size = img_size
        self.detector_backend = detector_backend
        self.stats = {
            'total_images': 0,
            'processed_images': 0,
            'failed_images': 0,
            'no_face_images': 0,
            'multiple_faces_images': 0
        }
        
        # 출력 디렉토리 생성
        if os.path.exists(self.output_dir):
            logger.warning(f"{self.output_dir} 디렉토리가 이미 존재합니다. 기존 파일을 덮어쓸 수 있습니다.")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def preprocess_face(self, face_img, img_size):
        """
        얼굴 이미지에 전처리를 적용합니다.
        
        Parameters:
        - face_img: 얼굴 이미지 (BGR 형식)
        - img_size: 목표 크기 (width, height)
        
        Returns:
        - processed_img: 전처리된 이미지
        """
        # 크기 조정
        face_img = cv2.resize(face_img, img_size)
        
        # 히스토그램 평활화 (밝기 정규화)
        # 컬러 이미지의 경우 CLAHE를 YUV 색 공간의 Y 채널에 적용
        yuv = cv2.cvtColor(face_img, cv2.COLOR_BGR2YUV)
        
        # CLAHE 객체 생성
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Y 채널에 히스토그램 평활화 적용
        yuv[:,:,0] = clahe.apply(yuv[:,:,0])
        
        # BGR 색 공간으로 변환
        face_img = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        
        return face_img
    
    def process_single_image(self, img_path, output_path):
        """
        단일 이미지를 처리합니다.
        
        Parameters:
        - img_path: 입력 이미지 경로
        - output_path: 출력 이미지 경로
        
        Returns:
        - success: 처리 성공 여부
        - message: 처리 결과 메시지
        """
        try:
            # 얼굴 추출
            faces = DeepFace.extract_faces(
                img_path=img_path,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=True  # 얼굴 정렬 활성화
            )
            
            if len(faces) == 0:
                self.stats['no_face_images'] += 1
                return False, "얼굴을 찾을 수 없음"
            
            if len(faces) > 1:
                self.stats['multiple_faces_images'] += 1
                # 가장 큰 얼굴 선택
                largest_face = max(faces, key=lambda x: x['area']['w'] * x['area']['h'])
                face_img = (largest_face['face'] * 255).astype(np.uint8)
            else:
                face_img = (faces[0]['face'] * 255).astype(np.uint8)
            
            # BGR로 변환 (DeepFace는 RGB로 반환)
            face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
            
            # 전처리 적용
            processed_img = self.preprocess_face(face_img, self.img_size)
            
            # 이미지 저장
            cv2.imwrite(output_path, processed_img)
            
            self.stats['processed_images'] += 1
            return True, "성공"
            
        except Exception as e:
            self.stats['failed_images'] += 1
            return False, f"오류: {str(e)}"
    
    def process_ally_directory(self, ally_name, ally_path, max_workers=4):
        """
        특정 아군의 모든 이미지를 처리합니다.
        
        Parameters:
        - ally_name: 아군 이름
        - ally_path: 아군 이미지 디렉토리 경로
        - max_workers: 병렬 처리 워커 수
        """
        # 출력 디렉토리 생성
        ally_output_dir = os.path.join(self.output_dir, ally_name)
        os.makedirs(ally_output_dir, exist_ok=True)
        
        # 이미지 파일 목록 가져오기
        image_files = [f for f in os.listdir(ally_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        if not image_files:
            logger.warning(f"{ally_name}: 이미지 파일이 없습니다.")
            return
        
        logger.info(f"{ally_name}: {len(image_files)}개 이미지 처리 시작")
        
        # 처리 결과 저장
        results = []
        
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for img_file in image_files:
                img_path = os.path.join(ally_path, img_file)
                output_filename = f"{os.path.splitext(img_file)[0]}_processed.jpg"
                output_path = os.path.join(ally_output_dir, output_filename)
                
                future = executor.submit(self.process_single_image, img_path, output_path)
                futures[future] = (img_file, img_path, output_path)
                self.stats['total_images'] += 1
                if self.stats['total_images'] ==50:
                    break
            
            # 결과 수집
            for future in tqdm(as_completed(futures), total=len(futures), desc=ally_name):
                img_file, img_path, output_path = futures[future]
                success, message = future.result()
                
                results.append({
                    'file': img_file,
                    'input_path': img_path,
                    'output_path': output_path,
                    'success': success,
                    'message': message
                })
        
        # 처리 결과 저장
        result_file = os.path.join(ally_output_dir, 'processing_results.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 성공률 계산
        success_count = sum(1 for r in results if r['success'])
        success_rate = (success_count / len(results)) * 100 if results else 0
        
        logger.info(f"{ally_name}: 처리 완료 - 성공률: {success_rate:.1f}% ({success_count}/{len(results)})")
    
    def process_all_allies(self, max_workers=4):
        """
        모든 아군의 이미지를 처리합니다.
        
        Parameters:
        - max_workers: 병렬 처리 워커 수
        """
        if not os.path.exists(self.input_dir):
            logger.error(f"입력 디렉토리가 존재하지 않습니다: {self.input_dir}")
            return
        
        # 아군 디렉토리 목록 가져오기
        ally_dirs = [d for d in os.listdir(self.input_dir) 
                    if os.path.isdir(os.path.join(self.input_dir, d))]
        
        if not ally_dirs:
            logger.error("아군 디렉토리를 찾을 수 없습니다.")
            return
        
        logger.info(f"총 {len(ally_dirs)}명의 아군 이미지 처리를 시작합니다.")
        
        # 각 아군별로 처리
        for i, ally_name in enumerate(ally_dirs, 1):
            ally_path = os.path.join(self.input_dir, ally_name)
            logger.info(f"\n[{i}/{len(ally_dirs)}] {ally_name} 처리 중...")
            self.process_ally_directory(ally_name, ally_path, max_workers)
        
        # 전체 통계 출력
        self.print_statistics()
        
        # 전체 통계 저장
        stats_file = os.path.join(self.output_dir, 'overall_statistics.json')
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def print_statistics(self):
        """처리 통계를 출력합니다."""
        logger.info("\n" + "="*50)
        logger.info("전체 처리 통계")
        logger.info("="*50)
        logger.info(f"총 이미지 수: {self.stats['total_images']}")
        logger.info(f"처리 성공: {self.stats['processed_images']}")
        logger.info(f"처리 실패: {self.stats['failed_images']}")
        logger.info(f"얼굴 없음: {self.stats['no_face_images']}")
        logger.info(f"다중 얼굴: {self.stats['multiple_faces_images']}")
        
        if self.stats['total_images'] > 0:
            success_rate = (self.stats['processed_images'] / self.stats['total_images']) * 100
            logger.info(f"전체 성공률: {success_rate:.1f}%")
    
    def validate_preprocessing(self, sample_size=5):
        """
        전처리 결과를 검증하고 샘플을 시각화합니다.
        
        Parameters:
        - sample_size: 각 아군별 샘플 크기
        """
        import matplotlib.pyplot as plt
        import random
        
        if not os.path.exists(self.output_dir):
            logger.error("전처리된 이미지 디렉토리가 없습니다.")
            return
        
        ally_dirs = [d for d in os.listdir(self.output_dir) 
                    if os.path.isdir(os.path.join(self.output_dir, d))]
        
        fig, axes = plt.subplots(len(ally_dirs), sample_size, figsize=(15, 3*len(ally_dirs)))
        if len(ally_dirs) == 1:
            axes = axes.reshape(1, -1)
        
        for i, ally_name in enumerate(ally_dirs):
            ally_path = os.path.join(self.output_dir, ally_name)
            images = [f for f in os.listdir(ally_path) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            # 랜덤 샘플 선택
            sample_images = random.sample(images, min(sample_size, len(images)))
            
            for j, img_file in enumerate(sample_images):
                img_path = os.path.join(ally_path, img_file)
                img = cv2.imread(img_path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                axes[i, j].imshow(img_rgb)
                axes[i, j].axis('off')
                if j == 0:
                    axes[i, j].set_title(f"{ally_name}", fontsize=12, loc='left')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'preprocessing_samples.png'), dpi=150)
        plt.show()


# 사용 예제
if __name__ == "__main__":
    # 전처리 시스템 초기화
    preprocessor = AllyImagePreprocessor(
        input_dir='ally_images',
        output_dir='ally_images_process',
        img_size=(360, 360),  # 원하는 크기로 조정
        detector_backend='retinaface'  # 높은 정확도
    )
    
    # 모든 아군 이미지 처리
    preprocessor.process_all_allies(max_workers=4)  # CPU 코어 수에 맞게 조정
    
    # 처리 결과 검증 및 시각화
    # preprocessor.validate_preprocessing(sample_size=5)
    
    # 특정 아군만 처리하고 싶은 경우
    # preprocessor.process_ally_directory('ally1', 'ally_images/ally1')
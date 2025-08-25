import cv2
import numpy as np
import os
import pickle
from deepface import DeepFace
import json
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

class AllyEnemyDetector:
    def __init__(self, ally_image_dir, model_name='Facenet512', detector_backend='retinaface'):
        """
        아군/적군 식별 시스템 초기화
        
        Parameters:
        - ally_image_dir: 아군 이미지가 저장된 디렉토리 경로
        - model_name: 사용할 얼굴 인식 모델 ('VGG-Face', 'Facenet512', 'ArcFace' 등)
        - detector_backend: 얼굴 탐지 백엔드
        """
        self.ally_image_dir = ally_image_dir
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.ally_embeddings = {}
        self.ally_names = []
        self.embeddings_cache_path = 'ally_embeddings.pkl'
        
        # 아군 임베딩 생성 또는 로드
        self._prepare_ally_embeddings()
    
    def _prepare_ally_embeddings(self):
        """아군 얼굴 임베딩을 준비합니다."""
        
        # 캐시된 임베딩이 있는지 확인
        if os.path.exists(self.embeddings_cache_path):
            print("저장된 임베딩을 로드합니다...")
            with open(self.embeddings_cache_path, 'rb') as f:
                self.ally_embeddings = pickle.load(f)
                self.ally_names = list(self.ally_embeddings.keys())
            print(f"{len(self.ally_names)}명의 아군 임베딩을 로드했습니다.")
            return
        
        print("아군 이미지에서 임베딩을 생성합니다...")
        
        # 아군별 디렉토리 탐색
        for person_name in os.listdir(self.ally_image_dir):
            person_path = os.path.join(self.ally_image_dir, person_name)
            if not os.path.isdir(person_path):
                continue
            
            print(f"{person_name}의 임베딩 생성 중...")
            embeddings = []
            
            # 병렬 처리로 속도 향상
            image_paths = []
            for img_name in os.listdir(person_path):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_paths.append(os.path.join(person_path, img_name))
            
            # 샘플링 (200장 중 50장만 사용하여 속도 향상)
            if len(image_paths) > 50:
                import random
                image_paths = random.sample(image_paths, 50)
            
            # 각 이미지에서 임베딩 추출
            for img_path in image_paths:
                try:
                    # 얼굴 임베딩 추출
                    embedding = DeepFace.represent(
                        img_path=img_path,
                        model_name=self.model_name,
                        detector_backend=self.detector_backend,
                        align=True,
                        enforce_detection=False
                    )
                    
                    if embedding and len(embedding) > 0:
                        embeddings.append(embedding[0]['embedding'])
                
                except Exception as e:
                    print(f"  - {img_path} 처리 중 오류: {str(e)}")
                    continue
            
            if embeddings:
                # 평균 임베딩 계산 (더 강건한 표현)
                self.ally_embeddings[person_name] = {
                    'embeddings': embeddings,
                    'mean_embedding': np.mean(embeddings, axis=0),
                    'count': len(embeddings)
                }
                self.ally_names.append(person_name)
                print(f"  - {person_name}: {len(embeddings)}개 임베딩 생성 완료")
        
        # 임베딩 캐시 저장
        with open(self.embeddings_cache_path, 'wb') as f:
            pickle.dump(self.ally_embeddings, f)
        print(f"총 {len(self.ally_names)}명의 아군 임베딩 생성 완료")
    
    def identify_faces(self, image_path, threshold=0.6, use_multi_match=True):
        """
        이미지에서 얼굴을 찾고 아군/적군을 식별합니다.
        
        Parameters:
        - image_path: 분석할 이미지 경로
        - threshold: 아군 판별 임계값 (낮을수록 엄격)
        - use_multi_match: 여러 임베딩과 비교하여 정확도 향상
        
        Returns:
        - results: 식별 결과 리스트
        """
        
        # 이미지 읽기
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 얼굴 탐지
        try:
            faces = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=True  # 얼굴 정렬로 정확도 향상
            )
        except Exception as e:
            print(f"얼굴 탐지 실패: {str(e)}")
            return []
        
        results = []
        
        for i, face_data in enumerate(faces):
            facial_area = face_data['facial_area']
            x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
            
            # 중심 좌표 계산
            center_x = x + w // 2
            center_y = y + h // 2
            
            # 얼굴 이미지 추출
            face_img = face_data['face']
            
            # 얼굴 임베딩 생성
            try:
                # 임시 파일로 저장 (DeepFace 요구사항)
                temp_path = f'temp_face_{i}.jpg'
                cv2.imwrite(temp_path, cv2.cvtColor((face_img * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
                
                target_embedding = DeepFace.represent(
                    img_path=temp_path,
                    model_name=self.model_name,
                    detector_backend='skip',  # 이미 추출된 얼굴 사용
                    enforce_detection=False
                )[0]['embedding']
                
                os.remove(temp_path)  # 임시 파일 삭제
                
            except Exception as e:
                print(f"얼굴 {i+1} 임베딩 생성 실패: {str(e)}")
                results.append({
                    'bbox': (x, y, w, h),
                    'center': (center_x, center_y),
                    'label': 'unknown',
                    'confidence': 0.0
                })
                continue
            
            # 아군과 비교
            best_match = None
            best_distance = float('inf')
            
            for ally_name, ally_data in self.ally_embeddings.items():
                if use_multi_match:
                    # 여러 임베딩과 비교하여 최소 거리 찾기
                    distances = []
                    for ally_emb in ally_data['embeddings']:
                        distance = self._cosine_distance(target_embedding, ally_emb)
                        distances.append(distance)
                    
                    # 상위 k개의 최소 거리 평균 사용
                    k = min(5, len(distances))
                    top_k_distances = sorted(distances)[:k]
                    avg_distance = np.mean(top_k_distances)
                else:
                    # 평균 임베딩과만 비교
                    avg_distance = self._cosine_distance(target_embedding, ally_data['mean_embedding'])
                
                if avg_distance < best_distance:
                    best_distance = avg_distance
                    best_match = ally_name
            
            # 아군/적군 판별
            if best_distance < threshold:
                label = best_match
                confidence = 1 - best_distance
            else:
                label = 'enemy'
                confidence = best_distance
            
            results.append({
                'bbox': (x, y, w, h),
                'center': (center_x, center_y),
                'label': label,
                'confidence': confidence,
                'distance': best_distance
            })
        
        return results
    
    def _cosine_distance(self, emb1, emb2):
        """코사인 거리 계산"""
        return 1 - np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def visualize_results(self, image_path, results, save_path='result.jpg'):
        """결과를 시각화합니다."""
        
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        for result in results:
            x, y, w, h = result['bbox']
            center_x, center_y = result['center']
            label = result['label']
            confidence = result['confidence']
            
            # 색상 설정 (아군: 초록색, 적군: 빨간색)
            if label == 'enemy':
                color = (255, 0, 0)  # 빨간색
            else:
                color = (0, 255, 0)  # 초록색
            
            # 박스 그리기
            cv2.rectangle(img_rgb, (x, y), (x+w, y+h), color, 2)
            
            # 중심점 표시
            cv2.circle(img_rgb, (center_x, center_y), 3, (0, 0, 255), -1)
            
            # 라벨과 신뢰도 표시
            label_text = f"{label} ({confidence:.2f})"
            cv2.putText(img_rgb, label_text, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 중심 좌표 표시
            coord_text = f"({center_x}, {center_y})"
            cv2.putText(img_rgb, coord_text, (x, y+h+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # 결과 저장 및 표시
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 8))
        plt.imshow(img_rgb)
        plt.axis('off')
        plt.title(f'Ally/Enemy Detection - {len(results)} faces detected')
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.show()
        
        return img_rgb

# 사용 예제
if __name__ == "__main__":
    # 아군 이미지 디렉토리 구조:
    # ally_images/
    #   ├── person1/
    #   │   ├── img1.jpg
    #   │   ├── img2.jpg
    #   │   └── ...
    #   ├── person2/
    #   │   └── ...
    #   └── ...
    
    # 시스템 초기화
    detector = AllyEnemyDetector(
        ally_image_dir='ally_processing/ally_images_process',
        model_name='Facenet512',  # 높은 정확도
        detector_backend='retinaface'  # 높은 탐지율
    )
    
    # 테스트 이미지 분석
    test_image = 'target2.jpg'
    results = detector.identify_faces(
        test_image, 
        threshold=0.4,  # 임계값 조정으로 민감도 변경
        use_multi_match=True  # 더 정확한 매칭
    )
    
    # 결과 출력
    print("\n=== 식별 결과 ===")
    for i, result in enumerate(results):
        print(f"\n얼굴 {i+1}:")
        print(f"  - 라벨: {result['label']}")
        print(f"  - 중심 좌표: {result['center']}")
        print(f"  - 바운딩 박스: {result['bbox']}")
        print(f"  - 신뢰도: {result['confidence']:.3f}")
        print(f"  - 거리: {result['distance']:.3f}")
    
    # 결과 시각화
    detector.visualize_results(test_image, results, 'detection_result.jpg')
    
    # JSON으로 결과 저장
    with open('detection_results.json', 'w') as f:
        json.dump(results, f, indent=2)
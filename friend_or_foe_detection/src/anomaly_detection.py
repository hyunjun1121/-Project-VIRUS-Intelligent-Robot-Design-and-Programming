"""
이상 탐지(적군 식별) 모듈
"""
import os
import numpy as np
import tensorflow as tf
import cv2
import pickle

class AnomalyDetector:
    """이상 탐지 모델 (아군/적군 구분)"""
    
    def __init__(self, model_path=None, feature_extractor_path=None, threshold=0.8):
        """
        이상 탐지 모델 초기화
        
        Args:
            model_path: 모델 파일 경로
            feature_extractor_path: 특징 추출기 모델 경로
            threshold: 정상/이상 판단 임계값
        """
        self.feature_extractor = None
        self.threshold = threshold
        self.embeddings = []
        self.class_names = []
        
        # 모델 로드
        if model_path and os.path.exists(model_path):
            self.load_model(model_path, feature_extractor_path)
    
    def load_model(self, model_path, feature_extractor_path=None):
        """
        모델 로드
        
        Args:
            model_path: 모델 파일 경로
            feature_extractor_path: 특징 추출기 모델 경로
        """
        # 특징 추출기 경로가 지정되지 않은 경우, 기본 경로 사용
        if feature_extractor_path is None:
            feature_extractor_path = os.path.join(
                os.path.dirname(model_path),
                'feature_extractor.h5'
            )
        
        # 모델 데이터 로드
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.embeddings = model_data['embeddings']
            self.class_names = model_data['class_names']
            self.threshold = model_data.get('threshold', self.threshold)
            
            # 특징 추출기 로드
            if os.path.exists(feature_extractor_path):
                self.feature_extractor = tf.keras.models.load_model(feature_extractor_path)
                print(f"특징 추출기가 {feature_extractor_path}에서 로드되었습니다.")
            else:
                print(f"특징 추출기 파일이 존재하지 않습니다: {feature_extractor_path}")
                return False
            
            print(f"이상 탐지 모델이 {model_path}에서 로드되었습니다.")
            print(f"임베딩 수: {len(self.embeddings)}, 임계값: {self.threshold}")
            return True
            
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            return False
    
    def detect(self, img, img_size=(224, 224)):
        """
        이미지가 아군인지 적군인지 판별
        
        Args:
            img: 입력 이미지
            img_size: 이미지 크기
            
        Returns:
            is_friend: 아군 여부
            confidence: 신뢰도
            class_name: 아군일 경우 클래스 이름
        """
        if self.feature_extractor is None:
            print("특징 추출기가 로드되지 않았습니다.")
            return False, 0, None
        
        if len(self.embeddings) == 0:
            print("참조 임베딩이 없습니다.")
            return False, 0, None
        
        # 이미지 전처리
        if img.shape[:2] != img_size:
            img = cv2.resize(img, img_size)
        
        # 배치 차원 추가 및 정규화
        img_array = np.expand_dims(img, axis=0) / 255.0
        
        # 임베딩 계산
        embedding = self.feature_extractor.predict(img_array, verbose=0)[0]
        
        # 모든 참조 임베딩과의 코사인 유사도 계산
        similarities = []
        for ref_embedding in self.embeddings:
            similarity = np.dot(embedding, ref_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(ref_embedding)
            )
            similarities.append(similarity)
        
        # 최대 유사도 및 해당 클래스
        max_similarity = max(similarities)
        max_index = np.argmax(similarities)
        class_name = self.class_names[max_index]
        
        # 아군 여부 판별
        is_friend = max_similarity >= self.threshold
        
        if is_friend:
            confidence = max_similarity
        else:
            # 적군일 경우, 1 - 최대 유사도를 신뢰도로 사용
            confidence = 1 - max_similarity
        
        return is_friend, confidence, class_name if is_friend else None
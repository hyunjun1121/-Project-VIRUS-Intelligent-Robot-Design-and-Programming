"""
모델 학습 스크립트: CNN 기반 얼굴 인식 모델과 이상 탐지 모델 학습
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, applications
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import cv2
from sklearn.metrics import classification_report, confusion_matrix
import argparse
import pickle
from face_detection import FaceDetector
import shutil
from tqdm import tqdm

def create_directory(directory):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"디렉토리 생성: {directory}")

class FaceRecognitionModel:
    """CNN 기반 얼굴 인식 모델"""
    
    def __init__(self, input_shape=(224, 224, 3), num_classes=None):
        """
        얼굴 인식 모델 초기화
        
        Args:
            input_shape: 입력 이미지 크기
            num_classes: 클래스 수 (사람 수)
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None
        self.history = None
        self.class_names = None
        
    def build_model(self):
        """모델 구축"""
        # 사전 훈련된 모델 사용 (MobileNetV2)
        base_model = applications.MobileNetV2(
            input_shape=self.input_shape,
            include_top=False,
            weights='imagenet'
        )
        
        # 특정 레이어까지 학습 가능하게 설정
        for layer in base_model.layers[:-30]:
            layer.trainable = False
        
        # 모델 구축
        model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.BatchNormalization(),
            layers.Dense(512, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        # 모델 컴파일
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def load_data(self, data_dir, img_size=(224, 224), validation_split=0.2):
        """
        데이터셋 로드 및 전처리
        
        Args:
            data_dir: 데이터 디렉토리
            img_size: 이미지 크기
            validation_split: 검증 데이터 비율
            
        Returns:
            훈련 및 검증 데이터 제너레이터
        """
        # 클래스 이름 가져오기 (디렉토리 이름)
        self.class_names = sorted([d for d in os.listdir(data_dir) 
                                  if os.path.isdir(os.path.join(data_dir, d))])
        
        # 클래스 수 설정
        self.num_classes = len(self.class_names)
        print(f"총 {self.num_classes}명의 사람을 인식하도록 학습합니다. 클래스: {self.class_names}")
        
        # 데이터 증강 설정 (훈련용)
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest',
            validation_split=validation_split
        )
        
        # 데이터 증강 설정 (검증용)
        val_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=validation_split
        )
        
        # 훈련 데이터 로드
        train_generator = train_datagen.flow_from_directory(
            data_dir,
            target_size=img_size,
            batch_size=32,
            class_mode='categorical',
            subset='training',
            shuffle=True
        )
        
        # 검증 데이터 로드
        validation_generator = val_datagen.flow_from_directory(
            data_dir,
            target_size=img_size,
            batch_size=32,
            class_mode='categorical',
            subset='validation',
            shuffle=False
        )
        
        return train_generator, validation_generator
    
    def train(self, train_generator, validation_generator, epochs=50, 
              model_save_path='data/models/face_recognition_model.h5'):
        """
        모델 학습
        
        Args:
            train_generator: 훈련 데이터 제너레이터
            validation_generator: 검증 데이터 제너레이터
            epochs: 학습 에포크 수
            model_save_path: 모델 저장 경로
            
        Returns:
            학습 이력
        """
        # 모델 없으면 구축
        if self.model is None:
            self.build_model()
        
        # 모델 저장 디렉토리 생성
        create_directory(os.path.dirname(model_save_path))
        
        # 콜백 설정
        callbacks = [
            # 가장 좋은 모델 저장
            ModelCheckpoint(
                model_save_path,
                monitor='val_accuracy',
                save_best_only=True,
                mode='max',
                verbose=1
            ),
            # 조기 종료
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            )
        ]
        
        # 모델 학습
        history = self.model.fit(
            train_generator,
            validation_data=validation_generator,
            epochs=epochs,
            callbacks=callbacks,
            verbose=1
        )
        
        self.history = history
        
        # 클래스 이름 저장
        class_names_path = os.path.join(os.path.dirname(model_save_path), 'class_names.pkl')
        with open(class_names_path, 'wb') as f:
            pickle.dump(self.class_names, f)
        
        print(f"모델이 {model_save_path}에 저장되었습니다.")
        print(f"클래스 이름이 {class_names_path}에 저장되었습니다.")
        
        return history
    
    def load_model(self, model_path, class_names_path=None):
        """
        저장된 모델 로드
        
        Args:
            model_path: 모델 파일 경로
            class_names_path: 클래스 이름 파일 경로
        """
        self.model = tf.keras.models.load_model(model_path)
        
        # 클래스 이름 로드
        if class_names_path:
            with open(class_names_path, 'rb') as f:
                self.class_names = pickle.load(f)
            self.num_classes = len(self.class_names)
        
        print(f"모델이 {model_path}에서 로드되었습니다.")
        if class_names_path:
            print(f"클래스 이름이 {class_names_path}에서 로드되었습니다. 클래스: {self.class_names}")
    
    def predict(self, img):
        """
        이미지에서 인물 식별
        
        Args:
            img: 입력 이미지
            
        Returns:
            예측 클래스, 신뢰도
        """
        if self.model is None:
            print("모델이 로드되지 않았습니다.")
            return None, 0
        
        # 이미지 전처리
        if img.shape[:2] != self.input_shape[:2]:
            img = cv2.resize(img, self.input_shape[:2])
        
        # 배치 차원 추가 및 정규화
        img_array = np.expand_dims(img, axis=0) / 255.0
        
        # 예측
        predictions = self.model.predict(img_array)
        
        # 최대 신뢰도 및 클래스 인덱스
        class_idx = np.argmax(predictions[0])
        confidence = predictions[0][class_idx]
        
        # 클래스 이름
        if self.class_names:
            class_name = self.class_names[class_idx]
        else:
            class_name = str(class_idx)
        
        return class_name, confidence
    
    def evaluate(self, test_generator):
        """
        모델 평가
        
        Args:
            test_generator: 테스트 데이터 제너레이터
            
        Returns:
            평가 결과
        """
        if self.model is None:
            print("모델이 로드되지 않았습니다.")
            return None
        
        # 모델 평가
        results = self.model.evaluate(test_generator)
        print(f"테스트 손실: {results[0]:.4f}")
        print(f"테스트 정확도: {results[1]:.4f}")
        
        # 예측
        y_pred = []
        y_true = []
        
        test_generator.reset()
        for i in range(len(test_generator)):
            x, y = test_generator[i]
            predictions = self.model.predict(x)
            y_pred.extend(np.argmax(predictions, axis=1))
            y_true.extend(np.argmax(y, axis=1))
        
        # 분류 보고서
        if self.class_names:
            report = classification_report(y_true, y_pred, target_names=self.class_names)
        else:
            report = classification_report(y_true, y_pred)
        
        print("분류 보고서:")
        print(report)
        
        return results
    
    def plot_history(self, save_path=None):
        """
        학습 이력 시각화
        
        Args:
            save_path: 그래프 저장 경로
        """
        if self.history is None:
            print("학습 이력이 없습니다.")
            return
        
        # 정확도 그래프
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 2, 1)
        plt.plot(self.history.history['accuracy'], label='Train')
        plt.plot(self.history.history['val_accuracy'], label='Validation')
        plt.title('Model Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        
        # 손실 그래프
        plt.subplot(1, 2, 2)
        plt.plot(self.history.history['loss'], label='Train')
        plt.plot(self.history.history['val_loss'], label='Validation')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            print(f"학습 이력 그래프가 {save_path}에 저장되었습니다.")
        
        plt.show()

class AnomalyDetector:
    """이상 탐지 모델 (아군/적군 구분)"""
    
    def __init__(self, feature_extractor=None, threshold=0.8):
        """
        이상 탐지 모델 초기화
        
        Args:
            feature_extractor: 특징 추출기 (CNN 모델)
            threshold: 정상/이상 판단 임계값
        """
        self.feature_extractor = feature_extractor
        self.threshold = threshold
        self.embeddings = []
        self.class_names = []
    
    def create_feature_extractor(self, input_shape=(224, 224, 3)):
        """
        특징 추출기 생성
        
        Args:
            input_shape: 입력 이미지 크기
            
        Returns:
            특징 추출 모델
        """
        # MobileNetV2 모델 로드
        base_model = applications.MobileNetV2(
            input_shape=input_shape,
            include_top=False,
            weights='imagenet'
        )
        
        # 특징 추출 모델 구축
        model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D()
        ])
        
        self.feature_extractor = model
        return model
    
    def compute_embeddings(self, data_dir, img_size=(224, 224)):
        """
        데이터셋에서 임베딩 계산
        
        Args:
            data_dir: 데이터 디렉토리 (아군 얼굴 이미지 포함)
            img_size: 이미지 크기
            
        Returns:
            임베딩 배열, 클래스 이름 목록
        """
        if self.feature_extractor is None:
            self.create_feature_extractor(input_shape=(*img_size, 3))
        
        all_embeddings = []
        all_class_names = []
        
        # 클래스 이름 가져오기 (디렉토리 이름)
        class_names = sorted([d for d in os.listdir(data_dir) 
                            if os.path.isdir(os.path.join(data_dir, d))])
        
        print(f"총 {len(class_names)}명의 아군 데이터를 처리 중입니다.")
        
        # 각 클래스(사람)별로 임베딩 계산
        for class_name in class_names:
            class_dir = os.path.join(data_dir, class_name)
            
            # 이미지 파일 목록
            image_files = [f for f in os.listdir(class_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            print(f"{class_name}의 이미지 {len(image_files)}개 처리 중...")
            
            for img_file in tqdm(image_files):
                img_path = os.path.join(class_dir, img_file)
                
                # 이미지 로드 및 전처리
                img = cv2.imread(img_path)
                if img is None:
                    continue
                
                img = cv2.resize(img, img_size)
                img = img / 255.0  # 정규화
                img = np.expand_dims(img, axis=0)  # 배치 차원 추가
                
                # 임베딩 계산
                embedding = self.feature_extractor.predict(img, verbose=0)[0]
                
                all_embeddings.append(embedding)
                all_class_names.append(class_name)
        
        self.embeddings = np.array(all_embeddings)
        self.class_names = all_class_names
        
        print(f"총 {len(all_embeddings)}개의 임베딩이 계산되었습니다.")
        
        return all_embeddings, all_class_names
    
    def save_model(self, model_path='data/models/anomaly_detector.pkl'):
        """
        모델 저장
        
        Args:
            model_path: 모델 저장 경로
        """
        # 저장할 데이터
        model_data = {
            'embeddings': self.embeddings,
            'class_names': self.class_names,
            'threshold': self.threshold
        }
        
        # 디렉토리 생성
        create_directory(os.path.dirname(model_path))
        
        # 모델 저장
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # 특징 추출기 저장
        if self.feature_extractor:
            feature_extractor_path = os.path.join(
                os.path.dirname(model_path),
                'feature_extractor.h5'
            )
            self.feature_extractor.save(feature_extractor_path)
            print(f"특징 추출기가 {feature_extractor_path}에 저장되었습니다.")
        
        print(f"이상 탐지 모델이 {model_path}에 저장되었습니다.")
    
    def load_model(self, model_path, feature_extractor_path=None):
        """
        모델 로드
        
        Args:
            model_path: 모델 파일 경로
            feature_extractor_path: 특징 추출기 모델 경로
        """
        # 모델 데이터 로드
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.embeddings = model_data['embeddings']
        self.class_names = model_data['class_names']
        self.threshold = model_data['threshold']
        
        # 특징 추출기 로드
        if feature_extractor_path:
            self.feature_extractor = tf.keras.models.load_model(feature_extractor_path)
            print(f"특징 추출기가 {feature_extractor_path}에서 로드되었습니다.")
        
        print(f"이상 탐지 모델이 {model_path}에서 로드되었습니다.")
        print(f"임베딩 수: {len(self.embeddings)}, 임계값: {self.threshold}")
    
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

def prepare_dataset(input_dir, output_dir, img_size=(224, 224)):
    """
    학습을 위한 데이터셋 준비 (얼굴 감지 및 전처리)
    
    Args:
        input_dir: 입력 디렉토리 (원본 이미지)
        output_dir: 출력 디렉토리 (전처리된 얼굴 이미지)
        img_size: 출력 이미지 크기
    """
    # 디렉토리 생성
    create_directory(output_dir)
    
    # 얼굴 감지기 초기화
    face_detector = FaceDetector(use_mediapipe=True, use_yolo=False)
    
    # 각 사람별 디렉토리 처리
    person_dirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    
    for person in person_dirs:
        person_input_dir = os.path.join(input_dir, person)
        person_output_dir = os.path.join(output_dir, person)
        create_directory(person_output_dir)
        
        # 이미지 파일 목록
        image_files = [f for f in os.listdir(person_input_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        print(f"{person}의 이미지 {len(image_files)}개 처리 중...")
        
        for img_file in tqdm(image_files):
            input_path = os.path.join(person_input_dir, img_file)
            output_path = os.path.join(person_output_dir, img_file)
            
            # 이미지 읽기
            img = cv2.imread(input_path)
            if img is None:
                print(f"이미지를 읽을 수 없습니다: {input_path}")
                continue
            
            # 얼굴 감지
            faces = face_detector.detect_faces(img)
            
            if faces:
                # 첫 번째 감지된 얼굴 사용
                face = faces[0]
                
                # 얼굴 영역 추출
                face_img = face_detector.extract_face(img, face, target_size=img_size)
                
                if face_img is not None:
                    # 이미지 저장
                    cv2.imwrite(output_path, face_img)
                else:
                    print(f"얼굴 영역을 추출할 수 없습니다: {input_path}")
            else:
                print(f"얼굴이 감지되지 않았습니다: {input_path}")
                # 원본 이미지를 크기 조정하여 저장
                resized_img = cv2.resize(img, img_size)
                cv2.imwrite(output_path, resized_img)
    
    print("모든 이미지 전처리가 완료되었습니다.")

def train_face_recognition_model(data_dir, output_model_path, epochs=50):
    """
    얼굴 인식 모델 학습
    
    Args:
        data_dir: 훈련 데이터 디렉토리
        output_model_path: 출력 모델 경로
        epochs: 학습 에포크 수
    """
    # 모델 초기화
    model = FaceRecognitionModel(input_shape=(224, 224, 3))
    
    # 데이터 로드
    train_generator, validation_generator = model.load_data(data_dir)
    
    # 모델 빌드
    model.build_model()
    
    # 모델 요약
    model.model.summary()
    
    # 모델 학습
    history = model.train(train_generator, validation_generator, epochs=epochs, 
                         model_save_path=output_model_path)
    
    # 학습 이력 시각화
    plot_path = os.path.join(os.path.dirname(output_model_path), 'training_history.png')
    model.plot_history(save_path=plot_path)
    
    return model

def train_anomaly_detector(data_dir, output_model_path, threshold=0.8):
    """
    이상 탐지 모델 학습
    
    Args:
        data_dir: 훈련 데이터 디렉토리 (아군 얼굴 이미지)
        output_model_path: 출력 모델 경로
        threshold: 정상/이상 판단 임계값
    """
    # 이상 탐지 모델 초기화
    detector = AnomalyDetector(threshold=threshold)
    
    # 특징 추출기 생성
    detector.create_feature_extractor()
    
    # 임베딩 계산
    detector.compute_embeddings(data_dir)
    
    # 모델 저장
    detector.save_model(output_model_path)
    
    return detector

def main():
    parser = argparse.ArgumentParser(description="얼굴 인식 및 이상 탐지 모델 학습")
    parser.add_argument("--data_dir", default="data/processed", help="훈련 데이터 디렉토리")
    parser.add_argument("--model_dir", default="data/models", help="모델 저장 디렉토리")
    parser.add_argument("--epochs", type=int, default=50, help="학습 에포크 수")
    parser.add_argument("--threshold", type=float, default=0.8, help="이상 탐지 임계값")
    parser.add_argument("--prepare_data", action="store_true", help="데이터 전처리 수행 여부")
    
    args = parser.parse_args()
    
    # 모델 저장 디렉토리 생성
    create_directory(args.model_dir)
    
    # 데이터 전처리 필요한 경우
    if args.prepare_data:
        print("데이터 전처리를 시작합니다...")
        prepare_dataset("data/raw", args.data_dir)
    
    # 얼굴 인식 모델 학습
    print("얼굴 인식 모델 학습을 시작합니다...")
    face_model_path = os.path.join(args.model_dir, "face_recognition_model.h5")
    train_face_recognition_model(args.data_dir, face_model_path, epochs=args.epochs)
    
    # 이상 탐지 모델 학습
    print("이상 탐지 모델 학습을 시작합니다...")
    anomaly_model_path = os.path.join(args.model_dir, "anomaly_detector.pkl")
    train_anomaly_detector(args.data_dir, anomaly_model_path, threshold=args.threshold)
    
    print("모델 학습이 완료되었습니다.")

if __name__ == "__main__":
    main()
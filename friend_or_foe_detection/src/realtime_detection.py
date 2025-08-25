"""
실시간 감지 스크립트: 카메라를 통해 아군/적군 식별 및 아군 신원 확인
"""
import os
import cv2
import numpy as np
import tensorflow as tf
import argparse
import time
from face_detection import FaceDetector
from anomaly_detection import AnomalyDetector
import pickle

class FaceRecognizer:
    """얼굴 인식 클래스"""
    
    def __init__(self, model_path=None, class_names_path=None):
        """
        얼굴 인식 클래스 초기화
        
        Args:
            model_path: 모델 파일 경로
            class_names_path: 클래스 이름 파일 경로
        """
        self.model = None
        self.class_names = None
        
        # 모델 로드
        if model_path and os.path.exists(model_path):
            self.load_model(model_path, class_names_path)
    
    def load_model(self, model_path, class_names_path=None):
        """
        저장된 모델 로드
        
        Args:
            model_path: 모델 파일 경로
            class_names_path: 클래스 이름 파일 경로
        """
        try:
            self.model = tf.keras.models.load_model(model_path)
            
            # 클래스 이름 로드
            if class_names_path is None:
                class_names_path = os.path.join(
                    os.path.dirname(model_path),
                    'class_names.pkl'
                )
            
            if os.path.exists(class_names_path):
                with open(class_names_path, 'rb') as f:
                    self.class_names = pickle.load(f)
            
            print(f"모델이 {model_path}에서 로드되었습니다.")
            if self.class_names:
                print(f"클래스 이름이 {class_names_path}에서 로드되었습니다. 클래스: {self.class_names}")
            return True
        
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            return False
    
    def predict(self, img, img_size=(224, 224)):
        """
        이미지에서 인물 식별
        
        Args:
            img: 입력 이미지
            img_size: 이미지 크기
            
        Returns:
            예측 클래스, 신뢰도
        """
        if self.model is None:
            print("모델이 로드되지 않았습니다.")
            return None, 0
        
        # 이미지 전처리
        if img.shape[:2] != img_size:
            img = cv2.resize(img, img_size)
        
        # 배치 차원 추가 및 정규화
        img_array = np.expand_dims(img, axis=0) / 255.0
        
        # 예측
        predictions = self.model.predict(img_array, verbose=0)
        
        # 최대 신뢰도 및 클래스 인덱스
        class_idx = np.argmax(predictions[0])
        confidence = predictions[0][class_idx]
        
        # 클래스 이름
        if self.class_names:
            class_name = self.class_names[class_idx]
        else:
            class_name = str(class_idx)
        
        return class_name, confidence

class RealtimeDetector:
    """실시간 얼굴 감지 및 식별 클래스"""
    
    def __init__(self, face_model_path=None, anomaly_model_path=None,
                 face_recognition_threshold=0.7, anomaly_threshold=0.8,
                 use_mediapipe=True, use_yolo=True):
        """
        실시간 감지 클래스 초기화
        
        Args:
            face_model_path: 얼굴 인식 모델 경로
            anomaly_model_path: 이상 탐지 모델 경로
            face_recognition_threshold: 얼굴 인식 임계값
            anomaly_threshold: 이상 탐지 임계값
            use_mediapipe: MediaPipe 사용 여부
            use_yolo: YOLO 사용 여부
        """
        self.face_recognition_threshold = face_recognition_threshold
        self.anomaly_threshold = anomaly_threshold
        
        # 클래스 이름 경로 계산
        if face_model_path:
            class_names_path = os.path.join(
                os.path.dirname(face_model_path),
                'class_names.pkl'
            )
        else:
            class_names_path = None
        
        # 특징 추출기 경로 계산
        if anomaly_model_path:
            feature_extractor_path = os.path.join(
                os.path.dirname(anomaly_model_path),
                'feature_extractor.h5'
            )
        else:
            feature_extractor_path = None
        
        # 얼굴 감지기 초기화
        self.face_detector = FaceDetector(
            use_mediapipe=use_mediapipe, 
            use_yolo=use_yolo
        )
        
        # 얼굴 인식 모델 초기화
        self.face_recognizer = FaceRecognizer(face_model_path, class_names_path)
        
        # 이상 탐지 모델 초기화
        self.anomaly_detector = AnomalyDetector(
            anomaly_model_path, 
            feature_extractor_path,
            threshold=anomaly_threshold
        )
    
    def process_frame(self, frame):
        """
        프레임 처리 (얼굴 감지 및 식별)
        
        Args:
            frame: 입력 영상 프레임
            
        Returns:
            result_frame: 결과 프레임 (시각화 포함)
            detections: 감지 결과 (바운딩 박스, 아군/적군 여부, 신원)
        """
        result_frame = frame.copy()
        detections = []
        
        # 얼굴 감지
        faces = self.face_detector.detect_faces(frame)
        
        for face in faces:
            x, y, w, h, conf, detector = face
            
            # 얼굴 영역 추출
            face_img = self.face_detector.extract_face(frame, face)
            
            if face_img is None:
                continue
            
            # 이상 탐지 (아군/적군 구분)
            is_friend, anomaly_conf, friend_class = self.anomaly_detector.detect(face_img)
            
            if is_friend:
                # 아군일 경우, 신원 식별
                person_name, recognition_conf = self.face_recognizer.predict(face_img)
                
                # 신뢰도가 임계값보다 낮으면 알 수 없음으로 처리
                if recognition_conf < self.face_recognition_threshold:
                    person_name = "Unknown Friend"
                
                # 녹색으로 표시
                color = (0, 255, 0)
                status = f"Friend: {person_name} ({recognition_conf:.2f})"
            else:
                # 적군일 경우, 빨간색으로 표시
                color = (0, 0, 255)
                person_name = None
                status = f"Foe ({anomaly_conf:.2f})"
            
            # 바운딩 박스 그리기
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, 2)
            
            # 상태 표시 (아군/적군, 신원)
            cv2.putText(result_frame, status, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 감지 결과 저장
            detection = {
                'bbox': (x, y, w, h),
                'is_friend': is_friend,
                'confidence': anomaly_conf if not is_friend else recognition_conf,
                'person_name': person_name
            }
            detections.append(detection)
        
        return result_frame, detections
    
    def run_camera(self, camera_id=0, window_name="Friend or Foe Detection", display_fps=True):
        """
        카메라를 통한 실시간 감지 실행
        
        Args:
            camera_id: 카메라 ID
            window_name: 창 이름
            display_fps: FPS 표시 여부
        """
        # 카메라 열기
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"카메라를 열 수 없습니다. ID: {camera_id}")
            return
        
        # 창 생성
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # FPS 계산 변수
        fps = 0
        frame_count = 0
        start_time = time.time()
        
        print("실시간 감지를 시작합니다. 종료하려면 'q' 키를 누르세요.")
        
        while True:
            # 프레임 읽기
            ret, frame = cap.read()
            if not ret:
                print("카메라에서 프레임을 읽을 수 없습니다.")
                break
            
            # 화면 좌우 반전 (거울 효과)
            frame = cv2.flip(frame, 1)
            
            # 프레임 처리
            result_frame, detections = self.process_frame(frame)
            
            # FPS 계산 및 표시
            if display_fps:
                frame_count += 1
                elapsed_time = time.time() - start_time
                
                if elapsed_time > 1:  # 1초마다 FPS 갱신
                    fps = frame_count / elapsed_time
                    frame_count = 0
                    start_time = time.time()
                
                cv2.putText(result_frame, f"FPS: {fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # 감지된 인물 수 표시
            cv2.putText(result_frame, f"Detected: {len(detections)}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # 화면 표시
            cv2.imshow(window_name, result_frame)
            
            # 'q' 키를 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # 자원 해제
        cap.release()
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="실시간 아군/적군 식별 시스템")
    parser.add_argument("--face_model", default="data/models/face_recognition_model.h5", 
                        help="얼굴 인식 모델 경로")
    parser.add_argument("--anomaly_model", default="data/models/anomaly_detector.pkl", 
                        help="이상 탐지 모델 경로")
    parser.add_argument("--camera", type=int, default=0, help="카메라 ID")
    parser.add_argument("--face_threshold", type=float, default=0.7, 
                        help="얼굴 인식 임계값")
    parser.add_argument("--anomaly_threshold", type=float, default=0.8, 
                        help="이상 탐지 임계값")
    parser.add_argument("--use_mediapipe", action="store_true", default=True, 
                        help="MediaPipe 사용 여부")
    parser.add_argument("--use_yolo", action="store_true", default=True, 
                        help="YOLO 사용 여부")
    
    args = parser.parse_args()
    
    # 모델 경로 확인
    if not os.path.exists(args.face_model):
        print(f"얼굴 인식 모델이 존재하지 않습니다: {args.face_model}")
        return
    
    if not os.path.exists(args.anomaly_model):
        print(f"이상 탐지 모델이 존재하지 않습니다: {args.anomaly_model}")
        return
    
    # 실시간 감지 객체 초기화
    detector = RealtimeDetector(
        face_model_path=args.face_model,
        anomaly_model_path=args.anomaly_model,
        face_recognition_threshold=args.face_threshold,
        anomaly_threshold=args.anomaly_threshold,
        use_mediapipe=args.use_mediapipe,
        use_yolo=args.use_yolo
    )
    
    # 카메라 실행
    detector.run_camera(camera_id=args.camera)

if __name__ == "__main__":
    main()
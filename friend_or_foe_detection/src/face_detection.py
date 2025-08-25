# """
# 얼굴 감지 모듈: MediaPipe와 YOLO를 사용하여 얼굴 감지
# """
# import cv2
# import numpy as np
# import mediapipe as mp
# from ultralytics import YOLO

# class FaceDetector:
#     """얼굴 감지 클래스"""
		
#     def __init__(self, use_mediapipe=True, use_yolo=True, 
#                  yolo_model_path="data/models/yolov8n-face.pt",
#                  mediapipe_confidence=0.5, yolo_confidence=0.5):
#         """
#         얼굴 감지 클래스 초기화
				
#         Args:
#             use_mediapipe: MediaPipe 사용 여부
#             use_yolo: YOLO 사용 여부
#             yolo_model_path: YOLO 모델 경로
#             mediapipe_confidence: MediaPipe 최소 감지 신뢰도
#             yolo_confidence: YOLO 최소 감지 신뢰도
#         """
#         self.use_mediapipe = use_mediapipe
#         self.use_yolo = use_yolo
				
#         # MediaPipe 초기화
#         if self.use_mediapipe:
#             self.mp_face_detection = mp.solutions.face_detection
#             self.mp_drawing = mp.solutions.drawing_utils
#             self.face_detection = self.mp_face_detection.FaceDetection(
#                 min_detection_confidence=mediapipe_confidence
#             )
				
#         # YOLO 초기화
#         if self.use_yolo:
#             try:
#                 self.yolo_model = YOLO(yolo_model_path)
#                 self.yolo_conf = yolo_confidence
#             except Exception as e:
#                 print(f"YOLO 모델 로드 실패: {e}")
#                 self.use_yolo = False
		
#     def detect_faces(self, frame):
#         """
#         프레임에서 얼굴을 감지하고 바운딩 박스 반환
				
#         Args:
#             frame: 입력 영상 프레임 (BGR)
						
#         Returns:
#             faces: 감지된 얼굴 목록 (x, y, w, h, confidence)
#         """
#         faces = []
#         h, w, _ = frame.shape
				
#         # MediaPipe로 얼굴 감지
#         if self.use_mediapipe:
#             # RGB 변환
#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = self.face_detection.process(rgb_frame)
						
#             if results.detections:
#                 for detection in results.detections:
#                     # 바운딩 박스 좌표 추출
#                     bbox = detection.location_data.relative_bounding_box
										
#                     # 상대 좌표를 절대 좌표로 변환
#                     xmin = max(0, int(bbox.xmin * w))
#                     ymin = max(0, int(bbox.ymin * h))
#                     width = min(w - xmin, int(bbox.width * w))
#                     height = min(h - ymin, int(bbox.height * h))
										
#                     # 신뢰도 점수
#                     confidence = detection.score[0]
										
#                     faces.append((xmin, ymin, width, height, float(confidence), 'mediapipe'))
				
#         # YOLO로 얼굴 감지
#         if self.use_yolo:
#             results = self.yolo_model(frame, conf=self.yolo_conf)[0]
						
#             for result in results.boxes.data.tolist():
#                 x1, y1, x2, y2, confidence, class_id = result
								
#                 # 절대 좌표로 변환
#                 xmin = int(x1)
#                 ymin = int(y1)
#                 width = int(x2 - x1)
#                 height = int(y2 - y1)
								
#                 faces.append((xmin, ymin, width, height, confidence, 'yolo'))
				
#         # 중복 제거 (IoU 기반)
#         if len(faces) > 1:
#             faces = self._non_max_suppression(faces)
				
#         return faces
		
#     def _non_max_suppression(self, boxes, iou_threshold=0.5):
#         """
#         중복된 바운딩 박스 제거 (Non-Maximum Suppression)
				
#         Args:
#             boxes: 바운딩 박스 목록 (x, y, w, h, confidence, detector)
#             iou_threshold: IoU 임계값
						
#         Returns:
#             선택된 바운딩 박스 목록
#         """
#         # 신뢰도에 따라 정렬
#         boxes = sorted(boxes, key=lambda x: x[4], reverse=True)
#         selected_boxes = []
				
#         while boxes:
#             current_box = boxes.pop(0)
#             selected_boxes.append(current_box)
						
#             # 현재 박스와 나머지 박스의 IoU 계산
#             remaining_boxes = []
#             for box in boxes:
#                 if self._calculate_iou(current_box[:4], box[:4]) < iou_threshold:
#                     remaining_boxes.append(box)
						
#             boxes = remaining_boxes
						
#         return selected_boxes
		
#     def _calculate_iou(self, box1, box2):
#         """
#         두 바운딩 박스의 IoU(Intersection over Union) 계산
				
#         Args:
#             box1: 첫 번째 바운딩 박스 (x, y, w, h)
#             box2: 두 번째 바운딩 박스 (x, y, w, h)
						
#         Returns:
#             IoU 값
#         """
#         # 박스 1의 좌표
#         x1_1, y1_1 = box1[0], box1[1]
#         x2_1, y2_1 = box1[0] + box1[2], box1[1] + box1[3]
				
#         # 박스 2의 좌표
#         x1_2, y1_2 = box2[0], box2[1]
#         x2_2, y2_2 = box2[0] + box2[2], box2[1] + box2[3]
				
#         # 교차 영역 계산
#         x1_i = max(x1_1, x1_2)
#         y1_i = max(y1_1, y1_2)
#         x2_i = min(x2_1, x2_2)
#         y2_i = min(y2_1, y2_2)
				
#         # 교차 영역이 없는 경우
#         if x2_i < x1_i or y2_i < y1_i:
#             return 0.0
				
#         # 교차 영역의 넓이
#         intersection_area = (x2_i - x1_i) * (y2_i - y1_i)
				
#         # 각 박스의 넓이
#         box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
#         box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
				
#         # 합집합 영역의 넓이
#         union_area = box1_area + box2_area - intersection_area
				
#         # IoU 계산
#         iou = intersection_area / union_area if union_area > 0 else 0.0
				
#         return iou
		
#     def draw_faces(self, frame, faces, color=(0, 255, 0), thickness=2):
#         """
#         프레임에 감지된 얼굴의 바운딩 박스 그리기
				
#         Args:
#             frame: 입력 영상 프레임
#             faces: 감지된 얼굴 목록 (x, y, w, h, confidence, detector)
#             color: 바운딩 박스 색상
#             thickness: 바운딩 박스 두께
						
#         Returns:
#             바운딩 박스가 그려진 프레임
#         """
#         result_frame = frame.copy()
				
#         for face in faces:
#             x, y, w, h, conf, detector = face
						
#             # 바운딩 박스 그리기
#             cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, thickness)
						
#             # 신뢰도 및 감지기 정보 표시
#             label = f"{detector}: {conf:.2f}"
#             cv2.putText(result_frame, label, (x, y - 10),
#                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
				
#         return result_frame
		
#     def extract_face(self, frame, face, target_size=(224, 224), add_margin=True):
#         """
#         프레임에서 얼굴 영역 추출
				
#         Args:
#             frame: 입력 영상 프레임
#             face: 얼굴 정보 (x, y, w, h, confidence, detector)
#             target_size: 추출할 얼굴 이미지 크기
#             add_margin: 여백 추가 여부
						
#         Returns:
#             추출된 얼굴 이미지
#         """
#         x, y, w, h, _, _ = face
#         h_frame, w_frame, _ = frame.shape
				
#         # 여백 추가
#         if add_margin:
#             margin = int(min(w, h) * 0.2)  # 20% 여백
#             x = max(0, x - margin)
#             y = max(0, y - margin)
#             w = min(w_frame - x, w + 2 * margin)
#             h = min(h_frame - y, h + 2 * margin)
				
#         # 얼굴 영역 추출
#         face_img = frame[y:y+h, x:x+w]
				
#         # 크기 조정
#         if face_img.size > 0:  # 유효한 얼굴 영역인지 확인
#             face_img = cv2.resize(face_img, target_size)
#             return face_img
#         else:
#             return None
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import numpy as np
import sys
import os

# matplotlib 경고 억제
os.environ['MPLCONFIGDIR'] = os.path.join(os.path.dirname(__file__), 'matplotlib_cache')

class FaceDetector:
		def __init__(self, model_path='data/models/efficientdet_lite0.tflite'):
				try:
						# 마지막 타임스탬프 저장
						self.last_timestamp = 0
						
						# model path 확인
						if not os.path.exists(model_path):
								raise FileNotFoundError(f"Model file not found: {model_path}")
						
						base_options = python.BaseOptions(model_asset_path=model_path)
						options = vision.ObjectDetectorOptions(
								base_options=base_options,
								running_mode=vision.RunningMode.LIVE_STREAM,
								score_threshold =0.5,
								result_callback=self.result_callback
						)
						self.face_detector = vision.ObjectDetector.create_from_options(options)
						self.latest_result = None
						print("FaceDetector initialized successfully")
						
				except Exception as e:
						print(f"FaceDetector 초기화 에러: {e}")
						raise

		def result_callback(self, result, image, timestamp_ms):
				try:
						# 결과를 전역 변수로 저장하지 않고 클래스 속성으로 저장
						self.latest_result = {
								'result': result,
								'image': image,
								'timestamp': timestamp_ms
						}
				except Exception as e:
						print(f"Callback error: {e}")

		def process_frame(self, frame, timestamp_ms):
				try:
						# 타임스탬프 단조증가 보장
						if timestamp_ms <= self.last_timestamp:
								timestamp_ms = self.last_timestamp + 1
						self.last_timestamp = timestamp_ms
						
						# BGR을 RGB로 변환
						rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
						
						# MediaPipe Image 생성
						image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
						
						# 비동기 얼굴 감지
						self.face_detector.detect_async(image, timestamp_ms)
						
				except Exception as e:
						print(f"Frame processing error: {e}")
						return False
				return True

		def run(self, video_source=0):
				# 카메라 열기
				cap = cv2.VideoCapture(video_source)
				
				# macOS 권한 문제 해결을 위한 설정
				if sys.platform == 'darwin':  # macOS
						cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('Y', 'U', 'Y', 'V'))
				
				if not cap.isOpened():
						print("카메라를 열 수 없습니다. 카메라 권한을 확인하세요.")
						return False
				
				# 프레임 카운터로 타임스탬프 생성
				frame_count = 0
				
				print("실행 중... ESC 키를 누르면 종료됩니다.")
				
				try:
						while True:
								ret, frame = cap.read()
								if not ret:
										print("프레임을 읽을 수 없습니다.")
										break
								
								frame_count += 1
								
								# 프레임 처리
								self.process_frame(frame, frame_count)
								
								# 결과 표시
								display_frame = frame.copy()
								
								if self.latest_result is not None:
										try:
												detection_result = self.latest_result['result']
												
												# 얼굴 그리기
												for detection in detection_result.detections:
														bbox = detection.bounding_box
														h, w, _ = frame.shape
														xmin = max(0, bbox.origin_x)
														ymin = max(0, bbox.origin_y)
														width = min(w - xmin, bbox.width)
														height = min(h - ymin,bbox.height)
														# 얼굴 영역 추출 (약간의 패딩 추가)
														padding_y = int(height * 0.45)
														ymini = max(ymin - padding_y, 0)
														
														padding_x = int(height * 0.1)
														xmini = max(xmin - padding_x, 0)
																		
														# 바운딩 박스
														# cv2.rectangle(display_frame, (xmini, ymini), (xmin+width+padding_x*2, ymin+height+10), (0, 255, 0), 2)
														cv2.rectangle(display_frame, (xmin,ymin), (xmin+width, ymin+height), (0, 255, 0), 2)

														# 신뢰도 표시
														if hasattr(detection, 'categories') and detection.categories:
																score = detection.categories[0].score
																cv2.putText(display_frame, f'{score:.2f}', (xmini, ymini-10),
																					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
										except Exception as e:
												print(f"Display error: {e}")
								
								# 화면에 표시
								cv2.imshow('Face Detection', display_frame)
								
								# ESC 키로 종료
								key = cv2.waitKey(1)
								if key == 27:  # ESC
										break
										
				except KeyboardInterrupt:
						print("\n프로그램을 종료합니다.")
				except Exception as e:
						print(f"실행 중 오류: {e}")
				finally:
						cap.release()
						cv2.destroyAllWindows()
						print("프로그램이 종료되었습니다.")

# 직접 실행할 때
if __name__ == "__main__":
		try:
				# 모델 파일 확인
				model_path = 'data/models/efficientdet_lite0.tflite'
				if not os.path.exists(model_path):
						print(f"모델 파일이 존재하지 않습니다: {model_path}")
						sys.exit(1)
				
				# 디텍터 생성 및 실행
				detector = FaceDetector(model_path)
				detector.run(video_source=0)
				
		except Exception as e:
				print(f"프로그램 오류: {e}")
				sys.exit(1)
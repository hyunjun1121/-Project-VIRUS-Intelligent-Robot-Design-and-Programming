import cv2
import numpy as np
from deepface import DeepFace
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def detect_and_draw_faces(image_path, detector_backend='retinaface', save_output=True):
		"""
		이미지에서 모든 얼굴을 탐지하고 박스를 그립니다.
		
		Parameters:
		- image_path: 입력 이미지 경로
		- detector_backend: 사용할 탐지기 ('retinaface', 'mtcnn', 'opencv', 'ssd', 'dlib')
		- save_output: 결과 이미지 저장 여부
		
		Returns:
		- faces: 탐지된 얼굴 정보 리스트
		- img_with_boxes: 박스가 그려진 이미지
		"""
		
		# 이미지 읽기
		img = cv2.imread(image_path)
		img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		
		# 얼굴 탐지 - RetinaFace가 가장 정확도가 높음
		faces = DeepFace.extract_faces(
				img_path=image_path,
				detector_backend=detector_backend,
				enforce_detection=False,
				align=False
		)
		
		# 원본 이미지에 박스 그리기
		img_with_boxes = img_rgb.copy()
		face_coords = []
		
		for i, face_data in enumerate(faces):
				# 얼굴 영역 좌표 가져오기
				facial_area = face_data['facial_area']
				x = facial_area['x']
				y = facial_area['y']
				w = facial_area['w']
				h = facial_area['h']
				
				# 박스 그리기
				cv2.rectangle(img_with_boxes, (x, y), (x+w, y+h), (0, 255, 0), 2)
				
				# 중심 좌표 계산
				center_x = x + w // 2
				center_y = y + h // 2
				
				# 중심점 표시
				cv2.circle(img_with_boxes, (center_x, center_y), 3, (255, 0, 0), -1)
				
				# 얼굴 번호 표시
				cv2.putText(img_with_boxes, f"Face {i+1}", (x, y-10), 
										cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
				
				face_coords.append({
						'face_id': i+1,
						'bbox': (x, y, w, h),
						'center': (center_x, center_y),
						'confidence': face_data.get('confidence', None)
				})
		
		# 결과 시각화
		plt.figure(figsize=(12, 8))
		plt.imshow(img_with_boxes)
		plt.axis('off')
		plt.title(f'Detected {len(faces)} faces')
		
		if save_output:
				plt.savefig('detected_faces.jpg', bbox_inches='tight', dpi=150)
				print(f"결과 이미지가 'detected_faces.jpg'로 저장되었습니다.")
		
		plt.show()
		
		# 탐지된 얼굴 정보 출력
		print(f"\n총 {len(faces)}개의 얼굴이 탐지되었습니다.")
		for face_info in face_coords:
				print(f"\nFace {face_info['face_id']}:")
				print(f"  - Bounding Box: {face_info['bbox']}")
				print(f"  - Center: {face_info['center']}")
				if face_info['confidence']:
						print(f"  - Confidence: {face_info['confidence']:.3f}")
		
		return face_coords, img_with_boxes
				
		# except Exception as e:
		#     print(f"얼굴 탐지 중 오류 발생: {str(e)}")
		#     return [], img_rgb

# 다중 탐지기를 사용한 앙상블 방식 (더 높은 정확도)
def detect_faces_ensemble(image_path, detectors=['retinaface', 'mtcnn'], threshold=0.5):
		"""
		여러 탐지기를 사용하여 더 정확한 얼굴 탐지를 수행합니다.
		
		Parameters:
		- image_path: 입력 이미지 경로
		- detectors: 사용할 탐지기 리스트
		- threshold: 탐지 임계값
		
		Returns:
		- merged_faces: 병합된 얼굴 탐지 결과
		"""
		
		all_detections = []
		
		for detector in detectors:
				try:
						faces = DeepFace.extract_faces(
								img_path=image_path,
								detector_backend=detector,
								enforce_detection=False,
								align=False
						)
						for face in faces:
								all_detections.append(face['facial_area'])
				except:
						continue
		
		# NMS (Non-Maximum Suppression)를 사용하여 중복 제거
		if all_detections:
				boxes = [[d['x'], d['y'], d['x']+d['w'], d['y']+d['h']] for d in all_detections]
				boxes = np.array(boxes)
				
				# 간단한 NMS 구현
				merged_boxes = []
				used = set()
				
				for i, box1 in enumerate(boxes):
						if i in used:
								continue
								
						merge_group = [box1]
						used.add(i)
						
						for j, box2 in enumerate(boxes[i+1:], i+1):
								if j in used:
										continue
										
								# IoU 계산
								x1 = max(box1[0], box2[0])
								y1 = max(box1[1], box2[1])
								x2 = min(box1[2], box2[2])
								y2 = min(box1[3], box2[3])
								
								if x1 < x2 and y1 < y2:
										intersection = (x2 - x1) * (y2 - y1)
										area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
										area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
										iou = intersection / (area1 + area2 - intersection)
										
										if iou > threshold:
												merge_group.append(box2)
												used.add(j)
						
						# 병합된 박스의 평균 계산
						if merge_group:
								merged_box = np.mean(merge_group, axis=0).astype(int)
								merged_boxes.append({
										'x': merged_box[0],
										'y': merged_box[1],
										'w': merged_box[2] - merged_box[0],
										'h': merged_box[3] - merged_box[1]
								})
				
				return merged_boxes
		
		return []

# 사용 예제
if __name__ == "__main__":
		# 기본 사용법
		image_path = "tot.jpg"  # 테스트할 이미지 경로
		
		# 단일 탐지기 사용 (빠르고 정확함)
		faces, result_img = detect_and_draw_faces(image_path, detector_backend='retinaface')
		
		# 앙상블 방식 사용 (더 높은 정확도)
		# ensemble_faces = detect_faces_ensemble(image_path, detectors=['retinaface', 'mtcnn'])
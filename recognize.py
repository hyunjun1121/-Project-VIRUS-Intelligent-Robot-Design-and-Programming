# recognize.py
import cv2
import pickle
import numpy as np
import time
from deepface import DeepFace

# 설정
EMBEDDINGS_PATH = "embeddings.pkl"
MODEL_NAME      = "VGG-Face"
DETECTOR_BACKEND= "opencv"
ENFORCE_DETECT  = False
DIST_METRIC     = "cosine"   # 'cosine' or 'euclidean'
THRESHOLD       = 0.4       # 거리 임계값 (실험적으로 조절)

# 폰트 설정
FONT_FACE = cv2.FONT_HERSHEY_DUPLEX  # 더 선명한 폰트
LABEL_FONT_SCALE = 0.7               # 메인 라벨 폰트 크기
LABEL_FONT_THICKNESS = 2             # 메인 라벨 폰트 두께
INFO_FONT_SCALE = 0.5                # 정보 라벨 폰트 크기
INFO_FONT_THICKNESS = 1              # 정보 라벨 폰트 두께

# 분석할 속성 설정
ANALYZE_FACE = True  # 얼굴 속성 분석 활성화/비활성화
ANALYZE_ACTIONS = ['age', 'gender', 'emotion', 'race']  # 분석할 속성들
PRINT_INTERVAL = 1.0  # 콘솔 출력 간격 (초)

# 1) 저장된 embeddings 로드
with open(EMBEDDINGS_PATH, "rb") as f:
    known_embeddings = pickle.load(f)

def compute_distance(a, b):
    if DIST_METRIC == "cosine":
        # cosine distance = 1 - cosine similarity
        return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    else:
        return np.linalg.norm(a - b)

def find_best_match(rep):
    best_person = None
    best_dist   = float("inf")
    # 모든 사람, 모든 vector 에 대해 최소 거리 탐색
    for person, vecs in known_embeddings.items():
        for db_vec in vecs:
            d = compute_distance(db_vec, rep)
            if d < best_dist:
                best_dist, best_person = d, person
    return best_person, best_dist

# 2) 카메라 열기
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

# 콘솔 출력을 위한 변수들
last_print_time = time.time()
detected_faces_info = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 매 프레임마다 정보 초기화
    detected_faces_info = []

    # 3) 얼굴만 잘라내기
    faces = DeepFace.extract_faces(
        img_path=rgb_frame,
        detector_backend=DETECTOR_BACKEND,
        enforce_detection=ENFORCE_DETECT,
        align=False
    )

    for face in faces:
        region = face["facial_area"]
        x, y, w, h = region["x"], region["y"], region["w"], region["h"]
        face_img = face["face"]

        # 4) 잘라낸 얼굴로부터 embedding 생성
        try:
            rep = DeepFace.represent(
                img_path=face_img,
                model_name=MODEL_NAME,
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=ENFORCE_DETECT
            )[0]

            # DeepFace.represent는 딕셔너리 형태로 반환함 
            # 임베딩 벡터를 추출하여 사용해야 함
            if 'embedding' in rep:
                rep = rep['embedding']
            elif 'representation' in rep:
                rep = rep['representation']
            else:
                # 임베딩 벡터가 없는 경우 스킵
                print("Error: Cannot find embedding vector in representation")
                continue

            # NumPy 배열로 변환
            rep = np.array(rep)
        except:
            continue

        # 얼굴 속성 분석 (선택적)
        face_info = ""
        if ANALYZE_FACE:
            try:
                # 얼굴 분석 실행
                analysis = DeepFace.analyze(
                    img_path=face_img,
                    actions=ANALYZE_ACTIONS,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=ENFORCE_DETECT,
                    silent=True
                )[0]  # 첫 번째 얼굴의 분석 결과
                
                # 분석 결과 정보 추출
                info_parts = []
                if 'age' in ANALYZE_ACTIONS:
                    info_parts.append(f"Age: {analysis['age']}")
                if 'gender' in ANALYZE_ACTIONS:
                    # 성별 정보 처리 - 확률 또는 단일 값 모두 처리 가능
                    if isinstance(analysis['gender'], dict):
                        # 확률 딕셔너리로 제공되는 경우 (예: {'Man': 0.8, 'Woman': 0.2})
                        dominant_gender = max(analysis['gender'], key=analysis['gender'].get)
                        info_parts.append(f"Gender: {dominant_gender}")
                    else:
                        # 단일 값으로 제공되는 경우 (예: 'Man')
                        info_parts.append(f"Gender: {analysis['gender']}")
                if 'emotion' in ANALYZE_ACTIONS:
                    emotion = analysis['emotion']
                    dominant_emotion = max(emotion, key=emotion.get)
                    info_parts.append(f"Emotion: {dominant_emotion}")
                if 'race' in ANALYZE_ACTIONS:
                    race = analysis['race']
                    dominant_race = max(race, key=race.get)
                    info_parts.append(f"Race: {dominant_race}")
                
                # 정보 문자열 생성
                face_info = " | ".join(info_parts)
            except Exception as e:
                face_info = "Analysis failed"
                print(f"Face analysis error: {str(e)}")

        # 5) 매칭
        name, dist = find_best_match(rep)
        if dist <= THRESHOLD:
            status = f"Ally: {name}"
            label = f"{status} ({dist:.3f})"
            color = (0, 255, 0)
        else:
            status = "Enemy"
            label = f"{status} ({dist:.3f})"
            color = (0, 0, 255)
        
        # 콘솔 출력용 정보 저장
        face_data = {
            "status": status,
            "distance": dist,
            "position": (x, y, w, h)
        }
        
        # 얼굴 속성 분석 정보 추가
        if ANALYZE_FACE:
            try:
                # 분석 결과가 있으면 콘솔 출력용 딕셔너리에 추가
                if 'age' in ANALYZE_ACTIONS and 'age' in analysis:
                    face_data["age"] = analysis['age']
                if 'gender' in ANALYZE_ACTIONS and 'gender' in analysis:
                    # 성별 정보 처리 - 확률 또는 단일 값 모두 처리 가능
                    if isinstance(analysis['gender'], dict):
                        # 확률 딕셔너리로 제공되는 경우
                        dominant_gender = max(analysis['gender'], key=analysis['gender'].get)
                        face_data["gender"] = dominant_gender
                    else:
                        # 단일 값으로 제공되는 경우
                        face_data["gender"] = analysis['gender']
                if 'emotion' in ANALYZE_ACTIONS and 'emotion' in analysis:
                    emotion = analysis['emotion']
                    face_data["emotion"] = max(emotion, key=emotion.get)
                if 'race' in ANALYZE_ACTIONS and 'race' in analysis:
                    race = analysis['race']
                    face_data["race"] = max(race, key=race.get)
            except:
                pass
        
        # 정보 리스트에 추가
        detected_faces_info.append(face_data)

        # 6) 화면에 그리기
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # 이름 라벨 배경 (가독성 향상을 위한 배경 상자)
        label_size = cv2.getTextSize(label, FONT_FACE, LABEL_FONT_SCALE, LABEL_FONT_THICKNESS)[0]
        cv2.rectangle(frame, 
                     (x, y-label_size[1]-10),
                     (x+label_size[0], y),
                     (0, 0, 0), -1)
        # 이름 라벨 텍스트
        cv2.putText(frame, label, (x, y-5), 
                    FONT_FACE, LABEL_FONT_SCALE, color, LABEL_FONT_THICKNESS)
        
        # 분석 정보 추가 (얼굴 아래)
        if face_info:
            # 정보가 길어질 수 있으므로 여러 줄로 표시
            face_info_lines = face_info.split(" | ")
            line_height = 20  # 줄 간격 증가
            
            for i, info_line in enumerate(face_info_lines):
                text_size = cv2.getTextSize(info_line, FONT_FACE, INFO_FONT_SCALE, INFO_FONT_THICKNESS)[0]
                y_pos = y + h + (i+1) * line_height
                
                # 배경 사각형 (가독성을 위해)
                cv2.rectangle(frame, 
                            (x, y_pos - line_height + 5), 
                            (x + text_size[0], y_pos + 5), 
                            (0, 0, 0), -1)
                # 텍스트
                cv2.putText(frame, info_line, (x, y_pos),
                        FONT_FACE, INFO_FONT_SCALE, (255, 255, 255), INFO_FONT_THICKNESS)

    # 1초마다 콘솔에 정보 출력
    current_time = time.time()
    if current_time - last_print_time >= PRINT_INTERVAL:
        print("\n" + "="*50)
        print(f"Number of faces detected: {len(detected_faces_info)}")
        
        for i, face in enumerate(detected_faces_info):
            print(f"\n[Face #{i+1}]")
            print(f"Status: {face['status']}, Distance: {face['distance']:.3f}")
            
            # 추가 속성 출력
            if 'age' in face:
                print(f"Age: {face['age']}")
            if 'gender' in face:
                print(f"Gender: {face['gender']}")
            if 'emotion' in face:
                print(f"Emotion: {face['emotion']}")
            if 'race' in face:
                print(f"Race: {face['race']}")
            
            print(f"Position: x={face['position'][0]}, y={face['position'][1]}, " 
                  f"w={face['position'][2]}, h={face['position'][3]}")
        
        if not detected_faces_info:
            print("No faces detected")
        
        print("="*50)
        last_print_time = current_time

    cv2.imshow("Face Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

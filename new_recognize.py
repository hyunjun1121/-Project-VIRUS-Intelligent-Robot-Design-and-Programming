import cv2
import os
import face_recognition

os.chdir(os.path.dirname(os.path.abspath(__file__)))

known_image = face_recognition.load_image_file("know_face/Hyunjun/IMG_0090.jpg")
known_encodings = face_recognition.face_encodings(known_image)

if len(known_encodings) == 0:
    raise Exception("Known face 이미지에서 얼굴이 인식되지 않았습니다. 다른 이미지를 사용해 주세요.")
known_encoding = known_encodings[0]

video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    rgb_frame = frame[:, :, ::-1]

    face_locations = face_recognition.face_locations(rgb_frame)

    # 얼굴이 없는 경우, 인코딩을 진행하지 않고 다음 프레임으로 이동
    if not face_locations:
        continue

    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces([known_encoding], face_encoding)
        match = matches[0]

        label = "True" if match else "False"
        color = (0, 255, 0) if match else (0, 0, 255)

        print(f"{label}, 좌표: 상단={top}, 우측={right}, 하단={bottom}, 좌측={left}")

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow('Face Recognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
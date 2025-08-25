import threading
import asyncio
import requests
from picamera import PiCamera
from datetime import datetime
import base64
import json
import time
import cv2
import picamera
import picamera.array
import numpy as np
# ===============================
# 이미지 캡처 함수
# ===============================
def capture_image(filename):
    camera = PiCamera()
    try:
        camera.start_preview()
        camera.rotation = 90  # 카메라 회전 설정
        time.sleep(1)
        camera.capture(filename)
        camera.stop_preview()
        print(f"📸 이미지 캡처 완료: {filename}")
    finally:
        camera.close()

# ===============================
# 비디오 프레임 캡처 클래스
# ===============================
class VideoFrameCapture:
    def __init__(self, duration=2, fps=3, width=640, height=480):
        self.duration = duration
        self.fps = fps
        self.frames = []
        self.width = width
        self.height = height

    def capture(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        frame_interval = 1.0 / self.fps
        start_time = time.time()
        last_time = 0
        frame_count = 0

        while time.time() - start_time < self.duration:
            ret, frame = cap.read()
            if not ret:
                break
            current_time = time.time()
            if current_time - last_time >= frame_interval:
                # 프레임 90도 회전
                frame_rotated = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                frame_resized = cv2.resize(frame_rotated, (self.width, self.height))
                _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_b64 = base64.b64encode(buffer).decode('utf-8')
                self.frames.append({
                    "frame_num": frame_count,
                    "timestamp": current_time - start_time,
                    "image": img_b64
                })
                frame_count += 1
                last_time = current_time

        cap.release()
        print(f"🎞️ 비디오 캡처 완료: {frame_count} 프레임")

# ===============================
# 서버로 이미지/비디오 업로드 함수
# ===============================
async def upload_file_async(filename_or_frames, server_url, filetype="image"):
    print(f"📡 {filetype.capitalize()} 업로드 중...")
    loop = asyncio.get_event_loop()

    if filetype == "image":
        # 이미지 파일을 읽어서 90도 회전
        img = cv2.imread(filename_or_frames)
        if img is not None:
            rotated_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            _, buffer = cv2.imencode('.jpg', rotated_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            encoded = base64.b64encode(buffer).tobytes().decode('utf-8')
        else:
            with open(filename_or_frames, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
        payload = {"image": encoded}

    elif filetype == "video":
        payload = {"frames": filename_or_frames}  # 이미 회전된 프레임 리스트

    else:
        raise ValueError("지원하지 않는 filetype")

    headers = {"Content-Type": "application/json"}
    response = await loop.run_in_executor(None, lambda: requests.post(server_url, json=payload, headers=headers))

    print(f"✅ 서버 응답: {response.status_code}")
    if response.ok:
        try:
            response_json = response.json()
            description = response_json.get("response", "(설명 없음)").strip()
        except Exception:
            description = response.text.strip()
        print("📄 설명 결과:")
        print(description)

        gpt_input = f"System: 이 {filetype}에 대한 설명을 GPT가 이해할 수 있게 정리합니다.\nUser: {description}"
        print("\n🧠 GPT 입력으로 사용할 수 있는 포맷:\n")
        print(gpt_input)
        return gpt_input
    else:
        print("❌ 서버 오류:", response.text)
        return None

# ===============================
# 메인 함수
# ===============================
def main(mode="image", server_url="https://02c4-34-126-104-160.ngrok-free.app/VLM"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if mode == "image":
        filename = f"capture_{timestamp}.jpg"
        thread = threading.Thread(target=capture_image, args=(filename,))
        thread.start()
        thread.join()
        asyncio.run(upload_file_async(filename, server_url, filetype="image"))

    elif mode == "video":
        # 영상은 다른 엔드포인트를 사용한다고 가정
        server_url = server_url.replace("/VLM", "/VLM_vid")
        vcap = VideoFrameCapture()
        vcap.capture()
        asyncio.run(upload_file_async(vcap.frames, server_url, filetype="video"))

    else:
        print("❓ 모드를 'image' 또는 'video'로 설정해주세요.")

if __name__ == "__main__":
    main(mode="image", server_url="https://02c4-34-126-104-160.ngrok-free.app/VLM")

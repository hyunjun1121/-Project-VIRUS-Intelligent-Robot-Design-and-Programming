import cv2
import threading
from colab_vlm import send_frame  # Import from colab_vlm.py
from colab_vlm_video import send_video_to_server
import picamera
import time
import picamera.array

# =========================
# 단일 이미지 캡처 및 업로드
# =========================
def capture_and_send_image():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        time.sleep(2)
        
        with picamera.array.PiRGBArray(camera) as output:
            
            output.truncate(0)
            
            camera.capture(output, format="bgr")  # BGR은 OpenCV용
            frame = output.array
            result = send_frame(frame.copy(), "VLM_face_area")
    return result

# =========================
# 다중 프레임 비디오 캡처 및 업로드
# =========================
def capture_and_send_video():
    # vcap = cv2.VideoCapture()
    # capture_thread = threading.Thread(target=vcap.capture_frames)
    # capture_thread.start()
    # capture_thread.join()

    # if not vcap.frames:
    #     print("no video frame")
    #     return

    # send_video_to_server(vcap.frames)
    return

# =========================
# 통합 실행 함수
# =========================
def main(mode="image"):
    if mode == "image":
        return capture_and_send_image()
    elif mode == "video":
        return capture_and_send_video()
    else:
        print("지원되지 않는 모드입니다.")
        return None

# =========================
if __name__ == "__main__":
    main("image")

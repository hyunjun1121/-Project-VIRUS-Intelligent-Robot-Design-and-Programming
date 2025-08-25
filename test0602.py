import cv2
import time
import picamera
import picamera.array

# 카메라 초기화
with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    time.sleep(2)  # 카메라 예열

    with picamera.array.PiRGBArray(camera) as output:
        while True:
            camera.capture(output, format="bgr")  # BGR은 OpenCV용
            frame = output.array

            # OpenCV로 이미지 처리
            cv2.imshow("Frame", frame)
            cv2.waitKey(0)
        cv2.destroyAllWindows()

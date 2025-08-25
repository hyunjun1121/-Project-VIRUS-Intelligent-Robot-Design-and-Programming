import cv2
import requests
import base64
import time
import picamera
import picamera.array
from threading import Thread

# Colab 서버 주소 (코랩에서 실행 후 변경 필요)
COLAB_URL = "https://fa2d-35-231-113-228.ngrok-free.app/"
# 실시간 처리 최적화 파라미터
MAX_FPS = 10  # 초당 전송 프레임 수 제한
COMPRESS_QUALITY = 70  # JPEG 압축 품질 (1-100)

def send_frame(frame, url):
    # 프레임 압축
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, COMPRESS_QUALITY])
    
    # Base64 인코딩
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    # 비동기 전송
    try:
        response = requests.post(
            COLAB_URL+url,
            json={'image': img_b64},
            headers={'Content-Type': 'application/json'},
            timeout=20  # 3초 타임아웃
        )
        if response.status_code == 200:
            #print("응답:", response.json()['response'])
            result = response.json()['response']
            print(result)
            return result
        else:
            print("서버 오류:", response.text)
            return None
    except Exception as e:
        print("전송 실패:", str(e))
        return None

def main():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        time.sleep(2)
        
        with picamera.array.PiRGBArray(camera) as output:
            last_time = 0
            while True:
                current_time = time.time()
                if current_time - last_time < 3:
                    continue
                last_time = current_time
                t= time.time()
                # 프레임 전처리
                
                output.truncate(0)
                
                camera.capture(output, format="bgr")  # BGR은 OpenCV용
                frame = output.array
                result = send_frame(frame.copy(), "VLM_face_area")
                rt = time.time()-t
                
                print("전송 시간:", rt)
                # make_img(result)
                if result is not None:
                    visualize_results(frame.copy(), result)
                cv2.imshow('fuck', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        #cap = cv2.VideoCapture(0)
        #last_time = time.time()
        cv2.destroyAllWindows()
def face_detect():
    
    frame = cv2.imread("target.jpg")
    t= time.time()
    # 프레임 전처리
    
    # frame = cv2.resize(frame, (640, 480))
    # 화면 출력 (옵션)
    
    # 별도 스레드에서 전송 (블로킹 방지)
    # Thread(target=send_frame, args=(frame.copy(),)).start()
    result = send_frame(frame.copy(), "VLM_face_area")
    rt = time.time()-t
    print("전송 시간:", rt)
    make_img(result)
    return 0
    
def make_img(faces):
    img_with_boxes = cv2.imread("target.jpg")
    for i, facial_area in enumerate(faces):
        # 얼굴 영역 좌표 가져오기
        # facial_area = face_data['facial_area']
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
    cv2.imshow('tmp', img_with_boxes)
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()


def visualize_results( frame, results, save_path='result.jpg'):
        """결과를 시각화합니다."""
        
        
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        for result in results:
            x, y, w, h = result['bbox']
            center_x, center_y = result['center']
            label = result['label']
            confidence = result['confidence']
            
            # 색상 설정 (아군: 초록색, 적군: 빨간색)
            if label == 'enemy':
                color = (255, 0, 0)  # 빨간색
            else:
                color = (0, 255, 0)  # 초록색
            
            # 박스 그리기
            cv2.rectangle(img_rgb, (x, y), (x+w, y+h), color, 2)
            
            # 중심점 표시
            cv2.circle(img_rgb, (center_x, center_y), 3, (0, 0, 255), -1)
            
            # 라벨과 신뢰도 표시
            label_text = f"{label} ({confidence:.2f})"
            cv2.putText(img_rgb, label_text, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 중심 좌표 표시
            coord_text = f"({center_x}, {center_y})"
            cv2.putText(img_rgb, coord_text, (x, y+h+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # 결과 저장 및 표시
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 8))
        plt.imshow(img_rgb)
        plt.axis('off')
        plt.title(f'Ally/Enemy Detection - {len(results)} faces detected')
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.show()
        
        return img_rgb

if __name__ == "__main__":
    main()
    # face_detect()



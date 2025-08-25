import cv2
import requests
import base64
import time
import json
from queue import Queue
import threading

# Colab 서버 주소 (코랩에서 실행 후 변경 필요)
COLAB_URL = "https://fb7a-34-126-104-160.ngrok-free.app/VLM_vid"

# 설정 파라미터
CAPTURE_DURATION = 2  # 캡처 시간 (초)
FPS = 3  # 초당 캡처할 프레임 수
COMPRESS_QUALITY = 70  # JPEG 압축 품질
RESIZE_WIDTH = 640
RESIZE_HEIGHT = 480

class VideoCapture:
    def __init__(self):
        self.frames = []
        self.capture_complete = False
        self.lock = threading.Lock()
        
    def capture_frames(self):
        """3초 동안 프레임 캡처"""
        cap = cv2.VideoCapture(0)
        
        # 웹캠 설정
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESIZE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESIZE_HEIGHT)
        
        print(f"📷 {CAPTURE_DURATION}초 동안 비디오 캡처 시작...")
        print("(ESC 키를 누르면 조기 종료)")
        time.sleep(1)  # 잠시 대기
        start_time = time.time()
        frame_interval = 1.0 / FPS
        last_capture_time = 0
        frame_count = 0
        
        while (time.time() - start_time) < CAPTURE_DURATION:
            ret, frame = cap.read()
            if not ret:
                print("프레임 읽기 실패")
                break
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            # FPS에 맞춰 프레임 캡처
            if current_time - last_capture_time >= frame_interval:
                # 프레임 리사이즈
                frame_resized = cv2.resize(frame, (RESIZE_WIDTH, RESIZE_HEIGHT))
                
                # JPEG 압축
                _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, COMPRESS_QUALITY])
                img_b64 = base64.b64encode(buffer).decode('utf-8')
                
                # 스레드 안전하게 리스트에 추가
                with self.lock:
                    self.frames.append({
                        'frame_num': frame_count,
                        'timestamp': elapsed,
                        'image': img_b64
                    })
                
                frame_count += 1
                last_capture_time = current_time
                
                # 화면에 표시
                remaining = CAPTURE_DURATION - elapsed
                # frm_cp = frame.copy()
                # cv2.putText(frm_cp, f"Recording: {frame_count} frames ({remaining:.1f}s left)", 
                #            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                # cv2.putText(frm_cp, f"Press ESC to stop early", 
                #            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                # cv2.imshow('Capture', frm_cp)
            
            if cv2.waitKey(1) == 27:  # ESC key
                print("사용자가 캡처를 중단했습니다.")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"캡처 완료: 총 {frame_count}개 프레임 ({elapsed:.1f}초)")
        self.capture_complete = True

def send_video_to_server(frames):
    """서버로 비디오 전송 및 결과 받기"""
    print(f"\n서버로 비디오 전송 중 ({len(frames)}개 프레임)...")
    
    try:
        # 요청 데이터 준비
        payload = {
            'frames': frames
        }
        
        # 서버로 전송
        start_time = time.time()
        response = requests.post(
            COLAB_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60  # 60초 타임아웃 (비디오 분석은 시간이 걸릴 수 있음)
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n응답 수신 완료 (소요 시간: {elapsed_time:.2f}초)")
            print(f"분석된 비디오 길이: {result['duration']:.1f}초")
            print(f"총 프레임 수: {result['total_frames']}")
            
            # 비디오 전체 설명 출력
            print("\n" + "="*80)
            print("🎬 비디오 분석 결과")
            print("="*80)
            print(result['response'])
            print("="*80)
            
            return result
        else:
            print(f"서버 오류: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.Timeout:
        print("요청 시간 초과 (비디오가 너무 길거나 서버가 바쁠 수 있습니다)")
        return None
    except Exception as e:
        print(f"전송 실패: {str(e)}")
        return None

def main():
    print("🎬 VLM 비디오 분석 클라이언트")
    print(f"서버 주소: {COLAB_URL}")
    print(f"캡처 설정: {CAPTURE_DURATION}초, {FPS} FPS")
    print("-" * 80)
    print("\n준비가 완료되면 Enter를 눌러 비디오 캡처를 시작하세요...")
    input()
    
    # 비디오 캡처 객체 생성
    capture = VideoCapture()
    
    # 별도 스레드에서 캡처 실행
    capture_thread = threading.Thread(target=capture.capture_frames)
    capture_thread.start()
    
    # 캡처 완료 대기
    capture_thread.join()
    
    # 캡처된 프레임 가져오기
    frames = capture.frames
    
    if not frames:
        print("캡처된 프레임이 없습니다.")
        return
    
    # 서버로 전송 및 결과 받기
    result = send_video_to_server(frames)
    # if result:
    #     print("\n분석 완료")
        
    #     # 결과를 파일로 저장
    #     timestamp = time.strftime("%Y%m%d_%H%M%S")
    #     filename = f'video_analysis_{timestamp}.json'
        
    #     with open(filename, 'w', encoding='utf-8') as f:
    #         json.dump({
    #             'capture_info': {
    #                 'duration': result['duration'],
    #                 'total_frames': result['total_frames'],
    #                 'fps': FPS,
    #                 'resolution': f"{RESIZE_WIDTH}x{RESIZE_HEIGHT}"
    #             },
    #             'analysis': result['response'],
    #             'timestamp': timestamp
    #         }, f, ensure_ascii=False, indent=2)
        
    #     print(f"📁 결과가 '{filename}' 파일로 저장되었습니다.")
    # else:
    #     print("\n분석 실패")
    
    print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
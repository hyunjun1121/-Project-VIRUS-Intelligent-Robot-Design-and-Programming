from PIL import Image
from llama_cpp import Llama
import cv2
import requests
import base64
import time
from threading import Thread
from llama_cpp.llama_chat_format import MiniCPMv26ChatHandler

def image_to_base64_data_uri(file_path):
    with open(file_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_data}"
def gen(path):
  try:
    data_uri = image_to_base64_data_uri(path)
    messages = [
        {"role": "system", "content": "이미지를 상세히 분석하고 요약하세요."},
        {"role": "user", "content": [
						{"type": "image_url", "image_url": {"url": data_uri }},
            {"type": "text", "text": "이미지에 대해 설명해. 이미지 내부에 있는 object들에 대해서 위치를 중점적으로 설명하고 특히 사람의 경우 더 자세히 설명해."},
        ]}
    ]

    # 추론 실행
    response = llm.create_chat_completion(
        messages=messages,
        temperature=0.3,
        max_tokens=512
    )
    return response['choices'][0]['message']['content']

  except Exception as e:
    print(e)
    return 'err'
model_path = '/Users/yangjiung/Downloads/Model-7.6B-Q4_K_M.gguf'
chat_handler = MiniCPMv26ChatHandler(clip_model_path="/Users/yangjiung/Downloads/mmproj-model-f16.gguf")
llm = Llama(model_path=model_path,
            n_ctx=4096,
            chat_handler=chat_handler,
            n_gpu_layers=-1,
            verbose=True)
while True:
    path = input("이미지 경로를 입력하세요: ")
    print(gen(path))


# Colab 서버 주소 (코랩에서 실행 후 변경 필요)
COLAB_URL = "https://ec73-34-169-95-178.ngrok-free.app/VLM"

# 실시간 처리 최적화 파라미터
MAX_FPS = 10  # 초당 전송 프레임 수 제한
COMPRESS_QUALITY = 70  # JPEG 압축 품질 (1-100)

def send_frame(frame):
    # 프레임 압축
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, COMPRESS_QUALITY])
    
    # Base64 인코딩
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    # 비동기 전송
    try:
        response = requests.post(
            COLAB_URL,
            json={'image': img_b64},
            headers={'Content-Type': 'application/json'},
            timeout=3  # 3초 타임아웃
        )
        if response.status_code == 200:
            print("응답:", response.json()['response'])
        else:
            print("서버 오류:", response.text)
    except Exception as e:
        print("전송 실패:", str(e))

def main():
    cap = cv2.VideoCapture(0)
    last_time = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # FPS 제어
        current_time = time.time()
        if current_time - last_time < 1/MAX_FPS:
            continue
        last_time = current_time
        
        # 프레임 전처리
        frame = cv2.resize(frame, (640, 480))
        
        gen(frame)
        
        # 화면 출력 (옵션)
        cv2.imshow('Webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()
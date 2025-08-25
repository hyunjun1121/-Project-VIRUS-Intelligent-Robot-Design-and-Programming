from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
import base64
def image_to_base64_data_uri(file_path):
    with open(file_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode('utf-8')
    # 확장자에 따라 MIME 타입을 알맞게 지정하세요 (예: png, jpeg 등)
    return f"data:image/jpeg;base64,{base64_data}"
chat_handler = Llava15ChatHandler(clip_model_path="/Users/develop/team8/mmproj-Qwen2.5-VL-7B-Instruct.gguf")
llm = Llama(
		model_path="/Users/develop/team8/Qwen2.5-VL-7B-Instruct.gguf",
		chat_handler=chat_handler
)
img_path = "/Users/develop/team8/KakaoTalk_Photo_2025-05-16-03-37-07.jpeg"
# data_uri = image_to_base64_data_uri(img_path)
messages = [
    {"role": "system", "content": "You are an assistant who perfectly describes images."},
    {"role": "user", "content": [
        {"type": "text", "text": "describe the image."},
        {"type": "image", "image": "/Users/develop/team8/KakaoTalk_Photo_2025-05-16-03-37-07.jpeg"}
    ]}
]
print("ready")
response = llm.create_chat_completion(messages=messages)
print(response["choices"][0]["message"]["content"])

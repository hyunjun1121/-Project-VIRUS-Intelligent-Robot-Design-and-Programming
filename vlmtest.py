import ollama
ollama.pull('gemma3:4b')

response = ollama.chat(model='gemma3:4b', 
    messages=[{
        'role': 'user', 
        'content': 'Describe the images',
        'images': ["/Users/develop/team8/KakaoTalk_Photo_2025-05-16-03-37-07.jpeg"]
    }],
)
print(response.message.content)
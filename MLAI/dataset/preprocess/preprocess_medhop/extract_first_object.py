import json
import os

def extract_first_object_supports(json_file_path, output_folder="./first_object_supports"):
    """
    JSON 파일의 첫 번째 객체의 supports 배열에 있는 문자열들을 
    개별 txt 파일로 저장하는 함수
    
    Args:
        json_file_path (str): JSON 파일 경로
        output_folder (str): 출력 폴더 경로
    """
    
    try:
        # JSON 파일 읽기
        print(f"파일 읽는 중: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 데이터가 배열인지 확인
        if not isinstance(data, list) or len(data) == 0:
            print("❌ JSON 파일이 비어있거나 배열 형태가 아닙니다.")
            return
        
        # 첫 번째 객체 가져오기
        first_object = data[0]
        print(f"첫 번째 객체를 찾았습니다.")
        
        # supports 배열 확인
        if 'supports' not in first_object:
            print("❌ 첫 번째 객체에 'supports' 필드가 없습니다.")
            return
        
        supports_list = first_object['supports']
        if not isinstance(supports_list, list):
            print("❌ 'supports' 필드가 배열 형태가 아닙니다.")
            return
        
        print(f"첫 번째 객체에서 {len(supports_list)}개의 supports를 발견했습니다.")
        
        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"폴더 생성: {output_folder}")
        
        # 각 supports 문자열을 개별 파일로 저장
        print(f"\n=== 개별 파일 저장 시작 ===")
        for i, support_text in enumerate(supports_list):
            # 파일명 생성 (3자리 숫자로 패딩)
            filename = f"first_support_{i+1:03d}.txt"
            filepath = os.path.join(output_folder, filename)
            
            # 파일에 supports 텍스트 저장
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(support_text)
            
            print(f"  저장: {filename}")
        
        print(f"\n✅ 총 {len(supports_list)}개의 개별 txt 파일을 {output_folder} 폴더에 저장했습니다.")
        
        # 첫 번째 객체의 다른 정보도 출력
        print(f"\n=== 첫 번째 객체 정보 ===")
        if 'query' in first_object:
            print(f"Query: {first_object['query']}")
        if 'candidates' in first_object:
            print(f"Candidates: {len(first_object['candidates'])}개")
        if 'answer' in first_object:
            print(f"Answer: {first_object['answer']}")
        if 'id' in first_object:
            print(f"ID: {first_object['id']}")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {json_file_path}")
    except json.JSONDecodeError:
        print(f"❌ JSON 파일 형식이 올바르지 않습니다: {json_file_path}")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")

def show_first_object_info(json_file_path):
    """
    첫 번째 객체의 구조와 정보를 보여주는 함수
    
    Args:
        json_file_path (str): JSON 파일 경로
    """
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        if isinstance(data, list) and len(data) > 0:
            first_object = data[0]
            
            print("=== 첫 번째 객체 구조 ===")
            for key, value in first_object.items():
                if isinstance(value, list):
                    print(f"{key}: 배열 (길이: {len(value)})")
                    if key == 'supports' and len(value) > 0:
                        print(f"  첫 번째 support 미리보기: {value[0][:100]}...")
                elif isinstance(value, str):
                    print(f"{key}: \"{value}\"")
                else:
                    print(f"{key}: {value}")
        else:
            print("❌ 유효한 데이터를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류: {e}")

# 사용 예시
if __name__ == "__main__":
    json_file = "qangaroo_v1.1/medhop/dev.json"
    
    # 첫 번째 객체 정보 확인
    print("=== 첫 번째 객체 정보 확인 ===")
    show_first_object_info(json_file)
    
    print("\n" + "="*50)
    
    # 첫 번째 객체의 supports 추출 및 저장
    extract_first_object_supports(json_file, "./first_object_supports") 
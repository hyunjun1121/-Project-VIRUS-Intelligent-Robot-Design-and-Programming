import json
import os
from typing import List

def create_question_answer_files_with_newline(json_file_paths: List[str], output_folder: str = "./qa_newline"):
    """
    여러 JSON 파일에서 각 객체마다 질문 파일과 답안 파일을 생성하는 함수
    (줄바꿈을 \\n으로 표기하여 qa_newline 폴더에 저장)
    
    Args:
        json_file_paths (List[str]): JSON 파일 경로들의 리스트
        output_folder (str): 출력 폴더 경로 (기본값: ./qa_newline)
    """
    
    # 출력 폴더 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"폴더 생성: {output_folder}")
    
    print(f"파일 저장 위치: {os.path.abspath(output_folder)}")
    
    total_processed = 0
    total_files_created = 0
    
    for file_path in json_file_paths:
        print(f"\n처리 중: {file_path}")
        
        try:
            # JSON 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            file_processed = 0
            file_files_created = 0
            
            # 각 객체 처리
            for item in data:
                if all(key in item for key in ['query', 'supports', 'candidates', 'id', 'answer']):
                    
                    # 1번 파일: 질문 파일 (id.txt)
                    question_filename = f"{item['id']}.txt"
                    question_filepath = os.path.join(output_folder, question_filename)
                    
                    # candidates를 \n으로 구분된 문자열로 변환 (실제 줄바꿈이 아닌 \n 문자)
                    if isinstance(item['candidates'], list):
                        candidates_text = '\\n'.join(item['candidates'])  # \\n으로 저장
                    else:
                        candidates_text = str(item['candidates'])
                    
                    question_content = f"""Answer the Question below. Choose the only one which is in the candidates below.\\n\\n#Question\\n{item['query']}\\n\\n#candidates\\n{candidates_text}"""
                    
                    # 질문 파일 저장
                    with open(question_filepath, 'w', encoding='utf-8') as file:
                        file.write(question_content)
                    
                    # 2번 파일: 답안 파일 (id_answer.txt)
                    answer_filename = f"{item['id']}_answer.txt"
                    answer_filepath = os.path.join(output_folder, answer_filename)
                    
                    # 답안 파일 저장
                    with open(answer_filepath, 'w', encoding='utf-8') as file:
                        file.write(item['answer'])
                    
                    file_processed += 1
                    file_files_created += 2
                    
                    # 진행 상황 출력 (100개마다)
                    if file_processed % 100 == 0:
                        print(f"  진행: {file_processed}개 객체 처리됨")
                
                else:
                    print(f"  ⚠️ 필수 필드가 없는 객체를 건너뜁니다: {item.get('id', '알 수 없음')}")
            
            print(f"  ✅ {file_processed}개 객체 처리, {file_files_created}개 파일 생성")
            total_processed += file_processed
            total_files_created += file_files_created
            
        except FileNotFoundError:
            print(f"  ❌ 파일을 찾을 수 없습니다: {file_path}")
        except json.JSONDecodeError:
            print(f"  ❌ JSON 파일 형식이 올바르지 않습니다: {file_path}")
        except Exception as e:
            print(f"  ❌ 오류가 발생했습니다: {e}")
    
    print(f"\n=== 전체 요약 ===")
    print(f"총 처리된 객체: {total_processed}개")
    print(f"생성된 파일: {total_files_created}개")
    print(f"질문 파일: {total_processed}개")
    print(f"답안 파일: {total_processed}개")
    print(f"저장 위치: {output_folder}")
    print(f"📝 줄바꿈이 \\n으로 표기됩니다.")



def main():
    """
    메인 실행 함수
    """
    
    # 입력 파일 경로들
    input_files = [
        "../../medhop/train.json",
        "../../medhop/dev.json"
    ]
    
    print("=== \\n 표기 버전으로 질문-답안 파일 생성 ===")
    create_question_answer_files_with_newline(input_files, "./qa_newline")

if __name__ == "__main__":
    main() 
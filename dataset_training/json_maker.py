import csv
import json
import os

def read_csv_column(filepath: str, column_name: str) -> list[str]:
    """
    CSV 파일에서 특정 컬럼의 데이터를 읽어 리스트로 반환합니다.
    여러 인코딩(utf-8, cp949, euc-kr, latin-1)을 시도합니다.

    Args:
        filepath (str): 읽을 CSV 파일의 경로입니다.
        column_name (str): 읽어올 컬럼의 헤더 이름입니다.

    Returns:
        list[str]: 해당 컬럼의 데이터 리스트입니다.
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 경우 발생합니다.
        ValueError: 해당 컬럼이 CSV 파일에 존재하지 않거나 파일을 읽을 수 없을 경우 발생합니다.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"오류: 파일 '{filepath}'를 찾을 수 없습니다.")

    encodings_to_try = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
    data = []
    
    for encoding in encodings_to_try:
        try:
            print(f"'{filepath}' 파일을 '{encoding}' 인코딩으로 읽기 시도 중...")
            with open(filepath, 'r', encoding=encoding) as csvfile:
                # 파일의 내용을 미리 읽어서 디코딩 오류를 먼저 확인
                content_check = csvfile.read()
                csvfile.seek(0) # 파일 포인터를 다시 처음으로 돌림
                
                reader = csv.DictReader(csvfile)
                if column_name not in reader.fieldnames:
                    # 이 경우는 인코딩 문제가 아니라 컬럼명 문제일 수 있으므로 루프를 계속하지 않고 바로 에러 발생
                    raise ValueError(f"오류: '{filepath}' 파일에 '{column_name}' 컬럼이 없습니다. 사용 가능한 컬럼: {reader.fieldnames}")
                
                # 컬럼이 존재하면 데이터 읽기
                for row in reader:
                    data.append(row[column_name])
            print(f"'{filepath}' 파일을 '{encoding}' 인코딩으로 읽기 성공.")
            return data # 성공적으로 읽었으면 함수 종료
        except UnicodeDecodeError:
            print(f"'{filepath}' 파일을 '{encoding}' 인코딩으로 읽기 실패.")
            data = [] # 데이터 리스트 초기화
            continue # 다음 인코딩 시도
        except ValueError as ve: # 컬럼명 오류는 여기서 처리하고 다시 raise
            raise ve

    # 모든 인코딩 시도 실패
    raise ValueError(f"오류: '{filepath}' 파일의 인코딩을 확인하거나 내용을 읽을 수 없습니다. (시도한 인코딩: {encodings_to_try})")

def create_sft_jsonl(user_contents: list[str], preferred_outputs: list[str], output_filepath: str):
    """
    입력된 사용자 내용과 선호 답변 리스트를 사용하여 SFT 학습용 JSON Lines 파일을 생성합니다.

    Args:
        user_contents (list[str]): User의 입력 내용 리스트입니다.
        preferred_outputs (list[str]): 선호되는 Assistant의 답변 리스트입니다.
        output_filepath (str): 저장할 JSON Lines 파일의 경로입니다.
    """
    num_records = min(len(user_contents), len(preferred_outputs))
    
    if len(user_contents) != num_records or len(preferred_outputs) != num_records:
        print(f"경고: 입력된 CSV 파일들의 행 개수가 다릅니다. 가장 적은 행 개수인 {num_records}개에 맞춰 JSONL 파일을 생성합니다.")
        print(f"  User Content 행 개수: {len(user_contents)}")
        print(f"  Preferred Output 행 개수: {len(preferred_outputs)}")

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        for i in range(num_records):
            json_record = {
                "messages": [
                    {
                        "role": "user",
                        "content": user_contents[i]
                    },
                    {
                        "role": "assistant",
                        "content": preferred_outputs[i]
                    }
                ]
            }
            outfile.write(json.dumps(json_record, ensure_ascii=False) + '\n')
    print(f"'{output_filepath}' 파일에 {num_records}개의 JSON 레코드가 저장되었습니다.")

if __name__ == "__main__":
    base_dir = "dataset_training"
    user_content_file = os.path.join(base_dir, "user_content.csv")
    prefer_output_file = os.path.join(base_dir, "prefer_output.csv")
    # non_preferred_output.csv는 SFT에 사용되지 않으므로 관련 코드 제거
    # non_preferred_output_file = os.path.join(base_dir, "non_preferred_output.csv") 
    output_jsonl_file = os.path.join(base_dir, "sft_dataset.jsonl") # 출력 파일명 변경

    try:
        # print 문은 read_csv_column 함수 내부로 이동했으므로 여기서는 제거하거나 주석 처리합니다.
        # print(f"'{user_content_file}'에서 'user_content' 컬럼 읽는 중...")
        user_data = read_csv_column(user_content_file, "user_content")
        
        # print(f"'{prefer_output_file}'에서 'prefer_output' 컬럼 읽는 중...")
        preferred_data = read_csv_column(prefer_output_file, "prefer_output")
        
        # print(f"'{non_preferred_output_file}'에서 'non_preferred_output' 컬럼 읽는 중...")
        # non_preferred_data = read_csv_column(non_preferred_output_file, "non_preferred_output")
        
        print("\nSFT JSONL 파일 생성 중...") # print 메시지 변경
        create_sft_jsonl(user_data, preferred_data, output_jsonl_file) # 변경된 함수 호출
        
    except FileNotFoundError as e:
        print(e)
        print("오류: 필요한 CSV 파일 중 하나 이상을 찾을 수 없습니다. 파일 경로와 파일명을 확인해주세요.")
        print(f"  예상 경로: {user_content_file}, {prefer_output_file}")
    except ValueError as e:
        print(e)
        print("오류: CSV 파일에서 지정된 컬럼을 찾을 수 없거나 파일 인코딩 문제일 수 있습니다. 각 CSV 파일의 헤더와 인코딩을 확인해주세요.")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

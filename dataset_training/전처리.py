import csv
import os

def create_final_csv(data_list: list[str], output_filename: str = "prefer_output.csv"):
    """
    주어진 리스트의 각 요소를 100번씩 반복하여 CSV 파일에 저장합니다.

    Args:
        data_list (list[str]): CSV에 저장할 문자열 리스트입니다.
        output_filename (str): 저장할 CSV 파일의 이름입니다. 기본값은 "prefer_output.csv"입니다.
    """
    output_dir = "dataset_training"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"'{output_dir}' 폴더가 생성되었습니다.")

    filepath = os.path.join(output_dir, output_filename)
    
    rows_to_write = []
    for item in data_list:
        rows_to_write.extend([item] * 100)
        
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['prefer_output'])  # 헤더 작성
        for row_data in rows_to_write:
            writer.writerow([row_data])
            
    print(f"'{filepath}' 파일에 총 {len(rows_to_write)}개의 행이 저장되었습니다.")

if __name__ == "__main__":
    # 예시 사용법
    example_list = ['"[ [{"cmd": "move", "val": 100}] ]"',
 '"[ [{"cmd": "move", "val": 100}] ]"',
 '"[ [{"cmd": "steer", "val": 90}], [{"cmd": "move", "val": -50}], [{"cmd": '
 '"move", "val": 50}], [{"cmd": "steer", "val": -90}] ]"',
 '"[ [{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": -45}], [{"cmd": '
 '"move", "val": 50}, {"cmd": "rotate_x", "val": -10}], [{"cmd": "move", '
 '"val": -50}, {"cmd": "rotate_x", "val": 10}], [{"cmd": "steer", "val": -90}, '
 '{"cmd": "rotate_x", "val": 90}], [{"cmd": "move", "val": 50}, {"cmd": '
 '"rotate_x", "val": 10}], [{"cmd": "move", "val": -50}, {"cmd": "rotate_x", '
 '"val": -10}], [{"cmd": "steer", "val": 45}, {"cmd": "rotate_x", "val": '
 '-45}], [{"cmd": "move", "val": 200}] ]"',
 '"[ [{"cmd": "steer", "val": -45}], [{"cmd": "move", "val": 100}, {"cmd": '
 '"rotate_x", "val": 360}], [{"cmd": "steer", "val": 90}], [{"cmd": "move", '
 '"val": 100}, {"cmd": "rotate_x", "val": 360}] ]"',
 '"[ [{"cmd": "move", "val": 50}], [{"cmd": "rotate_x", "val": 90}, {"cmd": '
 '"rotate_y", "val": 25}] ]"',
 '"[ [{"cmd": "move", "val": 200}], [{"cmd": "shoot", "val": 1}] ]"',
 '"[ [{"cmd": "move", "val": 300}] ]"',
 '"[]"',
 '"[ [{"cmd": "move", "val": 300}, {"cmd": "shoot", "val": 10}] ]"',
 '"[]"',
 '"[ [{"cmd": "move", "val": 300}] ]"',
 '"[ [{"cmd": "move", "val": -300}] ]"',
 '"[ [{"cmd": "move", "val": 100}], [{"cmd": "rotate_y", "val": 20}], [{"cmd": '
 '"steer", "val": 90}, [{"cmd": "move", "val": 100}], [{"cmd": "rotate_x", '
 '"val": -45}], [{"cmd": "rotate_x", "val": 90}], [{"cmd": "rotate_x", "val": '
 '-45}], [{"cmd": "steer", "val": -180}], [{"cmd": "move", "val": 200}], '
 '[{"cmd": "rotate_x", "val": -45}], [{"cmd": "rotate_x", "val": 90}], '
 '[{"cmd": "rotate_x", "val": -45}], [{"cmd": "steer", "val": 180}], [{"cmd": '
 '"move", "val": 100}], [{"cmd": "steer", "val": 90}], [{"cmd": "move", "val": '
 '100}], [{"cmd": "steer", "val": 180}], [{"cmd": "rotate_y", "val": -20}] ]"']
    create_final_csv(example_list)
    
    # 다른 예시 (짧은 리스트)
    # create_final_csv(["안녕하세요", "반갑습니다"])

"""
이미지 파일 이름 변경 스크립트: 이미지 파일 이름을 간단한 번호 형식으로 변경
"""
import os
import argparse
from tqdm import tqdm
import shutil
from PIL import Image, ExifTags
def correct_image_orientation(image_path):
    # 이미지 열기
    img = Image.open(image_path)

    # EXIF 데이터 확인
    try:
        # 이미지에서 EXIF 데이터를 추출
        exif = img._getexif()
        if exif is not None:
            # Orientation 태그를 찾음
            for tag, value in exif.items():
                if tag == 274:  # 274번 태그는 EXIF의 Orientation 태그
                    if value == 3:
                        img = img.rotate(180, expand=True)  # 180도 회전
                    elif value == 6:
                        img = img.rotate(270, expand=True)  # 270도 회전
                    elif value == 8:
                        img = img.rotate(90, expand=True)  # 90도 회전
        img.save(image_path)  # 수정된 이미지를 저장
    except (AttributeError, KeyError, IndexError):
        # EXIF 정보가 없는 경우 예외 처리
        pass

    return img

def rename_image_files(input_dir, output_dir=None, prefix="", start_number=1, extension="jpg"):
    """
    폴더 내의 이미지 파일 이름을 번호 형식으로 변경
    
    Args:
        input_dir: 이미지 파일이 있는 디렉토리
        output_dir: 이름이 변경된 이미지를 저장할 디렉토리 (None이면 원본 파일 덮어쓰기)
        prefix: 파일 이름 접두사 (예: "image_" -> "image_1.jpg")
        start_number: 시작 번호
        extension: 변경할 파일 확장자 (기본값: jpg)
    """
    # 이미지 파일 확장자 목록
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.JPG', '.JPEG', '.PNG', '.BMP']
    
    # 이미지 파일 목록 수집
    image_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_files.append(os.path.join(root, file))
    
    if not image_files:
        print(f"이미지 파일을 찾을 수 없습니다: {input_dir}")
        return False
    
    print(f"{len(image_files)}개의 이미지 파일을 찾았습니다.")
    
    # 출력 디렉토리 설정
    if output_dir:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"출력 디렉토리 생성: {output_dir}")
    else:
        output_dir = input_dir
    
    # 파일 이름 변경
    count = start_number
    renamed_files = []
    
    for img_path in tqdm(image_files, desc="이미지 이름 변경"):
        try:
            # 새 파일 이름 생성
            new_name = f"{prefix}{count}.{extension}"
            new_path = os.path.join(output_dir, new_name)
            
            # 이미 같은 이름의 파일이 있는지 확인
            while os.path.exists(new_path):
                count += 1
                new_name = f"{prefix}{count}.{extension}"
                new_path = os.path.join(output_dir, new_name)
            correct_image_orientation(img_path)
            # 파일 복사 또는 이름 변경
            if output_dir != input_dir:
                
                shutil.copy2(img_path, new_path)
            else:
                shutil.move(img_path, new_path)
            
            renamed_files.append((img_path, new_path))
            count += 1
                
        except Exception as e:
            print(f"파일 이름 변경 중 오류 발생: {img_path}, {e}")
    
    print(f"\n총 {len(renamed_files)}개의 이미지 파일 이름이 변경되었습니다.")
    print(f"이름 변경 범위: {prefix}{start_number}.{extension} ~ {prefix}{count-1}.{extension}")
    
    return renamed_files

def main():
    parser = argparse.ArgumentParser(description="이미지 파일 이름 번호 형식으로 변경")
    parser.add_argument("--input", required=True, help="이미지 파일이 있는 디렉토리")
    parser.add_argument("--output", help="이름이 변경된 이미지를 저장할 디렉토리 (지정하지 않으면 원본 파일 덮어쓰기)")
    parser.add_argument("--prefix", default="", help="파일 이름 접두사 (예: 'image_')")
    parser.add_argument("--start", type=int, default=1, help="시작 번호 (기본값: 1)")
    parser.add_argument("--ext", default="jpg", help="변경할 파일 확장자 (기본값: jpg)")
    
    args = parser.parse_args()
    
    rename_image_files(args.input, args.output, args.prefix, args.start, args.ext)

if __name__ == "__main__":
    main()
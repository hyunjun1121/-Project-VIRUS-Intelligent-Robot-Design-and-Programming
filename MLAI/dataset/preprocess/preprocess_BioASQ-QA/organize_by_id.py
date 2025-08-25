import os
import shutil
import re
from collections import defaultdict

def organize_files_by_id(qa_folder="./QA_files", document_folder="./document_files", output_folder="./organized_by_id"):
    """
    QA_files와 document_files의 파일들을 각 ID별로 묶어서 정리하는 함수
    
    Args:
        qa_folder (str): QA 파일들이 있는 폴더 경로
        document_folder (str): Document 파일들이 있는 폴더 경로  
        output_folder (str): 정리된 파일들을 저장할 폴더 경로
    """
    
    # 출력 폴더 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ 출력 폴더 생성: {output_folder}")
    
    # ID별로 파일들을 그룹화할 딕셔너리
    id_files = defaultdict(list)
    
    print("=== 파일 분석 시작 ===")
    
    # 1. QA 파일들 분석
    qa_files_count = 0
    if os.path.exists(qa_folder):
        for filename in os.listdir(qa_folder):
            if filename.endswith('.txt'):
                # 파일명 패턴: {type}_{id}.txt
                # 예: summary_55031181e9bde69634000014.txt
                match = re.match(r'(.+)_([^_]+)\.txt$', filename)
                if match:
                    question_type, question_id = match.groups()
                    file_path = os.path.join(qa_folder, filename)
                    id_files[question_id].append(('qa', file_path, filename))
                    qa_files_count += 1
                else:
                    print(f"⚠️ QA 파일명 패턴이 맞지 않음: {filename}")
    
    print(f"✅ QA 파일 분석 완료: {qa_files_count}개 파일")
    
    # 2. Document 파일들 분석
    document_files_count = 0
    if os.path.exists(document_folder):
        for filename in os.listdir(document_folder):
            if filename.endswith('.txt'):
                # 파일명 패턴: document_{id}_{순서}_{beginSection}.txt
                # 예: document_55031181e9bde69634000014_001_sections.txt
                match = re.match(r'document_([^_]+)_(.+)\.txt$', filename)
                if match:
                    question_id, rest = match.groups()
                    file_path = os.path.join(document_folder, filename)
                    id_files[question_id].append(('document', file_path, filename))
                    document_files_count += 1
                else:
                    print(f"⚠️ Document 파일명 패턴이 맞지 않음: {filename}")
    
    print(f"✅ Document 파일 분석 완료: {document_files_count}개 파일")
    
    # 3. ID별로 폴더 생성 및 파일 이동
    print(f"\n=== ID별 폴더 정리 시작 ===")
    print(f"발견된 고유 ID 수: {len(id_files)}개")
    
    total_moved_files = 0
    for i, (question_id, files) in enumerate(id_files.items(), 1):
        # ID별 폴더 생성
        id_folder = os.path.join(output_folder, question_id)
        if not os.path.exists(id_folder):
            os.makedirs(id_folder)
        
        # 해당 ID의 파일들 이동
        qa_count = 0
        doc_count = 0
        
        for file_type, src_path, filename in files:
            dst_path = os.path.join(id_folder, filename)
            
            try:
                shutil.copy2(src_path, dst_path)
                total_moved_files += 1
                
                if file_type == 'qa':
                    qa_count += 1
                else:
                    doc_count += 1
                    
            except Exception as e:
                print(f"❌ 파일 복사 실패: {filename} -> {e}")
        
        # 진행 상황 출력 (100개마다)
        if i % 100 == 0:
            print(f"    진행: {i}/{len(id_files)} ID 처리됨")
        
        # 첫 10개 ID에 대해서는 상세 정보 출력
        if i <= 10:
            print(f"  ID: {question_id}")
            print(f"    - QA 파일: {qa_count}개")
            print(f"    - Document 파일: {doc_count}개")
            print(f"    - 총 파일: {len(files)}개")
    
    print(f"\n{'='*60}")
    print(f"=== 정리 완료 요약 ===")
    print(f"처리된 고유 ID: {len(id_files)}개")
    print(f"이동된 총 파일: {total_moved_files}개")
    print(f"  - QA 파일: {qa_files_count}개")
    print(f"  - Document 파일: {document_files_count}개")
    print(f"출력 폴더: {output_folder}")
    print(f"{'='*60}")

def analyze_file_structure(qa_folder="./QA_files", document_folder="./document_files"):
    """
    현재 파일 구조를 분석하는 함수
    """
    print("=== 현재 파일 구조 분석 ===")
    
    # QA 파일 분석
    qa_count = 0
    qa_sample = []
    if os.path.exists(qa_folder):
        qa_files = [f for f in os.listdir(qa_folder) if f.endswith('.txt')]
        qa_count = len(qa_files)
        qa_sample = qa_files[:5]  # 처음 5개만 샘플로
    
    print(f"QA 파일 수: {qa_count}개")
    if qa_sample:
        print("QA 파일 샘플:")
        for filename in qa_sample:
            print(f"  - {filename}")
    
    # Document 파일 분석
    doc_count = 0
    doc_sample = []
    if os.path.exists(document_folder):
        doc_files = [f for f in os.listdir(document_folder) if f.endswith('.txt')]
        doc_count = len(doc_files)
        doc_sample = doc_files[:5]  # 처음 5개만 샘플로
    
    print(f"\nDocument 파일 수: {doc_count}개")
    if doc_sample:
        print("Document 파일 샘플:")
        for filename in doc_sample:
            print(f"  - {filename}")
    
    # ID 분석
    ids_from_qa = set()
    ids_from_doc = set()
    
    if os.path.exists(qa_folder):
        for filename in os.listdir(qa_folder):
            if filename.endswith('.txt'):
                match = re.match(r'(.+)_([^_]+)\.txt$', filename)
                if match:
                    ids_from_qa.add(match.groups()[1])
    
    if os.path.exists(document_folder):
        for filename in os.listdir(document_folder):
            if filename.endswith('.txt'):
                match = re.match(r'document_([^_]+)_(.+)\.txt$', filename)
                if match:
                    ids_from_doc.add(match.groups()[0])
    
    print(f"\nID 분석:")
    print(f"  - QA에서 발견된 고유 ID: {len(ids_from_qa)}개")
    print(f"  - Document에서 발견된 고유 ID: {len(ids_from_doc)}개")
    print(f"  - 공통 ID: {len(ids_from_qa & ids_from_doc)}개")
    
    # QA에만 있거나 Document에만 있는 ID 확인
    qa_only = ids_from_qa - ids_from_doc
    doc_only = ids_from_doc - ids_from_qa
    
    if qa_only:
        print(f"  - QA에만 있는 ID: {len(qa_only)}개")
        if len(qa_only) <= 5:
            print(f"    예시: {list(qa_only)}")
    
    if doc_only:
        print(f"  - Document에만 있는 ID: {len(doc_only)}개")
        if len(doc_only) <= 5:
            print(f"    예시: {list(doc_only)}")

def main():
    """
    메인 실행 함수
    """
    print("=== BioASQ 파일 ID별 정리 도구 ===\n")
    
    # 현재 파일 구조 분석
    analyze_file_structure()
    
    print(f"\n{'='*60}")
    
    # 사용자 확인
    response = input("파일들을 ID별로 정리하시겠습니까? (y/n): ").strip().lower()
    
    if response in ['y', 'yes', '예', 'ㅇ']:
        print("\n=== 파일 정리 시작 ===")
        organize_files_by_id()
        print("\n✅ 모든 작업이 완료되었습니다!")
    else:
        print("작업을 취소했습니다.")

if __name__ == "__main__":
    main() 
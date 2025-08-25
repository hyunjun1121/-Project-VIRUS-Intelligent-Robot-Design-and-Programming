#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abstract 파일명에 Document 개수 추가

factoid_{id}.txt -> {document_count}_factoid_{id}.txt 형식으로 변경
"""

import json
import os
import re
import sys
from typing import Dict

def load_document_counts(json_file: str) -> Dict[str, int]:
    """
    JSON 파일에서 각 질문 ID별 document 개수를 추출
    
    Args:
        json_file: BioASQ JSON 파일 경로
        
    Returns:
        ID -> document 개수 매핑 딕셔너리
    """
    print(f"JSON 파일에서 document 개수 로드 중: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
        elif isinstance(data, list):
            questions = data
        else:
            raise ValueError("지원되지 않는 JSON 구조입니다.")
        
        document_counts = {}
        
        for question in questions:
            if question.get('type') == 'factoid':
                question_id = question.get('id', '')
                documents = question.get('documents', [])
                document_count = len(documents)
                
                if question_id:
                    document_counts[question_id] = document_count
        
        print(f"총 {len(document_counts)}개의 factoid 질문 document 개수 로드 완료")
        return document_counts
        
    except Exception as e:
        print(f"JSON 파일 로드 중 오류: {e}")
        return {}

def extract_id_from_filename(filename: str) -> str:
    """
    factoid_{id}.txt 파일명에서 ID 추출
    
    Args:
        filename: 파일명
        
    Returns:
        추출된 ID (없으면 빈 문자열)
    """
    # factoid_{id}.txt 패턴에서 ID 추출
    match = re.match(r'factoid_([a-f0-9]+)\.txt$', filename)
    if match:
        return match.group(1)
    return ""

def rename_abstract_files(abstracts_dir: str, document_counts: Dict[str, int]):
    """
    Abstract 파일들의 이름을 document 개수 포함 형식으로 변경
    
    Args:
        abstracts_dir: abstracts 폴더 경로
        document_counts: ID -> document 개수 매핑
    """
    if not os.path.exists(abstracts_dir):
        print(f"abstracts 폴더가 존재하지 않습니다: {abstracts_dir}")
        return
    
    files = [f for f in os.listdir(abstracts_dir) if f.endswith('.txt')]
    print(f"처리할 파일 수: {len(files)}")
    
    success_count = 0
    error_count = 0
    not_found_count = 0
    
    for filename in files:
        try:
            # ID 추출
            question_id = extract_id_from_filename(filename)
            if not question_id:
                print(f"ID 추출 실패: {filename}")
                error_count += 1
                continue
            
            # Document 개수 찾기
            if question_id not in document_counts:
                print(f"Document 개수 정보 없음: {question_id}")
                not_found_count += 1
                continue
            
            doc_count = document_counts[question_id]
            
            # 새 파일명 생성
            new_filename = f"{doc_count}_{filename}"
            
            # 파일명 변경
            old_path = os.path.join(abstracts_dir, filename)
            new_path = os.path.join(abstracts_dir, new_filename)
            
            if os.path.exists(new_path):
                print(f"새 파일명이 이미 존재: {new_filename}")
                error_count += 1
                continue
            
            os.rename(old_path, new_path)
            print(f"변경 완료: {filename} -> {new_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"파일 처리 중 오류 ({filename}): {e}")
            error_count += 1
    
    print(f"\n=== 파일명 변경 완료 ===")
    print(f"성공: {success_count}개")
    print(f"오류: {error_count}개")
    print(f"document 정보 없음: {not_found_count}개")
    print(f"총 처리: {len(files)}개")

def main():
    """메인 함수"""
    # 경로 설정
    base_dir = r"E:\Project\dataset\preprocess\preprocess_BioASQ-QA"
    json_file = r"E:\Project\dataset\BioASQ-QA\training11b.json"
    abstracts_dir = os.path.join(base_dir, "abstracts")
    
    print("=== Abstract 파일명에 Document 개수 추가 ===")
    print(f"Base directory: {base_dir}")
    print(f"JSON file: {json_file}")
    print(f"Abstracts directory: {abstracts_dir}")
    
    # Document 개수 로드
    document_counts = load_document_counts(json_file)
    if not document_counts:
        print("Document 개수 정보를 로드할 수 없습니다.")
        return
    
    # 파일명 변경
    rename_abstract_files(abstracts_dir, document_counts)

if __name__ == "__main__":
    main() 
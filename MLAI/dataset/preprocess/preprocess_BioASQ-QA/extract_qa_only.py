#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BioASQ-QA QA 데이터만 추출하는 스크립트

factoid 타입 질문에서 body, ideal_answer, exact_answer를 추출하여 저장합니다.
"""

import json
import os
import sys
from typing import List, Dict

def load_bioasq_data(json_file: str) -> List[Dict]:
    """
    BioASQ JSON 파일을 로드하고 factoid 타입만 필터링
    
    Args:
        json_file: BioASQ JSON 파일 경로
        
    Returns:
        factoid 타입 질문 리스트
    """
    print(f"JSON 파일 로드 중: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
        elif isinstance(data, list):
            questions = data
        else:
            raise ValueError("지원되지 않는 JSON 구조입니다.")
        
        # factoid 타입만 필터링
        factoid_questions = [q for q in questions if q.get('type') == 'factoid']
        
        print(f"전체 질문 수: {len(questions)}")
        print(f"factoid 타입 질문 수: {len(factoid_questions)}")
        
        return factoid_questions
        
    except Exception as e:
        print(f"JSON 파일 로드 중 오류: {str(e)}")
        sys.exit(1)

def process_qa_data(factoid_questions: List[Dict], output_dir: str):
    """
    factoid 타입 질문들의 QA 데이터를 추출하여 저장
    
    Args:
        factoid_questions: factoid 타입 질문 리스트
        output_dir: 출력 디렉토리
    """
    print(f"\n=== QA 데이터 추출 시작 ===")
    
    # 출력 디렉토리 생성
    qa_dir = os.path.join(output_dir, "qa_data")
    os.makedirs(qa_dir, exist_ok=True)
    
    for i, question in enumerate(factoid_questions):
        question_id = question.get('id', f'unknown_{i}')
        
        print(f"처리 중 {i+1}/{len(factoid_questions)}: {question_id}")
        
        # QA 데이터 추출
        body = question.get('body', '')
        ideal_answer = question.get('ideal_answer', [])
        exact_answer = question.get('exact_answer', [])
        
        # 파일 내용 구성
        qa_content = []
        qa_content.append(f"QUESTION: {body}")
        qa_content.append("")
        
        if ideal_answer:
            qa_content.append("IDEAL_ANSWER:")
            for ans in ideal_answer:
                qa_content.append(f"- {ans}")
            qa_content.append("")
        
        if exact_answer:
            qa_content.append("EXACT_ANSWER:")
            for ans in exact_answer:
                qa_content.append(f"- {ans}")
        
        # 파일로 저장
        filename = f"QA_{question_id}.txt"
        filepath = os.path.join(qa_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(qa_content))
        
        print(f"  저장 완료: {filename}")

def main():
    # 파일 경로 설정
    json_file = r"E:\Project\dataset\BioASQ-QA\training11b.json"
    output_dir = r"E:\Project\dataset\preprocess\preprocess_BioASQ-QA"
    
    try:
        # 1. JSON 데이터 로드 및 factoid 필터링
        factoid_questions = load_bioasq_data(json_file)
        
        if not factoid_questions:
            print("factoid 타입 질문이 없습니다.")
            return
        
        # 2. QA 데이터 추출 및 저장
        process_qa_data(factoid_questions, output_dir)
        
        print(f"\n=== QA 데이터 추출 완료 ===")
        print(f"결과 저장 위치: {os.path.join(output_dir, 'qa_data')}")
        
    except Exception as e:
        print(f"QA 데이터 추출 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
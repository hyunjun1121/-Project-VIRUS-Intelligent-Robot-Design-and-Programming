#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BioASQ-QA 데이터의 각 질문별 document 수 분석

각 factoid 질문에 연결된 documents 배열의 길이를 분석합니다.
"""

import json
import os
import sys
from collections import Counter
from typing import Dict, List

def analyze_document_counts(json_file: str) -> Dict:
    """
    JSON 파일에서 각 질문의 document 수 분석
    
    Args:
        json_file: BioASQ JSON 파일 경로
        
    Returns:
        분석 결과 딕셔너리
    """
    print(f"JSON 파일 분석 중: {json_file}")
    
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
        
        # 각 질문의 document 수 분석
        document_counts = {}
        document_count_distribution = []
        
        for question in factoid_questions:
            question_id = question.get('id', 'unknown')
            documents = question.get('documents', [])
            doc_count = len(documents)
            
            document_counts[question_id] = doc_count
            document_count_distribution.append(doc_count)
        
        # 통계 계산
        total_questions = len(factoid_questions)
        total_documents = sum(document_count_distribution)
        avg_documents = total_documents / total_questions if total_questions > 0 else 0
        
        count_distribution = Counter(document_count_distribution)
        
        analysis_result = {
            'total_questions': total_questions,
            'total_documents': total_documents,
            'average_documents_per_question': avg_documents,
            'document_counts_by_id': document_counts,
            'distribution': dict(count_distribution),
            'min_documents': min(document_count_distribution) if document_count_distribution else 0,
            'max_documents': max(document_count_distribution) if document_count_distribution else 0
        }
        
        return analysis_result
        
    except Exception as e:
        print(f"JSON 파일 분석 중 오류: {str(e)}")
        sys.exit(1)

def print_analysis_summary(analysis: Dict):
    """
    분석 결과 요약 출력
    
    Args:
        analysis: 분석 결과 딕셔너리
    """
    print(f"\n=== Document 수 분석 결과 ===")
    print(f"총 질문 수: {analysis['total_questions']}")
    print(f"총 document 수: {analysis['total_documents']}")
    print(f"질문당 평균 document 수: {analysis['average_documents_per_question']:.2f}")
    print(f"최소 document 수: {analysis['min_documents']}")
    print(f"최대 document 수: {analysis['max_documents']}")
    
    print(f"\n=== Document 수 분포 ===")
    distribution = analysis['distribution']
    for doc_count in sorted(distribution.keys()):
        question_count = distribution[doc_count]
        percentage = (question_count / analysis['total_questions']) * 100
        print(f"{doc_count}개 documents: {question_count}개 질문 ({percentage:.1f}%)")

def print_detailed_counts(analysis: Dict, limit: int = 20):
    """
    상세한 ID별 document 수 출력
    
    Args:
        analysis: 분석 결과 딕셔너리
        limit: 출력할 최대 개수
    """
    print(f"\n=== ID별 Document 수 (처음 {limit}개) ===")
    document_counts = analysis['document_counts_by_id']
    
    for i, (question_id, doc_count) in enumerate(document_counts.items()):
        if i >= limit:
            break
        print(f"{question_id}: {doc_count}개 documents")
    
    if len(document_counts) > limit:
        print(f"... 외 {len(document_counts) - limit}개 더")

def save_detailed_report(analysis: Dict, output_file: str):
    """
    상세 보고서를 파일로 저장
    
    Args:
        analysis: 분석 결과 딕셔너리
        output_file: 출력 파일 경로
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("BioASQ-QA Document 수 분석 보고서\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"총 질문 수: {analysis['total_questions']}\n")
        f.write(f"총 document 수: {analysis['total_documents']}\n")
        f.write(f"질문당 평균 document 수: {analysis['average_documents_per_question']:.2f}\n")
        f.write(f"최소 document 수: {analysis['min_documents']}\n")
        f.write(f"최대 document 수: {analysis['max_documents']}\n\n")
        
        f.write("Document 수 분포:\n")
        distribution = analysis['distribution']
        for doc_count in sorted(distribution.keys()):
            question_count = distribution[doc_count]
            percentage = (question_count / analysis['total_questions']) * 100
            f.write(f"  {doc_count}개 documents: {question_count}개 질문 ({percentage:.1f}%)\n")
        
        f.write("\nID별 Document 수:\n")
        document_counts = analysis['document_counts_by_id']
        for question_id, doc_count in document_counts.items():
            f.write(f"  {question_id}: {doc_count}개\n")
    
    print(f"상세 보고서 저장: {output_file}")

def main():
    """메인 함수"""
    json_file = r"E:\Project\dataset\BioASQ-QA\training11b.json"
    output_dir = r"E:\Project\dataset\preprocess\preprocess_BioASQ-QA"
    
    # 분석 실행
    analysis = analyze_document_counts(json_file)
    
    # 결과 출력
    print_analysis_summary(analysis)
    print_detailed_counts(analysis, limit=10)
    
    # 상세 보고서 저장
    report_file = os.path.join(output_dir, "document_count_analysis.txt")
    save_detailed_report(analysis, report_file)

if __name__ == '__main__':
    main() 
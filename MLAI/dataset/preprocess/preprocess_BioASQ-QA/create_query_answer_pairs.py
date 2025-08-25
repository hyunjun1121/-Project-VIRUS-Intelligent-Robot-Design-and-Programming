#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA 데이터와 Abstract 데이터를 결합하여 Query-Answer 쌍 생성

qa_data와 abstracts 폴더의 파일들을 결합하여
{doc_count}_{id}_query.txt와 {doc_count}_{id}_answer.txt 파일을 생성합니다.
"""

import json
import os
import re
import sys
from typing import Dict, Optional, Tuple

class QueryAnswerGenerator:
    def __init__(self, base_dir: str, json_file: str):
        """
        Query-Answer 생성기 초기화
        
        Args:
            base_dir: 기본 디렉토리 경로
            json_file: BioASQ JSON 파일 경로
        """
        self.base_dir = base_dir
        self.json_file = json_file
        self.qa_data_dir = os.path.join(base_dir, "qa_data")
        self.abstracts_dir = os.path.join(base_dir, "abstracts")
        self.output_dir = os.path.join(base_dir, "test")
        
        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Document 개수 정보 로드
        self.document_counts = self.load_document_counts()
    
    def load_document_counts(self) -> Dict[str, int]:
        """
        JSON 파일에서 각 질문의 document 개수 로드
        
        Returns:
            질문 ID를 키로 하고 document 개수를 값으로 하는 딕셔너리
        """
        print(f"Document 개수 정보 로드 중: {self.json_file}")
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'questions' in data:
                questions = data['questions']
            elif isinstance(data, list):
                questions = data
            else:
                raise ValueError("지원되지 않는 JSON 구조입니다.")
            
            # factoid 타입만 필터링하고 document 개수 추출
            document_counts = {}
            
            for question in questions:
                if question.get('type') == 'factoid':
                    question_id = question.get('id', '')
                    documents = question.get('documents', [])
                    doc_count = len(documents)
                    document_counts[question_id] = doc_count
            
            print(f"Document 개수 정보 로드 완료: {len(document_counts)}개 질문")
            return document_counts
            
        except Exception as e:
            print(f"Document 개수 정보 로드 중 오류: {str(e)}")
            return {}
    
    def extract_id_from_qa_filename(self, filename: str) -> Optional[str]:
        """
        QA 파일명에서 ID 추출
        
        Args:
            filename: QA 파일명 (예: QA_5118dd1305c10fae75000001.txt)
            
        Returns:
            추출된 ID 또는 None
        """
        match = re.match(r'QA_(.+)\.txt$', filename)
        return match.group(1) if match else None
    
    def find_abstract_file(self, question_id: str) -> Optional[str]:
        """
        해당 ID의 abstract 파일 찾기
        
        Args:
            question_id: 질문 ID
            
        Returns:
            abstract 파일 경로 또는 None
        """
        if not os.path.exists(self.abstracts_dir):
            return None
            
        # factoid_{id}.txt 형태로 찾기
        abstract_filename = f"factoid_{question_id}.txt"
        abstract_path = os.path.join(self.abstracts_dir, abstract_filename)
        
        if os.path.exists(abstract_path):
            return abstract_path
        
        # 다른 가능한 형태들도 시도
        possible_patterns = [
            f"type_factoid_{question_id}.txt",
            f"{question_id}_abstract.txt",
            f"{question_id}.txt"
        ]
        
        for pattern in possible_patterns:
            test_path = os.path.join(self.abstracts_dir, pattern)
            if os.path.exists(test_path):
                return test_path
        
        return None
    
    def parse_qa_content(self, qa_content: str) -> Tuple[str, str]:
        """
        QA 파일 내용을 파싱하여 질문과 답변 분리
        
        Args:
            qa_content: QA 파일의 전체 내용
            
        Returns:
            (question, answer_content) 튜플
        """
        lines = qa_content.strip().split('\n')
        
        question = ""
        answer_lines = []
        in_question = False
        in_answer = False
        
        for line in lines:
            if line.startswith("QUESTION:"):
                question = line.replace("QUESTION:", "").strip()
                in_question = True
                in_answer = False
            elif line.startswith("IDEAL_ANSWER:") or line.startswith("EXACT_ANSWER:"):
                in_question = False
                in_answer = True
                answer_lines.append(line)
            elif in_answer and line.strip():
                answer_lines.append(line)
            elif not line.strip() and in_answer:
                answer_lines.append(line)
        
        answer_content = '\n'.join(answer_lines).strip()
        return question, answer_content
    
    def read_abstract_content(self, abstract_path: str) -> str:
        """
        Abstract 파일 내용 읽기
        
        Args:
            abstract_path: abstract 파일 경로
            
        Returns:
            abstract 내용
        """
        try:
            with open(abstract_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Abstract 파일 읽기 오류 ({abstract_path}): {str(e)}")
            return ""
    
    def create_query_file(self, question_id: str, question: str, abstract_content: str, doc_count: int):
        """
        Query 파일 생성
        
        Args:
            question_id: 질문 ID
            question: 질문 내용
            abstract_content: abstract 내용
            doc_count: document 개수
        """
        query_filename = f"{doc_count}_{question_id}_query.txt"
        query_path = os.path.join(self.output_dir, query_filename)
        
        query_content = f"{question}\n\n{abstract_content}"
        
        with open(query_path, 'w', encoding='utf-8') as f:
            f.write(query_content)
    
    def create_answer_file(self, question_id: str, answer_content: str, doc_count: int):
        """
        Answer 파일 생성
        
        Args:
            question_id: 질문 ID
            answer_content: 답변 내용
            doc_count: document 개수
        """
        answer_filename = f"{doc_count}_{question_id}_answer.txt"
        answer_path = os.path.join(self.output_dir, answer_filename)
        
        with open(answer_path, 'w', encoding='utf-8') as f:
            f.write(answer_content)
    
    def process_all_qa_files(self):
        """
        모든 QA 파일을 처리하여 Query-Answer 쌍 생성
        """
        if not os.path.exists(self.qa_data_dir):
            print(f"QA 데이터 디렉토리가 존재하지 않습니다: {self.qa_data_dir}")
            return
        
        qa_files = [f for f in os.listdir(self.qa_data_dir) if f.endswith('.txt')]
        
        print(f"처리할 QA 파일 수: {len(qa_files)}")
        
        success_count = 0
        no_abstract_count = 0
        no_doc_count_count = 0
        error_count = 0
        
        for i, qa_filename in enumerate(qa_files):
            try:
                # ID 추출
                question_id = self.extract_id_from_qa_filename(qa_filename)
                if not question_id:
                    print(f"ID 추출 실패: {qa_filename}")
                    error_count += 1
                    continue
                
                # Document 개수 가져오기
                doc_count = self.document_counts.get(question_id, 0)
                if doc_count == 0:
                    print(f"  경고: Document 개수 정보 없음 - {question_id}")
                    no_doc_count_count += 1
                
                print(f"처리 중 {i+1}/{len(qa_files)}: {question_id} ({doc_count}개 docs)")
                
                # QA 파일 읽기
                qa_path = os.path.join(self.qa_data_dir, qa_filename)
                with open(qa_path, 'r', encoding='utf-8') as f:
                    qa_content = f.read()
                
                # 질문과 답변 분리
                question, answer_content = self.parse_qa_content(qa_content)
                
                # Abstract 파일 찾기
                abstract_path = self.find_abstract_file(question_id)
                if abstract_path:
                    abstract_content = self.read_abstract_content(abstract_path)
                else:
                    print(f"  경고: Abstract 파일을 찾을 수 없음 - {question_id}")
                    abstract_content = "[Abstract를 찾을 수 없습니다]"
                    no_abstract_count += 1
                
                # Query 파일 생성 (document 개수 포함)
                self.create_query_file(question_id, question, abstract_content, doc_count)
                
                # Answer 파일 생성 (document 개수 포함)
                self.create_answer_file(question_id, answer_content, doc_count)
                
                success_count += 1
                
            except Exception as e:
                print(f"파일 처리 중 오류 ({qa_filename}): {str(e)}")
                error_count += 1
        
        print(f"\n=== 처리 완료 ===")
        print(f"성공: {success_count}")
        print(f"Abstract 없음: {no_abstract_count}")
        print(f"Document 개수 정보 없음: {no_doc_count_count}")
        print(f"오류: {error_count}")
        print(f"결과 저장 위치: {self.output_dir}")

def main():
    """메인 함수"""
    base_dir = r"E:\Project\dataset\preprocess\preprocess_BioASQ-QA"
    json_file = r"E:\Project\dataset\BioASQ-QA\training11b.json"
    
    generator = QueryAnswerGenerator(base_dir, json_file)
    
    print("=== Query-Answer 쌍 생성 시작 (Document 개수 포함) ===")
    generator.process_all_qa_files()

if __name__ == '__main__':
    main() 
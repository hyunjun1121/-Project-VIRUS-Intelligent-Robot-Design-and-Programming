#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BioASQ-QA 데이터 전처리 스크립트

factoid 타입 질문에서 abstract와 QA 데이터를 추출하여 저장합니다.
"""

import json
import os
import re
import sys
import time
from typing import List, Dict, Optional
from Bio import Entrez

class BioASQPreprocessor:
    def __init__(self, email: str = 'anonymous@example.com', batch_size: int = 100):
        """
        BioASQ 전처리기 초기화
        
        Args:
            email: NCBI에 제공할 이메일 주소
            batch_size: 한 번에 가져올 논문 수
        """
        Entrez.email = email
        self.batch_size = min(batch_size, 100)  # 안전을 위해 100으로 제한
        
    def load_bioasq_data(self, json_file: str) -> List[Dict]:
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
    
    def extract_pubmed_ids(self, documents: List[str]) -> List[str]:
        """
        documents 리스트에서 PubMed ID 추출
        
        Args:
            documents: PubMed URL 리스트
            
        Returns:
            PubMed ID 리스트
        """
        pubmed_ids = []
        
        for doc_url in documents:
            # http://www.ncbi.nlm.nih.gov/pubmed/28530548 형태에서 ID 추출
            match = re.search(r'/pubmed/(\d+)', doc_url)
            if match:
                pubmed_ids.append(match.group(1))
        
        return pubmed_ids
    
    def fetch_abstracts_batch(self, pubmed_ids: List[str]) -> Dict[str, str]:
        """
        PubMed ID 리스트에서 abstract 배치 추출
        
        Args:
            pubmed_ids: PubMed ID 리스트
            
        Returns:
            {pubmed_id: abstract} 딕셔너리
        """
        if not pubmed_ids:
            return {}
        
        try:
            # NCBI에서 XML 데이터 가져오기
            handle = Entrez.efetch(
                db="pubmed", 
                id=','.join(pubmed_ids),
                rettype="xml", 
                retmode="text", 
                retmax=len(pubmed_ids)
            )
            
            records = Entrez.read(handle)
            handle.close()
            
            abstracts = {}
            
            # XML에서 abstract 추출
            for pubmed_article in records['PubmedArticle']:
                try:
                    # PubMed ID 추출
                    pmid = str(pubmed_article['MedlineCitation']['PMID'])
                    
                    # Abstract 추출
                    article = pubmed_article['MedlineCitation']['Article']
                    
                    if 'Abstract' in article and 'AbstractText' in article['Abstract']:
                        abstract_text = article['Abstract']['AbstractText']
                        
                        # AbstractText가 리스트인 경우 (여러 섹션이 있는 경우)
                        if isinstance(abstract_text, list):
                            abstract = ' '.join([
                                str(section) if isinstance(section, str) 
                                else section.get('_text', str(section)) if hasattr(section, 'get')
                                else str(section)
                                for section in abstract_text
                            ])
                        else:
                            abstract = str(abstract_text)
                    else:
                        # Abstract가 없으면 제목 사용
                        abstract = str(article.get('ArticleTitle', 'No abstract available'))
                    
                    abstracts[pmid] = abstract.strip()
                    
                except Exception as e:
                    print(f"    개별 논문 처리 중 오류 (PMID: {pmid if 'pmid' in locals() else 'unknown'}): {str(e)}")
                    continue
            
            return abstracts
            
        except Exception as e:
            print(f"    배치 처리 중 오류: {str(e)}")
            return {}
    
    def process_factoid_abstracts(self, factoid_questions: List[Dict], output_dir: str):
        """
        factoid 타입 질문들의 abstract를 추출하여 저장
        
        Args:
            factoid_questions: factoid 타입 질문 리스트
            output_dir: 출력 디렉토리
        """
        print(f"\n=== Abstract 추출 시작 ===")
        
        # 출력 디렉토리 생성
        abstracts_dir = os.path.join(output_dir, "abstracts")
        os.makedirs(abstracts_dir, exist_ok=True)
        
        for i, question in enumerate(factoid_questions):
            question_id = question.get('id', f'unknown_{i}')
            question_type = question.get('type', 'factoid')
            
            print(f"처리 중 {i+1}/{len(factoid_questions)}: {question_id}")
            
            # documents에서 PubMed ID 추출
            documents = question.get('documents', [])
            pubmed_ids = self.extract_pubmed_ids(documents)
            
            if not pubmed_ids:
                print(f"  PubMed ID가 없습니다. 건너뜁니다.")
                continue
            
            print(f"  PubMed ID {len(pubmed_ids)}개 발견: {pubmed_ids}")
            
            # Abstract 추출
            abstracts = self.fetch_abstracts_batch(pubmed_ids)
            
            if abstracts:
                # Abstract들을 이어붙이기
                combined_abstract = '\n\n'.join([
                    f"[PMID: {pmid}]\n{abstract}" 
                    for pmid, abstract in abstracts.items()
                ])
                
                # 파일로 저장
                filename = f"{question_type}_{question_id}.txt"
                filepath = os.path.join(abstracts_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(combined_abstract)
                
                print(f"  저장 완료: {filename} (abstract {len(abstracts)}개)")
            else:
                print(f"  Abstract 추출 실패")
            
            # NCBI 서버 부하 방지
            time.sleep(0.5)
    
    def process_qa_data(self, factoid_questions: List[Dict], output_dir: str):
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
    
    # 전처리기 생성
    preprocessor = BioASQPreprocessor(email='anonymous@example.com', batch_size=50)
    
    try:
        # 1. JSON 데이터 로드 및 factoid 필터링
        factoid_questions = preprocessor.load_bioasq_data(json_file)
        
        if not factoid_questions:
            print("factoid 타입 질문이 없습니다.")
            return
        
        # 2. Abstract 추출 및 저장
        preprocessor.process_factoid_abstracts(factoid_questions, output_dir)
        
        # 3. QA 데이터 추출 및 저장
        preprocessor.process_qa_data(factoid_questions, output_dir)
        
        print(f"\n=== 전처리 완료 ===")
        print(f"결과 저장 위치: {output_dir}")
        
    except Exception as e:
        print(f"전처리 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
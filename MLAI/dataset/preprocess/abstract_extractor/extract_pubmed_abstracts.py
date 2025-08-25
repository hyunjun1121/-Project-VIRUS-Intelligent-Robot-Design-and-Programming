#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PubMed Abstract 추출기

PubMed ID 리스트를 입력받거나 키워드로 검색하여 해당 논문들의 abstract를 추출하고 
TSV 파일로 저장하는 스크립트입니다.

사용법:
    # PubMed ID 파일로부터 추출
    python extract_pubmed_abstracts.py pubmed_ids.txt
    
    # 키워드로 검색하여 추출
    python extract_pubmed_abstracts.py --search "diabetes mellitus" --max-results 1000
    python extract_pubmed_abstracts.py --search "COVID-19 treatment" --max-results 500 --output covid_abstracts.tsv
"""

from Bio import Entrez
import sys
import csv
import argparse
import time
import os
from typing import List, Dict, Optional

class PubMedAbstractExtractor:
    def __init__(self, email: str = 'anonymous@example.com', batch_size: int = 1000):
        """
        PubMed Abstract 추출기 초기화
        
        Args:
            email: NCBI에 제공할 이메일 주소
            batch_size: 한 번에 가져올 논문 수 (최대 1000)
        """
        Entrez.email = email
        self.batch_size = min(batch_size, 1000)  # NCBI 제한에 따라 최대 1000
    
    def search_pubmed(self, search_term: str, max_results: int = 1000, 
                     date_range: Optional[str] = None) -> List[str]:
        """
        키워드로 PubMed를 검색하여 관련 논문의 ID를 추출
        
        Args:
            search_term: 검색할 키워드 (예: "diabetes mellitus", "COVID-19 treatment")
            max_results: 최대 결과 수
            date_range: 날짜 범위 (예: "2020/01/01:2024/12/31")
            
        Returns:
            검색된 PubMed ID 리스트
        """
        print(f"키워드 '{search_term}'로 PubMed 검색 중...")
        print(f"최대 결과 수: {max_results}")
        if date_range:
            print(f"날짜 범위: {date_range}")
        
        try:
            # 검색 쿼리 구성
            search_query = search_term
            
            # 날짜 범위가 지정된 경우 추가
            if date_range:
                search_query += f" AND {date_range}[pdat]"
            
            # PubMed 검색 실행
            handle = Entrez.esearch(
                db="pubmed",
                term=search_query,
                retmax=max_results,
                sort="relevance"  # 관련성 순으로 정렬
            )
            
            search_results = Entrez.read(handle)
            handle.close()
            
            # 검색된 ID 리스트 추출
            pub_ids = search_results['IdList']  # type: ignore
            
            print(f"검색 완료: {len(pub_ids)}개의 논문을 찾았습니다.")
            return pub_ids
            
        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")
            return []
    
    def get_search_info(self, search_term: str) -> Dict:
        """
        검색 결과의 기본 정보를 가져옴
        
        Args:
            search_term: 검색할 키워드
            
        Returns:
            검색 결과 정보 딕셔너리
        """
        try:
            handle = Entrez.esearch(
                db="pubmed",
                term=search_term,
                retmax=0  # 개수만 확인
            )
            
            search_results = Entrez.read(handle)
            handle.close()
            
            return {
                'total_count': int(search_results['Count']),  # type: ignore
                'search_term': search_term
            }
            
        except Exception as e:
            print(f"검색 정보 조회 중 오류: {str(e)}")
            return {'total_count': 0, 'search_term': search_term}
        
    def fetch_abstracts(self, pub_ids: List[str], output_file: str = 'abstracts.tsv') -> Dict[str, str]:
        """
        PubMed ID 리스트에서 abstract를 추출하고 파일로 저장
        
        Args:
            pub_ids: PubMed ID 리스트
            output_file: 결과를 저장할 파일명
            
        Returns:
            추출된 abstract 딕셔너리 {pub_id: abstract}
        """
        abstract_dict = {}
        failed_ids = []
        
        # 기존 파일이 있으면 삭제
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print(f"총 {len(pub_ids)}개의 PubMed ID에서 abstract를 추출합니다.")
        print(f"배치 크기: {self.batch_size}")
        print(f"결과 파일: {output_file}")
        
        # 배치 단위로 처리
        for i in range(0, len(pub_ids), self.batch_size):
            j = min(i + self.batch_size, len(pub_ids))
            batch_ids = pub_ids[i:j]
            
            print(f"배치 {i//self.batch_size + 1}: {i+1}-{j}번째 논문 처리 중...")
            
            try:
                # NCBI에서 데이터 가져오기
                batch_abstracts = self._fetch_batch(batch_ids)
                abstract_dict.update(batch_abstracts)
                
                # 파일에 저장
                self._save_batch_to_file(batch_abstracts, output_file, is_first_batch=(i == 0))
                
                print(f"  성공: {len(batch_abstracts)}개 논문 처리 완료")
                
            except Exception as e:
                print(f"  오류 발생: {str(e)}")
                failed_ids.extend(batch_ids)
                continue
            
            # NCBI 서버 부하 방지를 위한 대기
            time.sleep(0.5)
        
        # 결과 요약
        print(f"\n=== 추출 완료 ===")
        print(f"총 처리된 논문: {len(abstract_dict)}개")
        print(f"실패한 논문: {len(failed_ids)}개")
        
        if failed_ids:
            print(f"실패한 PubMed ID들: {failed_ids[:10]}{'...' if len(failed_ids) > 10 else ''}")
            
        return abstract_dict
    
    def _fetch_batch(self, batch_ids: List[str]) -> Dict[str, str]:
        """
        한 배치의 PubMed ID에서 abstract 추출
        
        Args:
            batch_ids: 배치 PubMed ID 리스트
            
        Returns:
            추출된 abstract 딕셔너리
        """
        try:
            # PubMed에서 XML 데이터 가져오기
            handle = Entrez.efetch(
                db="pubmed", 
                id=','.join(batch_ids),
                rettype="xml", 
                retmode="text", 
                retmax=self.batch_size
            )
            
            records = Entrez.read(handle)
            handle.close()
            
            batch_abstracts = {}
            
            # XML에서 abstract 추출
            for idx, pubmed_article in enumerate(records['PubmedArticle']):
                try:
                    # PubMed ID 추출
                    pmid = str(pubmed_article['MedlineCitation']['PMID'])
                    
                    # Abstract 추출
                    article = pubmed_article['MedlineCitation']['Article']
                    
                    if 'Abstract' in article and 'AbstractText' in article['Abstract']:
                        abstract_text = article['Abstract']['AbstractText']
                        
                        # AbstractText가 리스트인 경우 (여러 섹션이 있는 경우)
                        if isinstance(abstract_text, list):
                            # 각 섹션을 합쳐서 하나의 텍스트로 만들기
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
                    
                    batch_abstracts[pmid] = abstract.strip()
                    
                except Exception as e:
                    print(f"    개별 논문 처리 중 오류 (인덱스 {idx}): {str(e)}")
                    continue
            
            return batch_abstracts
            
        except Exception as e:
            print(f"    배치 처리 중 오류: {str(e)}")
            raise
    
    def _save_batch_to_file(self, batch_abstracts: Dict[str, str], output_file: str, is_first_batch: bool = False):
        """
        배치 결과를 TSV 파일에 저장
        
        Args:
            batch_abstracts: 저장할 abstract 딕셔너리
            output_file: 출력 파일명
            is_first_batch: 첫 번째 배치인지 여부 (헤더 작성용)
        """
        mode = 'w' if is_first_batch else 'a'
        
        with open(output_file, mode, newline='', encoding='utf-8') as csvfile:
            fieldnames = ['pub_id', 'abstract']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
            
            if is_first_batch:
                writer.writeheader()
            
            for pub_id, abstract in batch_abstracts.items():
                writer.writerow({'pub_id': pub_id, 'abstract': abstract})

def load_pubmed_ids(filename: str) -> List[str]:
    """
    파일에서 PubMed ID 리스트를 로드
    
    Args:
        filename: PubMed ID가 저장된 파일명 (한 줄에 하나씩)
        
    Returns:
        PubMed ID 리스트
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            pub_ids = [line.strip() for line in f if line.strip()]
        
        print(f"파일에서 {len(pub_ids)}개의 PubMed ID를 로드했습니다.")
        return pub_ids
        
    except FileNotFoundError:
        print(f"오류: 파일 '{filename}'를 찾을 수 없습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"파일 로드 중 오류: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="PubMed에서 키워드 검색 또는 ID 파일로부터 abstract를 추출하여 TSV 파일로 저장",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # PubMed ID 파일로부터 추출
  python extract_pubmed_abstracts.py pubmed_ids.txt
  
  # 키워드로 검색하여 추출
  python extract_pubmed_abstracts.py --search "diabetes mellitus" --max-results 1000
  python extract_pubmed_abstracts.py --search "COVID-19 treatment" --max-results 500 --output covid_abstracts.tsv
  
  # 날짜 범위를 지정하여 검색
  python extract_pubmed_abstracts.py --search "alzheimer disease" --max-results 1000 --date-range "2020/01/01:2024/12/31"
  
  # 복합 검색어 사용
  python extract_pubmed_abstracts.py --search "machine learning AND medical diagnosis" --max-results 500
        """
    )
    
    # 입력 방식 선택 (파일 또는 검색)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('input_file', nargs='?', 
                           help='PubMed ID가 저장된 텍스트 파일 (한 줄에 하나씩)')
    input_group.add_argument('--search', '-s', 
                           help='PubMed에서 검색할 키워드')
    
    # 검색 관련 옵션
    parser.add_argument('--max-results', '-m', type=int, default=1000,
                       help='검색 시 최대 결과 수 (기본값: 1000)')
    parser.add_argument('--date-range', '-d',
                       help='검색 날짜 범위 (형식: YYYY/MM/DD:YYYY/MM/DD, 예: 2020/01/01:2024/12/31)')
    parser.add_argument('--info-only', action='store_true',
                       help='검색 정보만 확인하고 실제 다운로드는 하지 않음')
    
    # 공통 옵션
    parser.add_argument('--output', '-o', default='abstracts.tsv', 
                       help='결과를 저장할 TSV 파일명 (기본값: abstracts.tsv)')
    parser.add_argument('--batch-size', '-b', type=int, default=1000, 
                       help='한 번에 처리할 논문 수 (기본값: 1000, 최대: 1000)')
    parser.add_argument('--email', '-e', default='anonymous@example.com',
                       help='NCBI에 제공할 이메일 주소')
    
    args = parser.parse_args()
    
    # Abstract 추출기 생성
    extractor = PubMedAbstractExtractor(email=args.email, batch_size=args.batch_size)
    
    # 입력 방식에 따라 PubMed ID 획득
    if args.search:
        # 키워드 검색 모드
        if args.info_only:
            # 검색 정보만 확인
            info = extractor.get_search_info(args.search)
            print(f"\n=== 검색 정보 ===")
            print(f"검색어: {info['search_term']}")
            print(f"총 검색 결과: {info['total_count']:,}개")
            print(f"요청한 최대 결과: {args.max_results:,}개")
            return
        
        # 실제 검색 수행
        pub_ids = extractor.search_pubmed(
            search_term=args.search,
            max_results=args.max_results,
            date_range=args.date_range
        )
        
        if not pub_ids:
            print("검색 결과가 없습니다.")
            sys.exit(1)
            
    else:
        # 파일 입력 모드
        pub_ids = load_pubmed_ids(args.input_file)
    
    if not pub_ids:
        print("오류: PubMed ID가 없습니다.")
        sys.exit(1)
    
    # Abstract 추출 실행
    abstract_dict = extractor.fetch_abstracts(pub_ids, args.output)
    
    print(f"\n추출 완료! 결과가 '{args.output}' 파일에 저장되었습니다.")

if __name__ == '__main__':
    main() 
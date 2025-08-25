"""
논문 파싱 모듈
PDF 파일이나 텍스트에서 논문 정보를 추출하는 기능
"""

import re
import PyPDF2
from typing import Dict, Optional, List
import arxiv
import requests
from io import BytesIO


class PaperParser:
    """논문 텍스트 파싱 및 정보 추출 클래스"""
    
    def __init__(self):
        self.arxiv_client = arxiv.Client()
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, str]:
        """PDF 파일에서 텍스트 추출"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
            return self._extract_paper_info(text)
        except Exception as e:
            raise Exception(f"PDF 파싱 오류: {str(e)}")
    
    def parse_text(self, text: str) -> Dict[str, str]:
        """일반 텍스트에서 논문 정보 추출"""
        return self._extract_paper_info(text)
    
    def parse_arxiv(self, arxiv_id: str) -> Dict[str, str]:
        """arXiv ID로부터 논문 정보 가져오기"""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(self.arxiv_client.results(search))
            
            return {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'abstract': paper.summary,
                'arxiv_id': arxiv_id,
                'pdf_url': paper.pdf_url,
                'url': paper.entry_id,
                'published': paper.published.strftime('%Y-%m-%d'),
                'full_text': self._download_and_extract_pdf(paper.pdf_url)
            }
        except Exception as e:
            raise Exception(f"arXiv 논문 가져오기 오류: {str(e)}")
    
    def _extract_paper_info(self, text: str) -> Dict[str, str]:
        """텍스트에서 논문의 핵심 정보 추출"""
        info = {
            'title': self._extract_title(text),
            'authors': self._extract_authors(text),
            'abstract': self._extract_abstract(text),
            'sections': self._extract_sections(text),
            'full_text': text,
            'key_contributions': self._extract_key_contributions(text),
            'results': self._extract_results(text)
        }
        return info
    
    def _extract_title(self, text: str) -> str:
        """제목 추출"""
        lines = text.split('\n')
        # 첫 번째 줄이 제목일 가능성이 높음
        for line in lines[:5]:  # 상위 5줄 내에서 찾기
            line = line.strip()
            if len(line) > 10 and not line.isupper() and line.count(' ') > 1:
                return line
        return lines[0].strip() if lines else "제목을 찾을 수 없음"
    
    def _extract_authors(self, text: str) -> List[str]:
        """저자 추출"""
        author_patterns = [
            r'Authors?[:\s]*(.*?)(?:\n|Abstract)',
            r'by\s+(.*?)(?:\n|Abstract)',
            r'^(.*?)(?:\n.*?(?:Abstract|Introduction))'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                authors_text = match.group(1).strip()
                # 쉼표나 'and'로 구분된 저자들 분리
                authors = re.split(r',|\sand\s', authors_text)
                return [author.strip() for author in authors if author.strip()]
        
        return ["저자 정보를 찾을 수 없음"]
    
    def _extract_abstract(self, text: str) -> str:
        """초록 추출"""
        abstract_match = re.search(
            r'Abstract[:\s]*(.*?)(?:\n\s*\n|Introduction|1\.|Keywords)',
            text, re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            return abstract_match.group(1).strip()
        return "초록을 찾을 수 없음"
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """논문 섹션 추출"""
        sections = {}
        section_patterns = [
            r'(Introduction|서론)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\w+:|$))',
            r'(Method|Methodology|방법론)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\w+:|$))',
            r'(Results?|결과)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\w+:|$))',
            r'(Conclusion|결론)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\w+:|$))'
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_name = match.group(1).lower()
                sections[section_name] = match.group(2).strip()
        
        return sections
    
    def _extract_key_contributions(self, text: str) -> List[str]:
        """주요 기여점 추출"""
        contribution_patterns = [
            r'(?:we propose|we introduce|we present|우리는 제안|우리는 소개)(.*?)(?:\.|;|\n)',
            r'(?:our contribution|main contribution|주요 기여)(.*?)(?:\.|;|\n)',
            r'(?:novelty|novel approach|새로운 접근)(.*?)(?:\.|;|\n)'
        ]
        
        contributions = []
        for pattern in contribution_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            contributions.extend([match.strip() for match in matches])
        
        return contributions[:5]  # 상위 5개만 반환
    
    def _extract_results(self, text: str) -> List[str]:
        """결과 관련 내용 추출"""
        result_patterns = [
            r'(?:achieves?|outperforms?|improves?|달성|향상)(.*?)(?:\.|;|\n)',
            r'(?:SOTA|state-of-the-art|최고 성능)(.*?)(?:\.|;|\n)',
            r'(?:accuracy|F1|BLEU|성능|정확도)(.*?)(?:\.|;|\n)'
        ]
        
        results = []
        for pattern in result_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            results.extend([match.strip() for match in matches])
        
        return results[:5]  # 상위 5개만 반환
    
    def _download_and_extract_pdf(self, pdf_url: str) -> str:
        """PDF URL에서 텍스트 다운로드 및 추출"""
        try:
            response = requests.get(pdf_url)
            pdf_file = BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"PDF 다운로드 오류: {str(e)}"
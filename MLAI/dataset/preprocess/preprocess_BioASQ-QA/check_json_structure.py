#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BioASQ-QA JSON 파일 구조 확인 스크립트
"""

import json
import os

def check_json_structure():
    json_file = r"E:\Project\dataset\BioASQ-QA\training11b.json"
    
    if not os.path.exists(json_file):
        print(f"파일이 존재하지 않습니다: {json_file}")
        return
    
    print(f"JSON 파일 확인 중: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"데이터 타입: {type(data)}")
        
        if isinstance(data, dict):
            print(f"최상위 키들: {list(data.keys())}")
            
            # questions 키가 있는지 확인
            if 'questions' in data:
                questions = data['questions']
                print(f"질문 개수: {len(questions)}")
                
                # 첫 번째 질문 예시 확인
                if questions:
                    first_q = questions[0]
                    print(f"\n첫 번째 질문의 키들: {list(first_q.keys())}")
                    
                    # 각 키의 값 확인
                    for key, value in first_q.items():
                        if key == 'documents':
                            print(f"  {key}: {len(value)}개 문서")
                            if value:
                                print(f"    첫 번째 문서: {value[0]}")
                        elif isinstance(value, list):
                            print(f"  {key}: {len(value)}개 항목 (리스트)")
                        else:
                            print(f"  {key}: {str(value)[:100]}...")
                
                # type이 factoid인 것들 개수 확인
                factoid_count = sum(1 for q in questions if q.get('type') == 'factoid')
                print(f"\n'factoid' 타입 질문 개수: {factoid_count}")
                
                # 다른 타입들도 확인
                types = {}
                for q in questions:
                    q_type = q.get('type', 'unknown')
                    types[q_type] = types.get(q_type, 0) + 1
                
                print(f"질문 타입별 개수: {types}")
                
        elif isinstance(data, list):
            print(f"리스트 길이: {len(data)}")
            if data:
                print(f"첫 번째 항목의 키들: {list(data[0].keys()) if isinstance(data[0], dict) else '딕셔너리가 아님'}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == '__main__':
    check_json_structure() 
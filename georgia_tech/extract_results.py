#!/usr/bin/env python3
"""
DrafterBench 실험 결과 추출 및 엑셀 포맷 변환 스크립트
"""

import os
import re
import json
import pandas as pd
from datetime import datetime

# 엑셀에 기입해야 할 모델명과 API 모델 ID 매핑
MODEL_MAPPING = {
    "deepseek-ai/DeepSeek-V3-0324": "DeepSeek V3 0324",
    "deepseek-ai/DeepSeek-R1-0528": "DeepSeek R1 0528", 
    "togetherai/Qwen/Qwen3-235B-A22B-FP8": "Qwen 3 235B",
    "togetherai/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8": "Qwen 3 235B Instruct",
    "togetherai/Qwen/Qwen3-235B-A22B-Thinking-2507-FP8": "Qwen 3 235B Thinking",
    "google/gemini-2.5-pro-thinking-off": "Gemini 2.5 Pro",
    "google/gemini-2.5-flash-thinking-off": "Gemini 2.5 Flash",
    "xai/grok-4": "Grok 4",
    "togetherai/moonshotai/Kimi-K2-Instruct": "K2"
}

def parse_result_text(content):
    """결과 텍스트에서 점수 추출"""
    scores = {}
    
    # 정규식 패턴들
    patterns = {
        'structured': r'Structured language:\s*([\d.]+)',
        'unstructured': r'Unstructured language:\s*([\d.]+)', 
        'precise': r'Precise detail:\s*([\d.]+)',
        'vague': r'Vague detail:\s*([\d.]+)',
        'complete': r'Complete instruction:\s*([\d.]+)',
        'error': r'Incomplete.*instruction:\s*([\d.]+)',
        'single_object': r'Single object:\s*([\d.]+)',
        'multiple_objects': r'Multiple objects:\s*([\d.]+)',
        'single_operation': r'Single operation:\s*([\d.]+)',
        'multiple_operations': r'Multiple operations:\s*([\d.]+)',
        'average_tasks': r'Average tasks:\s*([\d.]+)',
        'comprehensive': r'Comprehensive rewards:\s*([\d.]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                scores[key] = float(match.group(1))
            except ValueError:
                scores[key] = None
        else:
            scores[key] = None
    
    return scores

def find_latest_results():
    """최신 실험 결과 찾기"""
    results_dir = "results"
    if not os.path.exists(results_dir):
        print("❌ results 디렉토리를 찾을 수 없습니다.")
        return {}
    
    all_results = {}
    
    for model_dir in os.listdir(results_dir):
        model_path = os.path.join(results_dir, model_dir)
        if not os.path.isdir(model_path):
            continue
        
        # txt 파일들 찾기
        txt_files = []
        for file in os.listdir(model_path):
            if file.endswith('.txt'):
                file_path = os.path.join(model_path, file)
                txt_files.append((file, os.path.getmtime(file_path)))
        
        if not txt_files:
            continue
        
        # 가장 최신 파일 선택
        latest_file = max(txt_files, key=lambda x: x[1])[0]
        latest_path = os.path.join(model_path, latest_file)
        
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                content = f.read()
                scores = parse_result_text(content)
                
                # 모델명 정리
                clean_model_name = model_dir.replace('_', '/')
                display_name = MODEL_MAPPING.get(clean_model_name, model_dir)
                
                all_results[display_name] = {
                    'model_id': clean_model_name,
                    'file_path': latest_path,
                    'timestamp': datetime.fromtimestamp(txt_files[-1][1]).isoformat(),
                    'scores': scores
                }
                
        except Exception as e:
            print(f"⚠️  {model_dir} 결과 파싱 실패: {str(e)}")
    
    return all_results

def create_excel_format(results):
    """엑셀 형식으로 데이터 정리"""
    if not results:
        return pd.DataFrame()
    
    # 데이터 정리
    data = []
    for model_name, info in results.items():
        scores = info['scores']
        row = {
            'Model': model_name,
            'Structured Language': scores.get('structured'),
            'Unstructured Language': scores.get('unstructured'), 
            'Precise Detail': scores.get('precise'),
            'Vague Detail': scores.get('vague'),
            'Complete Instruction': scores.get('complete'),
            'Error Instruction': scores.get('error'),
            'Single Object': scores.get('single_object'),
            'Multiple Objects': scores.get('multiple_objects'),
            'Single Operation': scores.get('single_operation'),
            'Multiple Operations': scores.get('multiple_operations'),
            'Average Tasks': scores.get('average_tasks'),
            'Comprehensive Score': scores.get('comprehensive'),
            'Timestamp': info['timestamp']
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    return df

def save_results(results, output_file='drafterbench_results.xlsx'):
    """결과를 엑셀 파일로 저장"""
    df = create_excel_format(results)
    
    if df.empty:
        print("📝 저장할 결과가 없습니다.")
        return
    
    try:
        df.to_excel(output_file, index=False)
        print(f"📊 결과가 저장되었습니다: {output_file}")
        
        # CSV 형태로도 저장
        csv_file = output_file.replace('.xlsx', '.csv')
        df.to_csv(csv_file, index=False)
        print(f"📄 CSV 형태로도 저장: {csv_file}")
        
    except Exception as e:
        print(f"❌ 파일 저장 실패: {str(e)}")
        # CSV로라도 저장 시도
        try:
            csv_file = output_file.replace('.xlsx', '.csv')
            df.to_csv(csv_file, index=False)
            print(f"📄 CSV 형태로 저장됨: {csv_file}")
        except Exception as e2:
            print(f"❌ CSV 저장도 실패: {str(e2)}")

def print_results_summary(results):
    """결과 요약 출력"""
    print(f"\n📊 DrafterBench 결과 요약")
    print(f"{'='*80}")
    print(f"{'Model':<25} {'Comprehensive':<15} {'Avg Tasks':<12} {'Status'}")
    print(f"{'-'*80}")
    
    for model_name, info in sorted(results.items()):
        scores = info['scores']
        comprehensive = scores.get('comprehensive', 0) or 0
        avg_tasks = scores.get('average_tasks', 0) or 0
        
        status = "✅ 완료" if comprehensive > 0 else "❌ 미완료"
        
        print(f"{model_name:<25} {comprehensive:<15.2f} {avg_tasks:<12.2f} {status}")

def main():
    """메인 함수"""
    print("🔍 DrafterBench 결과 추출 중...")
    
    # 결과 찾기
    results = find_latest_results()
    
    if not results:
        print("❌ 추출할 결과가 없습니다.")
        return
    
    print(f"✅ {len(results)}개 모델의 결과를 찾았습니다.")
    
    # 요약 출력
    print_results_summary(results)
    
    # 엑셀 파일로 저장
    save_results(results)
    
    # JSON으로도 저장 (디버깅용)
    with open('drafterbench_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("🔧 디버깅용 JSON 파일도 저장했습니다: drafterbench_results.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedHop 전체 객체 Supports 추출기

JSON 파일의 모든 객체에서 supports 배열을 추출하여 
개별 텍스트 파일로 저장하는 스크립트입니다.
파일명에 객체 ID가 포함됩니다 (예: MH_dev_0_support_001.txt)

사용법:
    python extract_all_objects_supports.py
    python extract_all_objects_supports.py --input dev.json --output ./supports
"""

import json
import os
import argparse
from typing import List, Dict, Tuple
from pathlib import Path

class MedHopSupportsExtractor:
    def __init__(self, output_base_folder: str = "./all_objects_supports"):
        """
        MedHop Supports 추출기 초기화
        
        Args:
            output_base_folder: 기본 출력 폴더 경로
        """
        self.output_base_folder = output_base_folder
        self.total_objects = 0
        self.total_supports = 0
        self.failed_objects = []
        
    def extract_all_supports(self, json_file_paths: List[str], save_mode: str = "flat") -> Dict[str, int]:
        """
        여러 JSON 파일에서 모든 객체의 supports를 추출
        
        Args:
            json_file_paths: JSON 파일 경로 리스트
            save_mode: 저장 방식 ("flat" 기본값 - 모든 파일을 하나의 폴더에 저장)
            
        Returns:
            추출 통계 딕셔너리
        """
        
        print(f"=== MedHop Supports 전체 추출 시작 ===")
        print(f"저장 방식: {save_mode} (파일명에 객체 ID 포함)")
        print(f"출력 폴더: {self.output_base_folder}")
        
        # 출력 폴더 생성
        if not os.path.exists(self.output_base_folder):
            os.makedirs(self.output_base_folder)
            print(f"기본 폴더 생성: {self.output_base_folder}")
        
        stats = {"total_objects": 0, "total_supports": 0, "failed_objects": 0, "processed_files": 0}
        
        for file_path in json_file_paths:
            print(f"\n처리 중: {file_path}")
            file_stats = self._process_single_file(file_path, save_mode)
            
            # 통계 누적
            for key in stats:
                stats[key] += file_stats.get(key, 0)
            
            print(f"  ✅ 파일 처리 완료: {file_stats['total_objects']}개 객체, {file_stats['total_supports']}개 supports")
        
        # 최종 결과 출력
        self._print_summary(stats)
        return stats
    
    def _process_single_file(self, json_file_path: str, save_mode: str) -> Dict[str, int]:
        """
        단일 JSON 파일 처리
        
        Args:
            json_file_path: JSON 파일 경로
            save_mode: 저장 방식
            
        Returns:
            파일 처리 통계
        """
        stats = {"total_objects": 0, "total_supports": 0, "failed_objects": 0, "processed_files": 0}
        
        try:
            # JSON 파일 읽기
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if not isinstance(data, list):
                print(f"  ❌ JSON 파일이 배열 형태가 아닙니다: {json_file_path}")
                return stats
            
            print(f"  총 {len(data)}개 객체 발견")
            
            # 각 객체 처리
            for obj_idx, obj in enumerate(data):
                try:
                    if save_mode == "by_object":
                        obj_stats = self._save_supports_by_object(obj, obj_idx)
                    else:  # flat mode (기본값)
                        obj_stats = self._save_supports_flat(obj, obj_idx, json_file_path)
                    
                    stats["total_objects"] += 1
                    stats["total_supports"] += obj_stats["supports_count"]
                    
                    # 진행 상황 표시 (100개마다)
                    if (obj_idx + 1) % 100 == 0:
                        print(f"    진행: {obj_idx + 1}/{len(data)} 객체 처리됨")
                        
                except Exception as e:
                    print(f"    ⚠️ 객체 {obj_idx} 처리 실패: {e}")
                    stats["failed_objects"] += 1
                    self.failed_objects.append(f"{json_file_path}:객체{obj_idx}")
            
            stats["processed_files"] = 1
            
        except FileNotFoundError:
            print(f"  ❌ 파일을 찾을 수 없습니다: {json_file_path}")
        except json.JSONDecodeError:
            print(f"  ❌ JSON 파일 형식이 올바르지 않습니다: {json_file_path}")
        except Exception as e:
            print(f"  ❌ 파일 처리 중 오류: {e}")
        
        return stats
    
    def _save_supports_by_object(self, obj: Dict, obj_idx: int) -> Dict[str, int]:
        """
        객체별 폴더에 supports 저장
        
        Args:
            obj: JSON 객체
            obj_idx: 객체 인덱스
            
        Returns:
            객체 처리 통계
        """
        stats = {"supports_count": 0}
        
        # 객체 ID 또는 인덱스로 폴더명 생성
        obj_id = obj.get('id', f'object_{obj_idx:05d}')
        obj_folder = os.path.join(self.output_base_folder, f"{obj_id}")
        
        # 객체별 폴더 생성
        if not os.path.exists(obj_folder):
            os.makedirs(obj_folder)
        
        # supports 배열 처리
        if 'supports' in obj and isinstance(obj['supports'], list):
            supports_list = obj['supports']
            
            # 각 support를 개별 파일로 저장
            for support_idx, support_text in enumerate(supports_list):
                filename = f"support_{support_idx+1:03d}.txt"
                filepath = os.path.join(obj_folder, filename)
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(support_text)
                
                stats["supports_count"] += 1
            
            # 객체 메타데이터 저장
            self._save_object_metadata(obj, obj_folder)
        
        return stats
    
    def _save_supports_flat(self, obj: Dict, obj_idx: int, source_file: str) -> Dict[str, int]:
        """
        모든 supports를 하나의 폴더에 평면적으로 저장 (파일명에 객체 ID 포함)
        
        Args:
            obj: JSON 객체
            obj_idx: 객체 인덱스
            source_file: 원본 파일 경로
            
        Returns:
            객체 처리 통계
        """
        stats = {"supports_count": 0}
        
        obj_id = obj.get('id', f'object_{obj_idx:05d}')
        
        # supports 배열 처리
        if 'supports' in obj and isinstance(obj['supports'], list):
            supports_list = obj['supports']
            
            for support_idx, support_text in enumerate(supports_list):
                filename = f"{obj_id}_support_{support_idx+1:03d}.txt"
                filepath = os.path.join(self.output_base_folder, filename)
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(support_text)
                
                stats["supports_count"] += 1
        
        return stats
    
    def _save_object_metadata(self, obj: Dict, obj_folder: str):
        """
        객체의 메타데이터를 별도 파일로 저장
        
        Args:
            obj: JSON 객체
            obj_folder: 객체 폴더 경로
        """
        metadata = {
            "id": obj.get('id', 'N/A'),
            "query": obj.get('query', 'N/A'),
            "answer": obj.get('answer', 'N/A'),
            "candidates_count": len(obj.get('candidates', [])),
            "supports_count": len(obj.get('supports', []))
        }
        
        # candidates도 저장
        if 'candidates' in obj:
            metadata["candidates"] = obj['candidates']
        
        metadata_file = os.path.join(obj_folder, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as file:
            json.dump(metadata, file, indent=2, ensure_ascii=False)
    
    def _print_summary(self, stats: Dict[str, int]):
        """
        최종 처리 결과 요약 출력
        
        Args:
            stats: 처리 통계
        """
        print(f"\n=== 추출 완료 요약 ===")
        print(f"처리된 파일: {stats['processed_files']}개")
        print(f"총 객체 수: {stats['total_objects']}개")
        print(f"총 supports 수: {stats['total_supports']}개")
        print(f"실패한 객체: {stats['failed_objects']}개")
        print(f"평균 supports/객체: {stats['total_supports']/max(stats['total_objects'], 1):.2f}개")
        print(f"저장 위치: {self.output_base_folder}")
        print(f"파일명 형식: [객체ID]_support_[번호].txt (예: MH_dev_0_support_001.txt)")
        
        if self.failed_objects:
            print(f"\n⚠️ 실패한 객체들:")
            for failed in self.failed_objects[:10]:  # 최대 10개만 표시
                print(f"  - {failed}")
            if len(self.failed_objects) > 10:
                print(f"  ... 그외 {len(self.failed_objects) - 10}개 더")

def analyze_json_structure(json_file_path: str):
    """
    JSON 파일 구조 분석 및 미리보기
    
    Args:
        json_file_path: JSON 파일 경로
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        if isinstance(data, list) and len(data) > 0:
            print(f"=== {json_file_path} 구조 분석 ===")
            print(f"총 객체 수: {len(data)}개")
            
            # 첫 번째 객체 구조 분석
            first_obj = data[0]
            print(f"\n첫 번째 객체 구조:")
            for key, value in first_obj.items():
                if isinstance(value, list):
                    print(f"  {key}: 배열 (길이: {len(value)})")
                    if key == 'supports' and len(value) > 0:
                        print(f"    첫 번째 support 미리보기: {value[0][:100]}...")
                    elif key == 'candidates' and len(value) > 0:
                        print(f"    candidates: {value}")
                elif isinstance(value, str):
                    print(f"  {key}: \"{value}\"")
                else:
                    print(f"  {key}: {value}")
            
            # 통계 정보
            supports_counts = [len(obj.get('supports', [])) for obj in data]
            print(f"\nSupports 통계:")
            print(f"  평균 supports/객체: {sum(supports_counts)/len(supports_counts):.2f}개")
            print(f"  최소 supports: {min(supports_counts)}개")
            print(f"  최대 supports: {max(supports_counts)}개")
            print(f"  총 supports 수: {sum(supports_counts)}개")
            
        else:
            print("❌ 유효한 데이터를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 분석 중 오류: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="MedHop JSON 파일에서 모든 객체의 supports를 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python extract_all_objects_supports.py
  python extract_all_objects_supports.py --input dev.json train.json
  python extract_all_objects_supports.py --output ./supports_extracted
  python extract_all_objects_supports.py --mode by_object --output ./supports_by_folder
  python extract_all_objects_supports.py --analyze-only
        """
    )
    
    parser.add_argument('--input', '-i', nargs='+', 
                       default=["../medhop/dev.json", "../medhop/train.json"],
                       help='처리할 JSON 파일들 (기본값: dev.json, train.json)')
    parser.add_argument('--output', '-o', default='./all_objects_supports',
                       help='출력 폴더 경로 (기본값: ./all_objects_supports)')
    parser.add_argument('--mode', '-m', choices=['by_object', 'flat'], default='flat',
                       help='저장 방식: flat(평면적, 기본값) 또는 by_object(객체별 폴더)')
    parser.add_argument('--analyze-only', '-a', action='store_true',
                       help='구조 분석만 수행하고 추출은 하지 않음')
    
    args = parser.parse_args()
    
    # 파일 존재 확인
    existing_files = []
    for file_path in args.input:
        if os.path.exists(file_path):
            existing_files.append(file_path)
        else:
            print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
    
    if not existing_files:
        print("❌ 처리할 파일이 없습니다.")
        return
    
    # 구조 분석
    print("=== JSON 파일 구조 분석 ===")
    for file_path in existing_files:
        analyze_json_structure(file_path)
        print()
    
    if args.analyze_only:
        print("분석만 수행했습니다. 추출을 원하시면 --analyze-only 옵션을 제거하세요.")
        return
    
    # Supports 추출 실행
    extractor = MedHopSupportsExtractor(args.output)
    stats = extractor.extract_all_supports(existing_files, args.mode)
    
    print(f"\n🎉 추출 완료! {stats['total_supports']}개의 supports가 추출되었습니다.")

if __name__ == "__main__":
    main() 
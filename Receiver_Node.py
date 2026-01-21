"""
=============================================================================
Receiver_Node.py - 채널 데이터 수신 및 카테고리 분해 노드

역할: 지정된 채널에서 데이터를 수신하고 마스터 컨트롤러 형식으로 변환
특징:
    - 카테고리별 데이터 분해
    - 프로젝트 정보 추출
    - 01~06 폴더 동적 읽기로 아웃풋 자동 관리

작성일: 2024-12-19
버전: 1.2 (07 숫자 제거, 단일 노드 구조 확립)
=============================================================================
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
import hashlib


class ReceiverNode:
    """
    지정된 채널에서 데이터를 수신하고 카테고리별로 분해하는 노드
    
    개선사항:
    - 01~06 폴더명을 동적으로 읽어 아웃풋 소켓 개수 자동 관리
    - 마스터 데이터와 프로젝트 정보만 다룸
    - 스킬 관련 내용 제거 (전담 시스템으로 분리)
    - Project_Master_Controller와 같은 단일 노드 구조
    """
    
    # 노드 정보
    NODE_NAME = "Receiver Node (Channel-based Data Reception)"
    VERSION = "1.2"
    
    # 입력/출력 소켓 정의
    INPUTS = {
        "CHANNEL": "str",           # 수신 채널 이름
        "CATEGORY_FILTER": "int",   # 1~N 필터 (0 = 모두)
    }
    
    def __init__(self):
        """
        초기화 - 자기 완결적 구조
        """
        self.node_dir = Path(__file__).parent
        
        # 캐시 디렉토리 (Communication 폴더에서 이동)
        self.cache_dir = self.node_dir / ".cache" / "channels"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 (내부 정의)
        self.config = {
            "channel_timeout": 30,
            "enable_checksum": True,
            "validate_checksum": True,
            "default_format": "json"
        }
        
        # 카테고리 동적 로드
        self.categories = self._load_categories_dynamically()
        self._generate_outputs()
    
    def _load_categories_dynamically(self) -> Dict[int, str]:
        """
        01~06 폴더를 동적으로 읽어 카테고리 목록 생성
        
        Returns:
            {1: "01_Background", 2: "02_Equipment", ...}
        """
        categories = {}
        
        try:
            # 현재 노드 디렉토리에서 01~06 폴더 찾기
            for i in range(1, 10):  # 최대 9개 (1~9)
                folder_name = f"{i:02d}_*"  # 01_*, 02_*, ...
                
                # 현재 위치에서 폴더 검색
                for item in self.node_dir.iterdir():
                    if item.is_dir() and item.name.startswith(f"{i:02d}_"):
                        categories[i] = item.name
                        break
        except Exception as e:
            print(f"⚠️ 카테고리 동적 로드 실패: {e}")
        
        # 기본값 (실패 시)
        if not categories:
            categories = {
                1: "01_Background",
                2: "02_Equipment",
                3: "03_Character",
                4: "04_Structure",
                5: "05_SpecialEffects",
                6: "06_Audio"
            }
        
        return categories
    
    def _generate_outputs(self):
        """카테고리 개수에 따라 동적 아웃풋 생성"""
        self.OUTPUTS = {}
        
        # 동적 카테고리 아웃풋
        for cat_num in sorted(self.categories.keys()):
            cat_name = self.categories[cat_num].replace("_", " ").split(" ", 1)[1]  # "01_Background" → "Background"
            socket_name = f"{cat_num}_{cat_name.upper()}"
            self.OUTPUTS[socket_name] = "dict"
        
        # 공통 아웃풋
        self.OUTPUTS["PROJECT_INFO"] = "dict"
        self.OUTPUTS["STATUS"] = "str"
        self.OUTPUTS["MESSAGE"] = "str"
    
    def _verify_checksum(self, data: Dict[str, Any], checksum: str) -> Tuple[bool, str]:
        """체크섬 검증"""
        if not self.config.get("validate_checksum", True):
            return True, "체크섬 검증 비활성화"
        
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        calculated = hashlib.sha256(json_str.encode()).hexdigest()
        
        if calculated == checksum:
            return True, f"✅ 체크섬 일치"
        else:
            return False, f"❌ 체크섬 불일치"
    
    def _load_from_cache(self, channel: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """캐시에서 데이터 로드"""
        try:
            channel_safe = channel.replace("/", "_").replace("\\", "_")
            cache_file = self.cache_dir / f"{channel_safe}_latest.json"
            
            if not cache_file.exists():
                return False, f"❌ 채널 '{channel}'에 데이터가 없습니다", None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                packed_data = json.load(f)
            
            return True, f"✅ 캐시에서 로드 완료", packed_data
            
        except Exception as e:
            return False, f"❌ 캐시 로드 실패: {e}", None
    
    def validate_inputs(self, channel: str, category_filter: int) -> Tuple[bool, str]:
        """입력 데이터 검증"""
        if not isinstance(channel, str) or not channel.strip():
            return False, "❌ CHANNEL은 비어있지 않은 문자열이어야 합니다"
        
        if not isinstance(category_filter, int):
            return False, "❌ CATEGORY_FILTER는 정수여야 합니다"
        
        max_cat = max(self.categories.keys())
        if not (0 <= category_filter <= max_cat):
            return False, f"❌ CATEGORY_FILTER는 0~{max_cat} 범위여야 합니다"
        
        return True, "✅ 입력 검증 완료"
    
    def _unpack_data(self, packed_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """데이터 언팩"""
        try:
            metadata = packed_data.get("metadata", {})
            payload = packed_data.get("payload")
            
            if not payload:
                return False, "❌ 페이로드가 없습니다", None
            
            # 체크섬 검증
            if self.config.get("enable_checksum", True):
                checksum = metadata.get("checksum", "")
                is_valid, msg = self._verify_checksum(payload, checksum)
                print(f"   {msg}")
                if not is_valid:
                    return False, msg, None
            
            return True, "✅ 언팩 완료", payload
            
        except Exception as e:
            return False, f"❌ 언팩 실패: {e}", None
    
    def _extract_project_info(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """마스터 데이터에서 프로젝트 정보 추출"""
        project_info = master_data.get("project_info", {})
        return {
            "name": project_info.get("name", "Unknown"),
            "asset_path": project_info.get("asset_path", ""),
            "description": project_info.get("description", ""),
            "version": project_info.get("version", "1.0"),
            "timestamp": int(datetime.now().timestamp())
        }
    
    def _extract_categories(self, master_data: Dict[str, Any], category_filter: int) -> Dict[int, Dict[str, Any]]:
        """마스터 데이터에서 카테고리별 데이터 추출"""
        categories_data = master_data.get("categories", {})
        extracted = {}
        
        # 추출할 카테고리 결정
        if category_filter == 0:
            categories_to_extract = list(self.categories.keys())
        else:
            categories_to_extract = [category_filter] if category_filter in self.categories else []
        
        # 카테고리별 데이터 추출
        for cat_num in categories_to_extract:
            cat_key = self.categories.get(cat_num, f"{cat_num}_Unknown")
            extracted[cat_num] = categories_data.get(cat_key, {})
        
        return extracted
    
    def execute(self, CHANNEL: str, CATEGORY_FILTER: int = 0) -> Dict[str, Any]:
        """노드 실행"""
        print(f"\n{'='*70}")
        print(f"🟢 수신 노드 실행 (Receiver Node v{self.VERSION})")
        print(f"{'='*70}")
        
        # 1. 입력 검증
        print("\n1️⃣ 입력 데이터 검증")
        is_valid, msg = self.validate_inputs(CHANNEL, CATEGORY_FILTER)
        print(f"   {msg}")
        
        if not is_valid:
            return self._create_error_output(msg)
        
        # 2. 캐시에서 데이터 로드
        print("\n2️⃣ 채널에서 데이터 수신")
        load_ok, load_msg, packed_data = self._load_from_cache(CHANNEL)
        print(f"   {load_msg}")
        
        if not load_ok:
            return self._create_error_output(load_msg)
        
        # 3. 데이터 언팩
        print("\n3️⃣ 데이터 언팩 및 검증")
        unpack_ok, unpack_msg, master_data = self._unpack_data(packed_data)
        print(f"   {unpack_msg}")
        
        if not unpack_ok:
            return self._create_error_output(unpack_msg)
        
        # 4. 프로젝트 정보 추출
        print("\n4️⃣ 프로젝트 정보 추출")
        project_info = self._extract_project_info(master_data)
        print(f"   ✅ 프로젝트: {project_info['name']}")
        print(f"   ✅ 에셋 경로: {project_info['asset_path']}")
        
        # 5. 카테고리 분해
        print("\n5️⃣ 카테고리 데이터 분해")
        categories = self._extract_categories(master_data, CATEGORY_FILTER)
        
        if CATEGORY_FILTER == 0:
            print(f"   ✅ 전체 카테고리 ({len(self.categories)}개) 추출")
        else:
            print(f"   ✅ 카테고리 {CATEGORY_FILTER} 추출")
        
        # 6. 출력 구성
        print("\n6️⃣ 출력 구성")
        result = {"PROJECT_INFO": project_info}
        
        # 동적 카테고리 추출
        for cat_num in sorted(self.categories.keys()):
            socket_name = f"{cat_num}_{self.categories[cat_num].replace('_', ' ').split(' ', 1)[1].upper()}"
            result[socket_name] = categories.get(cat_num, {})
        
        result["STATUS"] = "SUCCESS"
        result["MESSAGE"] = f"✅ 채널 '{CHANNEL}'에서 데이터 수신 완료 ({len(categories)} 카테고리)"
        
        print(f"   ✅ 출력 구성 완료 ({len(categories)}개 카테고리 + 프로젝트 정보)")
        
        print(f"\n{'='*70}\n")
        
        return result
    
    def _create_error_output(self, message: str) -> Dict[str, Any]:
        """에러 출력 생성"""
        result = {"PROJECT_INFO": {}}
        
        # 모든 카테고리 소켓에 빈 딕셔너리
        for cat_num in self.categories.keys():
            socket_name = f"{cat_num}_{self.categories[cat_num].replace('_', ' ').split(' ', 1)[1].upper()}"
            result[socket_name] = {}
        
        result["STATUS"] = "FAILED"
        result["MESSAGE"] = message
        
        return result


# ComfyUI 호환성을 위한 NODE_CLASS_MAPPINGS
NODE_CLASS_MAPPINGS = {
    "Receiver_Node": ReceiverNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Receiver_Node": "🟢 Receiver Node (Channel-based Reception v1.2)"
}

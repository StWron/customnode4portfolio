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
from pathlib import Path
from . import global_channels # Import the global channel mechanism
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List


class ReceiverNode:
    # 노드 정보
    NODE_NAME = "Receiver Node (Channel-based Data Reception)"
    def validate_inputs(self, channel: str, category_filter: int) -> Tuple[bool, str]:
        """입력 데이터 검증"""
        if not isinstance(channel, str) or not channel.strip():
            return False, "❌ CHANNEL은 비어있지 않은 문자열이어야 합니다"
        
        if not isinstance(category_filter, int):
            return False, "❌ CATEGORY_FILTER는 정수여야 합니다"
        
        max_cat = max(self.categories.keys()) # self.categories는 __init__에서 초기화됨
        if not (0 <= category_filter <= max_cat):
            return False, f"❌ CATEGORY_FILTER는 0~{max_cat} 범위여야 합니다"
        
        return True, "✅ 입력 검증 완료"
    VERSION = "1.2"
    FUNCTION = "execute"
    CATEGORY = "Universal_Pipeline/Distributed_Control"


    @staticmethod
    def _get_dynamic_categories_static() -> Dict[int, str]:
        """
        01~06 폴더를 동적으로 읽어 카테고리 목록 생성 (정적 메서드)
        INPUT_TYPES, RETURN_TYPES, RETURN_NAMES 및 __init__에서 사용
        
        Returns:
            {1: "01_Background", 2: "02_Equipment", ...}
        """
        categories = {}
        
        try:
            node_dir = Path(__file__).parent
            for i in range(1, 10): # Assuming max 9 categories for now (01_ to 09_)
                folder_prefix = f"{i:02d}_"
                found_category_for_i = False
                for item in node_dir.iterdir():
                    if item.is_dir() and item.name.startswith(folder_prefix):
                        categories[i] = item.name
                        found_category_for_i = True
                        break
                if not found_category_for_i and i > 1:
                    break
        except Exception as e:
            print(f"⚠️ Static category dynamic load failed in ReceiverNode: {e}")
            # Fallback to default if dynamic loading fails or is empty
            pass

        # 기본값 (동적 로드가 실패하거나 아무것도 찾지 못했을 때)
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
    
    @classmethod
    def INPUT_TYPES(s):
        categories = s._get_dynamic_categories_static()
        max_cat = max(categories.keys()) if categories else 6

        return {
            "required": {
                "CHANNEL": ("STRING", {"default": ""}),
                "CATEGORY_FILTER": ("INT", {"default": 0, "min": 0, "max": max_cat, "step": 1}),
                # "PACKED_DATA_INPUT": ("DICT",), # 직접 연결을 위해 필수 입력으로 변경 (이제 글로벌 채널 사용)
            }
        }

    @classmethod
    def RETURN_TYPES(s):
        categories = s._get_dynamic_categories_static()
        return_types = []
        
        # Dynamic category outputs
        for _ in sorted(categories.keys()):
            return_types.append("DICT")
        
        # Common outputs
        return_types.extend(["DICT", "STRING", "STRING"]) # PROJECT_INFO, STATUS, MESSAGE
        return tuple(return_types)

    @classmethod
    def RETURN_NAMES(s):
        categories = s._get_dynamic_categories_static()
        return_names = []
        
        # Dynamic category outputs
        for cat_num in sorted(categories.keys()):
            cat_name = categories[cat_num].replace("_", " ").split(" ", 1)[1]
            socket_name = f"{cat_num}_{cat_name.upper()}"
            return_names.append(socket_name)
        
        return_names.extend(["PROJECT_INFO", "STATUS", "MESSAGE"])
        return tuple(return_names)


    def __init__(self):
        self.node_dir = Path(__file__).parent
        self.categories = self._get_dynamic_categories_static() # 정적 메서드 호출로 변경


    def _unpack_data(self, packed_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """데이터 언팩"""
        try:
            metadata = packed_data.get("metadata", {})
            payload = packed_data.get("payload")
            
            if not payload:
                return False, "❌ 페이로드가 없습니다", None
            return True, "✅ 언팩 완료", payload
        except Exception as e:
            return False, f"❌ 언팩 실패: {e}", None
    
    def _extract_project_info(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """마스터 데이터에서 프로젝트 정보 추출"""
        project_info = master_data.get("project_info", {})
        # ProjectMasterController의 project_info 구조에 맞게 수정
        return {
            "name": project_info.get("name", "Unknown"),
            "root": project_info.get("root", ""), # ProjectMasterController에서 "root"로 제공됨
            "version": project_info.get("version", "1.0"),
            "timestamp": int(datetime.now().timestamp())
        }
    
    def _extract_categories(self, master_data: Dict[str, Any], category_filter: int) -> Dict[int, Dict[str, Any]]:
        """마스터 데이터에서 카테고리별 데이터 추출"""
        categories_data = master_data.get("settings", {}) # ProjectMasterController의 출력 구조에 맞게 "settings" 사용
        extracted = {}
        
        # 추출할 카테고리 결정
        if category_filter == 0:
            categories_to_extract = list(self.categories.keys())
        else:
            categories_to_extract = [category_filter] if category_filter in self.categories else []
        
        # 카테고리별 데이터 추출 (예: "01_Background" 키로 접근)
        for cat_num in categories_to_extract:
            cat_key = self.categories.get(cat_num, f"{cat_num}_Unknown")
            extracted[cat_num] = categories_data.get(cat_key, {})
        
        return extracted
    
    def execute(self, CHANNEL: str, CATEGORY_FILTER: int = 0) -> Tuple[Any, ...]:
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
        
        # 2. 글로벌 채널에서 데이터 로드
        print("\n2️⃣ 글로벌 채널에서 데이터 로드")
        packed_data = global_channels.get_channel_data(CHANNEL)
        if packed_data is None:
            return self._create_error_output(f"❌ 채널 '{CHANNEL}'에 데이터가 없습니다. Sender 노드가 실행되었는지 확인하세요.")
        print(f"   ✅ 채널 '{CHANNEL}'에서 데이터 로드 완료")

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
        print(f"   ✅ 에셋 루트: {project_info['root']}") # "asset_path" 대신 "root"로 변경
        
        # 5. 카테고리 분해
        print("\n5️⃣ 카테고리 데이터 분해")
        categories = self._extract_categories(master_data, CATEGORY_FILTER)
        
        if CATEGORY_FILTER == 0:
            print(f"   ✅ 전체 카테고리 ({len(self.categories)}개) 추출")
        else:
            print(f"   ✅ 카테고리 {CATEGORY_FILTER} 추출")
        
        # 6. 출력 구성 및 반환
        print("\n6️⃣ 출력 구성 및 반환")
        output_values = []
        
        # 동적 카테고리 데이터 추가
        for cat_num in sorted(self.categories.keys()):
            output_values.append(categories.get(cat_num, {}))
        
        # 공통 출력 데이터 추가
        output_values.append(project_info) # PROJECT_INFO
        output_values.append("SUCCESS")    # STATUS
        output_values.append(f"✅ 채널 '{CHANNEL}'에서 데이터 수신 완료 ({len(categories)} 카테고리)") # MESSAGE
        
        print(f"   ✅ 출력 구성 완료 ({len(categories)}개 카테고리 + 프로젝트 정보)")
        
        print(f"\n{'='*70}\n")
        
        return tuple(output_values)
    
    def _create_error_output(self, message: str) -> Tuple[Any, ...]:
        """에러 출력 생성"""
        error_output_values = []
        
        # 모든 동적 카테고리 소켓에 빈 딕셔너리 추가
        categories_static = self._get_dynamic_categories_static()
        for _ in sorted(categories_static.keys()):
            error_output_values.append({})
        
        # 공통 출력 데이터 추가
        error_output_values.append({}) # PROJECT_INFO (empty dict)
        error_output_values.append("FAILED") # STATUS
        error_output_values.append(message) # MESSAGE
        
        return tuple(error_output_values)

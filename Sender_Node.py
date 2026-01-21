"""
=============================================================================
Sender_Node.py - 마스터 컨트롤러 데이터 송신 노드

역할: 마스터 컨트롤러에서 생성된 통합 데이터를 지정된 채널로 전송
특징: 
    - 마스터 데이터(project_info + 카테고리) 송신만 담당
    - 자동 체크섬 생성 (SHA256)
    - 캐시 기반 파일 저장
    - 스킬 관련 내용 제거 (전담 시스템으로 분리)

작성일: 2024-12-19
버전: 1.2 (07 숫자 제거, 단일 노드 구조 확립)
=============================================================================
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import hashlib


class SenderNode:
    """
    마스터 컨트롤러의 통합 데이터를 지정 채널로 전송하는 노드
    
    개선사항:
    - 마스터 데이터(project_info + 카테고리)만 다룸
    - 변경 불필요한 안정적인 설계
    - 스킬 관련 내용 제거
    - Project_Master_Controller와 같은 단일 노드 구조
    """
    
    # 노드 정보
    NODE_NAME = "Sender Node (Channel-based Data Transmission)"
    VERSION = "1.2"
    
    # 입력/출력 소켓 정의
    INPUTS = {
        "MASTER_DATA": "dict",      # 마스터 컨트롤러의 통합 데이터
        "CHANNEL": "str",           # 수신처 채널 이름
    }
    
    OUTPUTS = {
        "STATUS": "str",            # "SUCCESS" / "FAILED"
        "MESSAGE": "str",           # 상태 메시지
        "TIMESTAMP": "int",         # 전송 타임스탬프 (Unix time)
        "CHECKSUM": "str",          # 데이터 무결성 검증용 해시
    }
    
    def __init__(self):
        """
        초기화 - 자기 완결적 구조
        """
        self.node_dir = Path(__file__).parent
        
        # 캐시 디렉토리 (Communication 폴더에서 이동)
        self.cache_dir = self.node_dir / ".cache" / "channels"
        self._init_cache_dir()
        
        # 설정 (내부 정의)
        self.config = {
            "channel_timeout": 30,
            "max_payload_size": 104857600,
            "enable_checksum": True,
            "cache_enabled": True,
            "default_format": "json"
        }
    
    def _init_cache_dir(self):
        """캐시 디렉토리 초기화"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """데이터 무결성 검증용 체크섬 생성"""
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def validate_inputs(self, master_data: Dict[str, Any], channel: str) -> Tuple[bool, str]:
        """입력 데이터 검증"""
        # 마스터 데이터 검증
        if not isinstance(master_data, dict):
            return False, "❌ MASTER_DATA는 dict 타입이어야 합니다"
        
        if "project_info" not in master_data:
            return False, "❌ MASTER_DATA에 project_info가 없습니다"
        
        if "categories" not in master_data:
            return False, "❌ MASTER_DATA에 categories가 없습니다"
        
        # 채널 이름 검증
        if not isinstance(channel, str):
            return False, "❌ CHANNEL은 str 타입이어야 합니다"
        
        if not channel.strip():
            return False, "❌ CHANNEL 이름이 비어있습니다"
        
        # 페이로드 크기 검증
        payload_size = len(json.dumps(master_data).encode())
        max_size = self.config.get("max_payload_size", 104857600)
        
        if payload_size > max_size:
            return False, f"❌ 페이로드 크기 초과: {payload_size} > {max_size}"
        
        return True, "✅ 입력 검증 완료"
    
    def _pack_data(self, master_data: Dict[str, Any], channel: str) -> Dict[str, Any]:
        """데이터 패킹 (포장)"""
        timestamp = int(datetime.now().timestamp())
        
        # 체크섬 생성
        checksum = ""
        if self.config.get("enable_checksum", True):
            checksum = self._generate_checksum(master_data)
        
        # 패킹 구조
        packed = {
            "metadata": {
                "channel": channel,
                "sender": f"{self.NODE_NAME} v{self.VERSION}",
                "timestamp": timestamp,
                "format": self.config.get("default_format", "json"),
                "checksum": checksum
            },
            "payload": master_data
        }
        
        return packed
    
    def _save_to_cache(self, channel: str, packed_data: Dict[str, Any]) -> Tuple[bool, str, Path]:
        """데이터를 캐시에 저장 (파일 기반 채널)"""
        if not self.config.get("cache_enabled", True):
            return True, "✅ 캐시 비활성화 (스킵됨)", None
        
        try:
            # 채널별 파일 생성
            channel_safe = channel.replace("/", "_").replace("\\", "_")
            cache_file = self.cache_dir / f"{channel_safe}_latest.json"
            
            # 이전 파일 백업
            if cache_file.exists():
                backup_file = self.cache_dir / f"{channel_safe}_backup.json"
                if backup_file.exists():
                    backup_file.unlink()
                cache_file.rename(backup_file)
            
            # 새 파일 저장
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(packed_data, f, indent=2, ensure_ascii=False)
            
            return True, f"✅ 캐시 저장 완료: {cache_file.name}", cache_file
            
        except Exception as e:
            return False, f"❌ 캐시 저장 실패: {e}", None
    
    def execute(self, MASTER_DATA: Dict[str, Any], CHANNEL: str) -> Dict[str, Any]:
        """노드 실행"""
        print(f"\n{'='*70}")
        print(f"🔴 송신 노드 실행 (Sender Node v{self.VERSION})")
        print(f"{'='*70}")
        
        # 1. 입력 검증
        print("\n1️⃣ 입력 데이터 검증")
        is_valid, msg = self.validate_inputs(MASTER_DATA, CHANNEL)
        print(f"   {msg}")
        
        if not is_valid:
            return {
                "STATUS": "FAILED",
                "MESSAGE": msg,
                "TIMESTAMP": int(datetime.now().timestamp()),
                "CHECKSUM": ""
            }
        
        # 2. 데이터 패킹
        print("\n2️⃣ 데이터 패킹")
        packed_data = self._pack_data(MASTER_DATA, CHANNEL)
        print(f"   ✅ 패킹 완료 (크기: {len(json.dumps(packed_data))} bytes)")
        
        # 3. 데이터 저장 (캐시/파일 기반 채널)
        print("\n3️⃣ 채널 데이터 저장")
        save_ok, save_msg, save_path = self._save_to_cache(CHANNEL, packed_data)
        print(f"   {save_msg}")
        
        if not save_ok:
            return {
                "STATUS": "FAILED",
                "MESSAGE": save_msg,
                "TIMESTAMP": packed_data["metadata"]["timestamp"],
                "CHECKSUM": packed_data["metadata"]["checksum"]
            }
        
        # 4. 완료
        print("\n4️⃣ 송신 완료")
        timestamp = packed_data["metadata"]["timestamp"]
        checksum = packed_data["metadata"]["checksum"]
        
        print(f"   ✅ 채널: {CHANNEL}")
        print(f"   ✅ 타임스탐프: {timestamp}")
        print(f"   ✅ 체크섬: {checksum[:16]}...")
        print(f"   ✅ 프로젝트: {MASTER_DATA.get('project_info', {}).get('name', 'Unknown')}")
        
        print(f"\n{'='*70}\n")
        
        return {
            "STATUS": "SUCCESS",
            "MESSAGE": f"✅ 채널 '{CHANNEL}'으로 데이터 전송 완료",
            "TIMESTAMP": timestamp,
            "CHECKSUM": checksum
        }


# ComfyUI 호환성을 위한 NODE_CLASS_MAPPINGS
NODE_CLASS_MAPPINGS = {
    "Sender_Node": SenderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Sender_Node": "📤 Sender Node (Channel-based Transmission v1.2)"
}

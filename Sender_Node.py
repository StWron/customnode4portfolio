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
    def INPUT_TYPES(s):
        return {
            "required": {
                "MASTER_DATA": ("DICT",),
                "CHANNEL": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT",) # PACKED_DATA는 이제 글로벌 채널로 전송
    RETURN_NAMES = ("STATUS", "MESSAGE", "TIMESTAMP",)
    FUNCTION = "execute"
    CATEGORY = "Universal_Pipeline/Distributed_Control"

    def __init__(self):
        """
        초기화 - 자기 완결적 구조
        """
        self.node_dir = Path(__file__).parent
        self.config = {"channel_timeout": 30, "max_payload_size": 104857600}

    def validate_inputs(self, master_data: Dict[str, Any], channel: str) -> Tuple[bool, str]:
        """입력 데이터 검증"""
        # 마스터 데이터 검증
        if not isinstance(master_data, dict):
            return False, "❌ MASTER_DATA는 dict 타입이어야 합니다"
        if "settings" not in master_data: # ProjectMasterController의 출력 구조에 맞게 "settings"로 변경
            return False, "❌ MASTER_DATA에 settings가 없습니다"
        
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
        packed = {
            "metadata": {
                "channel": channel,
                "sender": f"{self.NODE_NAME} v{self.VERSION}",
                "timestamp": timestamp,
                "format": "json", # default_format config에서 제거했으므로 하드코딩
                "checksum": "" # 직접 연결에서는 체크섬을 사용하지 않음
            },
            "payload": master_data
        }
        return packed
    
    def execute(self, MASTER_DATA: Dict[str, Any], CHANNEL: str) -> Tuple[str, str, int, Dict[str, Any]]:
        """노드 실행"""
        print(f"\n{'='*70}")
        print(f"🔴 송신 노드 실행 (Sender Node v{self.VERSION})") # PACKED_DATA는 빈 딕셔너리
        print(f"{'='*70}")
        
        # 1. 입력 검증
        print("\n1️⃣ 입력 데이터 검증")
        is_valid, msg = self.validate_inputs(MASTER_DATA, CHANNEL)
        print(f"   {msg}")
        
        if not is_valid:
            return ("FAILED", msg, int(datetime.now().timestamp()))
        packed_data = self._pack_data(MASTER_DATA, CHANNEL)
        print(f"   ✅ 패킹 완료 (크기: {len(json.dumps(packed_data))} bytes)")
        
        # 3. 글로벌 채널에 데이터 저장
        print("\n3️⃣ 글로벌 채널에 데이터 저장")
        global_channels.set_channel_data(CHANNEL, packed_data)
        print(f"   ✅ 채널 '{CHANNEL}'에 데이터 저장 완료")

        # 4. 완료
        print("\n4️⃣ 송신 완료")
        timestamp = packed_data["metadata"]["timestamp"]
        print(f"   ✅ 채널: {CHANNEL}")
        print(f"   ✅ 타임스탐프: {timestamp}")
        print(f"   ✅ 프로젝트: {MASTER_DATA.get('project_info', {}).get('name', 'Unknown')}")
        
        print(f"\n{'='*70}\n")

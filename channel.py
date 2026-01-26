import os
import json
import unicodedata

# 파일 내부 전역 변수로 데이터 저장소 구현 (외부 파일 의존성 제거)
INTERNAL_STORAGE = {}

class SenderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "MASTER_DATA": ("DICT",),
                "CHANNEL": ("STRING", {"default": "MASTER_CH"}),
            }
        }

    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("sent_data",)
    FUNCTION = "execute_transmission"
    CATEGORY = "Universal_Pipeline/Distributed_Control"

    def execute_transmission(self, MASTER_DATA, CHANNEL):
        # 전역 변수에 데이터 저장
        INTERNAL_STORAGE[CHANNEL] = MASTER_DATA
        return (MASTER_DATA,)

class ReceiverNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "CHANNEL": ("STRING", {"default": "MASTER_CH"}),
            }
        }

    RETURN_TYPES = ("DICT", "DICT", "DICT", "DICT", "DICT", "DICT", "DICT", "STRING", "STRING")
    RETURN_NAMES = (
        "01_Background", "02_Equipment", "03_Character", 
        "04_Structure", "05_SpecialEffects", "06_Audio",
        "PROJECT_INFO", "PROJECT_NAME", "ASSET_ROOT"
    )
    FUNCTION = "execute_reception"
    CATEGORY = "Universal_Pipeline/Distributed_Control"

    def execute_reception(self, CHANNEL):
        # 전역 변수에서 데이터 로드
        data = INTERNAL_STORAGE.get(CHANNEL)
        
        if not data:
            return ({}, {}, {}, {}, {}, {}, {}, "NONE", "NONE")

        # ProjectMasterController 구조에 따른 데이터 분해
        info = data.get("project_info", {})
        settings = data.get("settings", {})
        
        return (
            settings.get("01_Background", {}),
            settings.get("02_Equipment", {}),
            settings.get("03_Character", {}),
            settings.get("04_Structure", {}),
            settings.get("05_SpecialEffects", {}),
            settings.get("06_Audio", {}),
            info,
            info.get("name", "Unknown"),
            info.get("root", "")
        )

# 노드 매핑 등록
NODE_CLASS_MAPPINGS = {
    "SenderNode": SenderNode,
    "ReceiverNode": ReceiverNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SenderNode": "🔴 Sender Node (Channel-based)",
    "ReceiverNode": "🟢 Receiver Node (Channel-based)"
}
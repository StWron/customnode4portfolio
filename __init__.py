import os
import json
import importlib
import unicodedata

NODE_DIR = os.path.dirname(os.path.realpath(__file__))
CATEGORIES = ["01_Background", "02_Equipment", "03_Character", "04_Structure", "05_SpecialEffects", "06_Audio"]

# 초기 생성용 규격화 데이터
DEFAULT_DATA = {
    "01_Background": {
        "ckpt": {"type": "combo", "value": "ponyDiffusionV6XL_v6StartWithThisOne.safetensors"},
        "prompt": {"type": "string", "value": "score_9, score_8_up, score_7_up, (scenic landscape:1.2), battlefield, fire, cinematic lighting"},
        "ratio": {"type": "combo", "value": "16:9"}
    },
    "02_Equipment": {
        "lora": {"type": "combo", "value": "reij-style01.safetensors"},
        "strength": {"type": "float", "value": 0.8, "min": 0.0, "max": 2.0, "step": 0.01},
        "tags": {"type": "string", "value": "metallic, armor, high detail"}
    },
    "03_Character": {
        "ckpt": {"type": "combo", "value": "ponyDiffusionV6XL_v6StartWithThisOne.safetensors"},
        "prompt": {"type": "string", "value": "score_9, score_8_up, score_7_up, 1girl, warrior, full armor, masterpiece"},
        "denoise": {"type": "float", "value": 0.6, "min": 0.0, "max": 1.0, "step": 0.05}
    },
    "04_Structure": {
        "control_net": {"type": "combo", "value": "diffusion_pytorch_model_promax.safetensors"},
        "mode": {"type": "combo", "value": "standard"},
        "type": {"type": "combo", "value": "openpose"},
        "strength": {"type": "float", "value": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}
    },
    "05_SpecialEffects": {
        "motion": {"type": "combo", "value": "hsxl_temporal_layers.safetensors"},
        "fps": {"type": "int", "value": 12, "min": 1, "max": 60},
        "fx_type": {"type": "combo", "value": "fire"}
    },
    "06_Audio": {
        "model": {"type": "combo", "value": "model.ckpt"},
        "prompt": {"type": "string", "value": "Epic cinematic, [소설 상황 묘사 문단 삽입], 128 BPM"},
        "duration": {"type": "float", "value": 5.0, "min": 0.1, "max": 30.0, "step": 0.1},
        "bpm": {"type": "int", "value": 128, "min": 40, "max": 250}
    }
}

def initialize_modular_infra():
    """물리적 폴더 인식 및 초기 인프라(JSON/Txt) 구축"""
    for cat in CATEGORIES:
        cat_path = os.path.join(NODE_DIR, cat)
        setting_base = os.path.join(cat_path, "setting")
        category_presets = DEFAULT_DATA.get(cat, {})
        
        for key, config_template in category_presets.items():
            preset_folder = os.path.join(setting_base, key)
            if not os.path.exists(preset_folder):
                os.makedirs(preset_folder, exist_ok=True)
                config_file = os.path.join(preset_folder, "config.json")
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump({key: config_template}, f, indent=4)

        order_file = os.path.join(setting_base, "order_list.txt")
        if not os.path.exists(order_file):
            with open(order_file, "w", encoding="utf-8") as f:
                f.write("\n".join(category_presets.keys()))

# 1. 인프라 초기화 실행
initialize_modular_infra()

# 2. ComfyUI 노드 매핑 초기화
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 3. [복문] 각 카테고리 폴더에서 노드 클래스를 동적으로 임포트하여 매핑
for cat in CATEGORIES:
    try:
        # 모듈 경로 예: .01_Background.01_Background_Setting_Node
        module_path = f".{cat}.{cat}_Setting_Node"
        # 클래스 이름 예: BackgroundSettingNode
        class_name = f"{cat.split('_')[1]}SettingNode"
        
        # importlib을 이용한 동적 로드
        module = importlib.import_module(module_path, package=__name__)
        node_class = getattr(module, class_name)
        
        # 매핑 등록
        NODE_CLASS_MAPPINGS[class_name] = node_class
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = f"⚙️ {cat} Setting"
        
    except Exception as e:
        print(f"❌ [Infra] Failed to load {cat}: {e}")

# __init__.py 하단 매핑 부분

try:
    # 통합된 파일에서 두 클래스를 모두 가져옴
    from .Master_Slave import ProjectMasterController, SlaveDistributor
    
    NODE_CLASS_MAPPINGS["ProjectMasterController"] = ProjectMasterController
    NODE_DISPLAY_NAME_MAPPINGS["ProjectMasterController"] = "📁 Project Master Controller (Master)"
    
    NODE_CLASS_MAPPINGS["SlaveDistributor"] = SlaveDistributor
    NODE_DISPLAY_NAME_MAPPINGS["SlaveDistributor"] = "🟢 [SLAVE] Asset Distributor"
    
except Exception as e:
    print(f"❌ [Infra] Failed to load Integrated Master/Slave: {e}")

# 5. 채널 기반 통신 노드 (Sender, Receiver) 추가 등록
try:
    from .Receiver_Node import ReceiverNode
    NODE_CLASS_MAPPINGS["Receiver_Node"] = ReceiverNode
    NODE_DISPLAY_NAME_MAPPINGS["Receiver_Node"] = "🟢 Receiver Node (Channel-based)"
except Exception as e:
    print(f"❌ [Infra] Failed to load Receiver_Node: Receiver_Node.py not found or class missing.")
    pass

try:
    # Sender_Node.py 파일이 제공되지 않았으므로, 일반적인 패턴을 가정하여 추가합니다.
    # 실제 Sender_Node.py 파일의 클래스 이름과 매핑 키에 맞게 수정해야 합니다.
    from .Sender_Node import SenderNode
    NODE_CLASS_MAPPINGS["Sender_Node"] = SenderNode
    NODE_DISPLAY_NAME_MAPPINGS["Sender_Node"] = "🔴 Sender Node (Channel-based)"
except Exception as e:
    print(f"❌ [Infra] Failed to load Sender_Node: Sender_Node.py not found or class missing.")
    pass

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
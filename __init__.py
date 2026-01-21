import os
import json
import importlib
import unicodedata

NODE_DIR = os.path.dirname(os.path.realpath(__file__))
CATEGORIES = ["01_Background", "02_Equipment", "03_Character", "04_Structure", "05_SpecialEffects", "06_Audio"]

# 초기 생성용 규격화 데이터
DEFAULT_DATA = {
    "01_Background": {
        "ckpt": {"type": "combo", "value": "v1-5-pruned-emaonly.safetensors"},
        "prompt": {"type": "string", "value": "scenic landscape"},
        "ratio": {"type": "combo", "value": "16:9"}
    },
    "02_Equipment": {
        "lora": {"type": "combo", "value": "None"},
        "strength": {"type": "float", "value": 0.7, "min": 0.0, "max": 1.0, "step": 0.01},
        "tags": {"type": "string", "value": "metallic"}
    },
    "03_Character": {
        "ckpt": {"type": "combo", "value": "v1-5-pruned-emaonly.safetensors"},
        "prompt": {"type": "string", "value": "1girl, warrior, masterpiece"},
        "denoise": {"type": "float", "value": 0.7, "min": 0.0, "max": 1.0, "step": 0.05}
    },
    "04_Structure": {
        "control_net": {"type": "combo", "value": "none"},
        "type": {"type": "combo", "value": "interior"},
        "strength": {"type": "float", "value": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}
    },
    "05_SpecialEffects": {
        "motion": {"type": "combo", "value": "none"},
        "fps": {"type": "int", "value": 8, "min": 1, "max": 60},
        "fx_type": {"type": "string", "value": "fire"}
    },
    "06_Audio": {
        "model": {"type": "combo", "value": "none"},
        "duration": {"type": "float", "value": 5.0, "min": 0.1, "max": 60.0, "step": 0.1},
        "bpm": {"type": "int", "value": 120, "min": 40, "max": 250}
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

# 4. 프로젝트 마스터 컨트롤러(Archiver) 추가 등록
try:
    from .Project_Master_Controller import ProjectMasterController
    NODE_CLASS_MAPPINGS["ProjectMasterController"] = ProjectMasterController
    NODE_DISPLAY_NAME_MAPPINGS["ProjectMasterController"] = "📁 Project Master Controller"
except ImportError:
    pass

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
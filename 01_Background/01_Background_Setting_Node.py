import os
import json
import unicodedata

class BackgroundSettingNode:
    @classmethod
    def INPUT_TYPES(s):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        scan_path = os.path.join(current_dir, "setting")
        order_file = os.path.join(scan_path, "order_list.txt")
        
        if not os.path.exists(scan_path): os.makedirs(scan_path, exist_ok=True)
        
        # 1. order_list.txt에서 UI 설계도(항목) 확보
        ui_keys = []
        if os.path.exists(order_file):
            with open(order_file, "r", encoding="utf-8") as f:
                ui_keys = [unicodedata.normalize('NFC', l.strip()) for l in f.readlines() if l.strip()]
        
        required_inputs = {"mode": (["Standard", "Variant", "Draft"],)}

        # 2. [복문] 각 항목별 물리 폴더 및 JSON 데이터 대조
        for key in ui_keys:
            param_folder = os.path.join(scan_path, key)
            config_path = os.path.join(param_folder, "config.json")
            
            # 실제 파일/폴더 스캔 (드롭다운 자원 확보)
            sub_items = []
            if os.path.exists(param_folder):
                sub_items = [d for d in os.listdir(param_folder) if not d.endswith('.json') and not d.endswith('.txt')]
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        conf_data = json.load(f).get(key, {})
                    
                    w_type = conf_data.get("type", "combo")
                    val = conf_data.get("value", "none")

                    if w_type == "float":
                        required_inputs[key] = ("FLOAT", {"default": val, "min": conf_data.get("min", 0.0), "max": conf_data.get("max", 1.0), "step": conf_data.get("step", 0.01)})
                    elif w_type == "int":
                        required_inputs[key] = ("INT", {"default": val, "min": conf_data.get("min", 0), "max": conf_data.get("max", 100)})
                    elif w_type == "string":
                        required_inputs[key] = ("STRING", {"default": str(val)})
                    else: 
                        # [복구 핵심] 파일이 있거나 JSON 옵션이 있으면 '드롭다운' 강제 유지
                        options = conf_data.get("options", sub_items)
                        
                        if options:
                            required_inputs[key] = (options,)
                        else:
                            # 아무 자원도 없을 때만 FALLBACK으로 텍스트 입력창 제공
                            required_inputs[key] = ("STRING", {"default": str(val)})
                except:
                    required_inputs[key] = (["config_error"],)
            else:
                # config가 없어도 폴더 내 파일이 있으면 드롭다운 출력
                if sub_items:
                    required_inputs[key] = (sub_items,)
                else:
                    required_inputs[key] = ("STRING", {"default": "none"})

        return {"required": required_inputs}

    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("01_Background",)
    FUNCTION = "load_config"
    CATEGORY = "Universal_Pipeline/Setting"

    def load_config(self, mode, **kwargs):
        return ({"category": self.RETURN_NAMES[0], "mode": mode, "params": kwargs},)
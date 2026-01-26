import os
import json
from datetime import datetime

class ProjectMasterController:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "project_name": ("STRING", {"default": "NOVELPIA_PROJ"}),
                "asset_save_root": ("STRING", {"default": "output/Asset_Library"}),
                "archive_root": ("STRING", {"default": "output/Archive_Data"}),
            },
            "optional": {
                "01_Background": ("DICT",),
                "02_Equipment": ("DICT",),
                "03_Character": ("DICT",),
                "04_Structure": ("DICT",),
                "05_SpecialEffects": ("DICT",),
                "06_Audio": ("DICT",),
            }
        }

    # 무의미한 PATH_PACKAGE를 제거하고 통합된 딕셔너리 하나만 내보냅니다.
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("merged_data",)
    FUNCTION = "execute_management"
    CATEGORY = "Universal_Pipeline/Management"
    
    def execute_management(self, project_name, asset_save_root, archive_root, **kwargs):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        abs_asset_root = os.path.abspath(asset_save_root)
        project_base_path = os.path.join(abs_asset_root, project_name)
        
        # 1. 통합 데이터 패키지 생성 (중복 제거 및 구조화)
        total_package = {
            "project_info": {
                "name": project_name, 
                "root": project_base_path,
                "timestamp": timestamp
            },
            "settings": {k: v for k, v in kwargs.items() if v is not None}
        }

        # 2. 인프라 구축 (에셋 저장 폴더 생성)
        categories = ["01_Background", "02_Equipment", "03_Character", "04_Structure", "05_SpecialEffects", "06_Audio"]
        for cat in categories:
            os.makedirs(os.path.join(project_base_path, cat), exist_ok=True)

        # 3. 아카이브 저장 및 리스트 갱신
        abs_archive_root = os.path.abspath(archive_root)
        arch_dir = os.path.join(abs_archive_root, "archive_dictionary")
        os.makedirs(arch_dir, exist_ok=True)
        
        file_name = f"{timestamp}_{project_name}.json"
        list_file = os.path.join(abs_archive_root, "archiving_list.txt")
        
        with open(list_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] PROJ: {project_name} | FILE: {file_name}\n")

        with open(os.path.join(arch_dir, file_name), "w", encoding="utf-8") as f:
            json.dump(total_package, f, indent=4)

        # 4. 통합 패키지 단일 출력
        return (total_package,)

NODE_CLASS_MAPPINGS = {"ProjectMasterController": ProjectMasterController}
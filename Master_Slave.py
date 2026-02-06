import os
import json
from datetime import datetime

# 파일 내부 전역 버스 (Master와 Slave가 공유)
INTERNAL_PROJECT_BUS = {}

class ProjectMasterController:
    """데이터 생성 및 전역 채널 직접 송신 후 소켓 없이 종료하는 마스터 노드"""
    
    # 연결된 후속 노드가 없어도 실행되도록 설정
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "project_name": ("STRING", {"default": "MASTER_PROJ"}),
                "asset_save_root": ("STRING", {"default": "output/Asset_Library"}),
                "archive_root": ("STRING", {"default": "output/Archive_Data"}),
                "CHANNEL": ("STRING", {"default": "MASTER_CH"}),
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

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "execute_management"
    CATEGORY = "Universal_Pipeline/Management"
    
    def execute_management(self, project_name, asset_save_root, archive_root, CHANNEL, **kwargs):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        abs_asset_root = os.path.abspath(asset_save_root)
        project_base_path = os.path.join(abs_asset_root, project_name)
        
        # 1. 통합 데이터 패키지 생성
        total_package = {
            "project_info": {
                "name": project_name, 
                "root": project_base_path,
                "timestamp": timestamp
            },
            "settings": {k: v for k, v in kwargs.items() if v is not None}
        }

        # 2. 인프라 구축
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

        # 개별 아카이브 JSON 파일 저장
        with open(os.path.join(arch_dir, file_name), "w", encoding="utf-8") as f:
            json.dump(total_package, f, indent=4)

        # 4. 내부 버스에 데이터 등록
        INTERNAL_PROJECT_BUS[CHANNEL] = total_package
        
        return ()

class SlaveDistributor:
    """채널 혹은 아카이브를 참조하여 project_info와 i값을 결합 분배하는 슬레이브 노드"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "CHANNEL": ("STRING", {"default": "MASTER_CH"}),
                "reference_mode": (["Channel", "Archive"], {"default": "Channel"}),
                "archive_file_path": ("STRING", {"default": "output/Archive_Data/archive_dictionary/filename.json"}),
            }
        }

    # 지시사항: 리턴 타입 6개 고정
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "01_Background", "02_Equipment", "03_Character", 
        "04_Structure", "05_SpecialEffects", "06_Audio"
    )
    FUNCTION = "distribute"
    CATEGORY = "Universal_Pipeline/Distributed_Control"

    def distribute(self, CHANNEL, reference_mode, archive_file_path):
        data = None
        
        # 1. 데이터 참조 로직
        if reference_mode == "Archive":
            if os.path.exists(archive_file_path):
                try:
                    with open(archive_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        print(f"📦 [SLAVE] 아카이브 데이터 참조 성공: {archive_file_path}")
                except Exception as e:
                    print(f"❌ [SLAVE] 아카이브 로드 실패: {e}")

        if data is None:
            data = INTERNAL_PROJECT_BUS.get(CHANNEL)
        
        if not data:
            return ({}, {}, {}, {}, {}, {})

        project_info = data.get("project_info", {})
        settings = data.get("settings", {})
        
        category_keys = [
            "01_Background", "02_Equipment", "03_Character", 
            "04_Structure", "05_SpecialEffects", "06_Audio"
        ]
        
        output_list = []
        for i in range(6):
            integrated_dict = project_info.copy()
            key = category_keys[i]
            
            # root 경로를 프로젝트경로/카테고리명으로 업데이트
            if "root" in integrated_dict:
                integrated_dict["root"] = os.path.join(integrated_dict["root"], key)
            
            # 카테고리별 데이터 병합
            category_data = settings.get(key, {})
            if category_data:
                integrated_dict.update(category_data)
            
            # 리스트에 추가
            output_list.append(integrated_dict)
        
        # output_list에 6개의 항목 지정, 차후 동적 참조 추가 예정
        return (
            output_list[0], output_list[1], output_list[2], 
            output_list[3], output_list[4], output_list[5]
        )

NODE_CLASS_MAPPINGS = {
    "ProjectMasterController": ProjectMasterController,
    "SlaveDistributor": SlaveDistributor
}

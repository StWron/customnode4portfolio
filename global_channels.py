import threading
from typing import Dict, Any, Optional

# 이 딕셔너리는 모든 채널의 데이터를 저장합니다.
# Key: channel_name (str)
# Value: packed_data (Dict[str, Any])
GLOBAL_CHANNEL_DATA: Dict[str, Any] = {}

# 전역 채널 데이터에 대한 스레드 안전한 접근을 보장하기 위한 락
GLOBAL_CHANNEL_LOCK = threading.Lock()

def set_channel_data(channel_name: str, data: Dict[str, Any]):
    """주어진 채널에 데이터를 설정합니다."""
    with GLOBAL_CHANNEL_LOCK:
        GLOBAL_CHANNEL_DATA[channel_name] = data

def get_channel_data(channel_name: str) -> Optional[Dict[str, Any]]:
    """주어진 채널에서 데이터를 검색합니다."""
    with GLOBAL_CHANNEL_LOCK:
        return GLOBAL_CHANNEL_DATA.get(channel_name)
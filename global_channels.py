# 글로벌 채널 데이터 저장소
GLOBAL_CHANNELS = {}

def set_channel_data(channel_name, data):
    GLOBAL_CHANNELS[channel_name] = data

def get_channel_data(channel_name):
    return GLOBAL_CHANNELS.get(channel_name)
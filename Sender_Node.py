import os
import json
import unicodedata

from . import global_channels

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
        global_channels.set_channel_data(CHANNEL, MASTER_DATA)
        return (MASTER_DATA,)

NODE_CLASS_MAPPINGS = {"SenderNode": SenderNode}

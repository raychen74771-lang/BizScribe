import os
import re
import time
import json
import httpx
import torch
from funasr import AutoModel
from openai import OpenAI

class DualEngineProvider:
    def __init__(self, deepseek_api_key):
        # 初始化 L0 物理感官 (SenseVoice)
        device_name = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.audio_model = AutoModel(
            model="iic/SenseVoiceSmall", vad_model="fsmn-vad", vad_kwargs={"max_single_segment_time": 30000},
            trust_remote_code=True, device=device_name, disable_update=True, log_level="ERROR"
        )
        # 初始化 L2 大脑 (DeepSeek V3)
        self.client_default = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com", timeout=120.0)
        custom_http_client = httpx.Client(trust_env=False, timeout=120.0)
        self.client_direct = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com", http_client=custom_http_client)

    def transcribe_audio(self, audio_path):
        """L0 物理提取：将音频切片转化为原始高熵文本"""
        res = self.audio_model.generate(input=audio_path, cache={}, language="auto", use_itn=True)
        raw_text = res[0]['text']
        return re.sub(r'<\|.*?\|>', '', raw_text).strip()

    def refine_text(self, raw_text, style_text="", target_lang="简体中文"):
        """L2 契约坍缩：将高熵文本强行转化为四维 JSON 契约"""
        sow_context = style_text if style_text.strip() else "无特定前置约束。"
        
        system_prompt = f"""你是一个冷酷的企业级商业风控官与会议审计员。
你的任务是将这段混沌会议语音记录，坍缩为绝对的强类型 JSON 契约。输出语言必须为【{target_lang}】。
【最高物理指令】：
你必须且只能输出一个合法的 JSON 对象。严禁添加、修改或嵌套任何未给出的字段！
【强制 JSON 模板】 (严格照抄键名，仅填充值):
{{
  "summary": "100字内摘要",
  "decisions": ["决议1", "决议2"],
  "action_items": [{{"owner": "张三", "task": "具体任务", "deadline": "周五下班前"}}],
  "risks": ["违背SOW点1", "合规漏洞2"]
}}

【前置 SOW 约束 / 商业红线】(必须严苛比对，发现违背直接写入risks):
{sow_context}"""

        last_err = ""
        # 冗余路由退火机制
        for mode_name, client in [("System", self.client_default), ("Direct", self.client_direct)]:
            for attempt in range(2):
                try:
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt}, 
                            {"role": "user", "content": f"【混沌会议记录】:\n{raw_text}"}
                        ],
                        temperature=0.0, # 剥夺创造力
                        response_format={"type": "json_object"} # 网关级死锁
                    )
                    return res.choices[0].message.content.strip()
                except Exception as e:
                    last_err = str(e)
                    time.sleep(2)
        raise Exception(f"Network Blocked ({last_err}). Check API status.")
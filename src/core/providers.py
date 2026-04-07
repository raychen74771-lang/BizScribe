import os
import re
import time
import httpx
import torch
from funasr import AutoModel
from openai import OpenAI

class DualEngineProvider:
    def __init__(self, deepseek_api_key):
        device_name = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.audio_model = AutoModel(
            model="iic/SenseVoiceSmall", vad_model="fsmn-vad", vad_kwargs={"max_single_segment_time": 30000},
            trust_remote_code=True, device=device_name, disable_update=True, log_level="ERROR"
        )
        self.client_default = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com", timeout=120.0)
        custom_http_client = httpx.Client(trust_env=False, timeout=120.0)
        self.client_direct = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com", http_client=custom_http_client)

    def transcribe_audio(self, audio_path):
        res = self.audio_model.generate(input=audio_path, cache={}, language="auto", use_itn=True)
        raw_text = res[0]['text']
        return re.sub(r'<\|.*?\|>', '', raw_text).strip()

    def refine_text(self, raw_text, style_text="", target_lang="简体中文"):
        system_prompt = (
            f"You are a ruthless Corporate Project Manager and Risk Analyst.
"
            f"Below is a rough transcription of a business meeting (potentially multi-lingual).
"
            f"Your CORE TASK is to COLLAPSE this chaotic conversation into a strict JSON contract in 【{target_lang}】.

"
            f"RULES:
"
            f"1. OUTPUT FORMAT: You MUST output ONLY valid JSON. No markdown wrappers like ```json, no explanations.
"
            f"2. JSON SCHEMA:
"
            f"{{
"
            f"  \"summary\": \"100字以内的核心商业目标总结\",
"
            f"  \"decisions\": [\"决议事项1\", \"决议事项2\"],
"
            f"  \"action_items\": [\"@责任人: 截止时间 - 具体任务\"],
"
            f"  \"risks\": [\"识别出的合规、预算或推诿风险（若无则填无）\"]
"
            f"}}
"
            f"3. OBJECTIVITY: Filter out all chitchat, emotions, and polite nonsense. Extract ONLY actionable business data."
        )
        
        if style_text:
            system_prompt += (
                "\n\n[STYLE CLONING DIRECTIVE]\n"
                "The following <context> contains past sermons of this speaker.\n"
                "WARNING: The following <context> is the Prior SOW, Contract, or Business Background. Use this to detect if any decisions in the meeting violate these prior rules!\n"
                "CRITICAL: DO NOT hallucinate or mix specific stories, names, or theological arguments from the reference into the current transcription!\n"
                f"<context>\n{style_text[:5000]}\n</context>"
            )
        
        last_err = ""
        for mode_name, client in[("System", self.client_default), ("Direct", self.client_direct)]:
            for attempt in range(2):
                try:
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Rough Text:\n{raw_text}"}],
                        temperature=0.1
                    )
                    return res.choices[0].message.content.strip()
                except Exception as e:
                    last_err = str(e)
                    time.sleep(2)
        raise Exception(f"Network Blocked ({last_err}). Check API status.")

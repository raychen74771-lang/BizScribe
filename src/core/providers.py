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
            f"You are a top-tier theological editor and proofreader.\n"
            f"Below is a rough transcription of a sermon (potentially multi-lingual).\n"
            f"Your CORE TASK is to translate, refine, and format this into publication-ready 【{target_lang}】.\n\n"
            f"RULES:\n"
            f"1. OUTPUT LANGUAGE: The final output MUST be purely in {target_lang}. Do not leave original foreign words unless they are universally accepted theological terms.\n"
            f"2. THEOLOGICAL ACCURACY: Correct any homophone errors or mistranscribed theological terms. Ensure they match the standard Bible translation.\n"
            f"3. PUBLICATION QUALITY: Merge broken sentences, remove spoken redundancies, and ensure logical flow.\n"
            # 🎯 V9.2 柔性约束：禁止脑补小标题，要求自然连贯
            f"4. NATURAL FLOW (NO TAGS): Do NOT add any artificial subtitles, bracketed tags (e.g., 【讲道精编】, 【经文默想】), or paragraph summaries. Just output the continuous sermon text naturally.\n"
            f"5. NO CHITCHAT: Output ONLY the refined text. No explanations."
        )
        
        if style_text:
            system_prompt += (
                "\n\n[STYLE CLONING DIRECTIVE]\n"
                "The following <style_reference> contains past sermons of this speaker.\n"
                "WARNING: You MUST ONLY learn their 'tone, sentence rhythm, and stylistic preferences'.\n"
                "CRITICAL: DO NOT hallucinate or mix specific stories, names, or theological arguments from the reference into the current transcription!\n"
                f"<style_reference>\n{style_text[:5000]}\n</style_reference>"
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

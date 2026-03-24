# test_sensevoice.py
import os
import re
import torch
from funasr import AutoModel

# 确保环境变量找到本地的 ffmpeg
os.environ["PATH"] = os.getcwd() + os.pathsep + os.environ.get("PATH", "")

# 🎯 物理引擎侦测
device_name = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"⚙️ 物理引擎侦测完毕，即将使用: {device_name} 进行计算")

print("🚀 正在加载 VAD 切割器与 SenseVoice 模型 (首次运行会自动下载 VAD 模型，请稍候)...")
# 初始化本地听写大模型（加入了 VAD 防爆存机制）
model = AutoModel(
    model="iic/SenseVoiceSmall",
    vad_model="fsmn-vad",          # 👈 核心修复：引入阿里开源的 VAD 模型，自动切短句
    vad_kwargs={"max_single_segment_time": 30000}, # 👈 强制规定单句最长不超过 30 秒
    trust_remote_code=True,
    device=device_name
)
print("✅ 模型加载完毕！")

def transcribe_local(audio_path):
    print(f"🎙️ 正在转写: {audio_path} (已开启 VAD 自动切句防溢出机制)")
    try:
        # 核心转写逻辑
        res = model.generate(
            input=audio_path,
            cache={},
            language="auto", # 支持中韩英混合识别
            use_itn=True     # 开启逆文本正则化
        )
        
        # 提取文本并清理 SenseVoice 的特殊标签 (如 <|zh|><|NEUTRAL|>)
        raw_text = res[0]['text']
        clean_text = re.sub(r'<\|.*?\|>', '', raw_text).strip()
        
        return clean_text
    except Exception as e:
        return f"❌ 转写失败: {str(e)}"

if __name__ == "__main__":
    test_file = "test_audio.mp3" # 请替换为你的测试音频文件名
    
    if not os.path.exists(test_file):
        print(f"⚠️ 找不到测试文件 {test_file}。请在根目录放一个音频文件用于测试。")
    else:
        result = transcribe_local(test_file)
        print("\n" + "="*40)
        print("🎯 转写结果:")
        print(result)
        print("="*40)
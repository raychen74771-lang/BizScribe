import os
from dotenv import load_dotenv
from src.core.engine import run_pipeline

if __name__ == "__main__":
    print("="*50)
    print("🚀 FlowScribe V7 (双引擎降落版) 启动")
    print("="*50)
    
    # 🎯 核心修复：自动读取根目录的 .env 文件
    load_dotenv()
    
    # 获取 API Key
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        api_key = input("🔑 未在 .env 找到 Key，请手动输入 DeepSeek API Key (sk-...): ").strip()
        
    if not api_key.startswith("sk-"):
        print("❌ API Key 格式错误，请前往 platform.deepseek.com 获取。")
    else:
        run_pipeline(api_key)
import os
import sys
import time

# --- 强行设置代理 (这是关键) ---
PROXY_URL = "http://127.0.0.1:7897"  # 👈 请确认您的端口是 7897
os.environ["http_proxy"] = PROXY_URL
os.environ["https_proxy"] = PROXY_URL
os.environ["all_proxy"] = PROXY_URL

print(f"🔌 正在尝试通过代理 {PROXY_URL} 连接 Google...")

try:
    # 我们用最底层的库来测试，不依赖任何第三方包
    import urllib.request
    
    # 尝试访问 Google
    url = "https://www.google.com"
    req = urllib.request.Request(url)
    
    start_time = time.time()
    with urllib.request.urlopen(req, timeout=5) as response:
        content = response.read(100)
        print(f"✅ 连接成功！(耗时: {time.time() - start_time:.2f}s)")
        print(f"📡 状态码: {response.getcode()}")
        print("🎉 您的代理设置完全正确，Python 可以联网！")
        
except Exception as e:
    print(f"❌ 连接失败: {e}")
    print("\n🔍 故障排查建议：")
    print("1. 请检查您的 VPN 软件是否开启？")
    print(f"2. 请检查 VPN 设置里的 '端口' 真的是 {PROXY_URL.split(':')[-1]} 吗？")
    print("3. 请尝试把 127.0.0.1 换成 localhost 试试。")
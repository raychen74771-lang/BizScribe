# L1 物理操作指令：提取 FlowScribe 核心拓扑代码
import os

# 仅捕获核心引擎、UI入口与配置文件
TARGET_FILES = ['main.py', 'ui_main.py', 'config.yaml']
TARGET_DIRS = ['src']
OUTPUT_FILE = 'core_code_context.txt'

def pack_code():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        # 1. 提取根目录核心文件
        for f in TARGET_FILES:
            if os.path.exists(f):
                out_f.write(f"\n{'='*40}\n[FILE_START]: {f}\n{'='*40}\n")
                with open(f, 'r', encoding='utf-8') as in_f:
                    out_f.write(in_f.read())
                    
        # 2. 遍历提取 src 目录下的所有逻辑组件 (.py, .yaml)
        if os.path.exists('src'):
            for root, _, files in os.walk('src'):
                for file in files:
                    if file.endswith(('.py', '.yaml')):
                        filepath = os.path.join(root, file)
                        out_f.write(f"\n{'='*40}\n[FILE_START]: {filepath}\n{'='*40}\n")
                        with open(filepath, 'r', encoding='utf-8') as in_f:
                            out_f.write(in_f.read())
                            
    print(f"[Logos]: 核心拓扑已坍缩至 {OUTPUT_FILE}，请直接将内容发送给 Virtual CTO Max。")

if __name__ == "__main__":
    pack_code()
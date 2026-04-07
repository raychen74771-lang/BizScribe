import os

# ==========================================
# L1: 基因重组字典 (The Mutation Map)
# 严格按照从长到短、从特异到通用的顺序排列，防止二次污染
# ==========================================
MUTATION_MAP = {
    # 1. 核心代号与版本清洗
    "FlowScribe V9.4": "BizScribe V1.0",
    "FlowScribe V7 (双引擎降落版)": "BizScribe V1.0 (契约坍缩引擎)",
    "FlowScribe V7": "BizScribe V1.0",
    "V9.4": "V1.0",
    "FlowScribe": "BizScribe",
    "flowscribe": "bizscribe",
    "恩流": "商录",
    
    # 2. UI 认知拓扑重构 (UI Logic Shift)
    "讲员风格": "前置SOW约束",
    "专有名词": "商业红线",
    "请在此输入特定的人名、术语，或希望AI总结的特定风格（例如：冷酷、精简）。": "请在此输入商业红线、历史合同约束或前置SOW，AI将在坍缩时进行严苛的风控审计...",
    "开始转录": "启动契约坍缩",
    "音频转写器": "企业级契约坍缩引擎",
    "生成会议摘要": "生成高管战报与契约JSON",
    "转写中": "数据坍缩与审计中",
    "转写完成": "契约坍缩完成",
    "音频处理中": "混沌数据提取中"
}

# ==========================================
# L2: 物理靶向扫描区
# ==========================================
TARGET_EXTENSIONS = ('.py', '.md', '.txt', '.yaml')
EXCLUDE_DIRS = ('venv', 'venv_cpu_build', '__pycache__', '.git', 'workspace', 'output')

def purge_and_mutate():
    print("🚀 启动 BizScribe 基因清洗与 UI 突变协议...\n")
    mutated_files_count = 0
    
    for root, dirs, files in os.walk('.'):
        # 物理隔离黑名单目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if not file.endswith(TARGET_EXTENSIONS) or file == os.path.basename(__file__):
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                # 执行纳米级替换
                for old_str, new_str in MUTATION_MAP.items():
                    content = content.replace(old_str, new_str)
                
                # 如果发生变异，则覆写物理文件
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"🧬 [突变成功] 物理文件已重构: {filepath}")
                    mutated_files_count += 1
            except Exception as e:
                print(f"⚠️ [跳过] 无法读取文件 {filepath}: {e}")

    print(f"\n✅ 基因清洗完成！共重塑了 {mutated_files_count} 个文件的认知拓扑。")
    print("UI 逻辑已从'录音工具'彻底升维至'风控审计气闸'。")

if __name__ == "__main__":
    purge_and_mutate()
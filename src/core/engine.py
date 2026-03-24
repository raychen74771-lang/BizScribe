import os
import json
from glob import glob
from .audio import zero_ram_slice, smart_compress
from .providers import DualEngineProvider

def run_pipeline(api_key, style_file_path=None, target_lang="简体中文", progress_callback=None):
    def emit(msg, pct):
        if progress_callback: progress_callback(msg, pct)

    input_dir, output_dir = "workspace/input", "workspace/output"
    os.makedirs(input_dir, exist_ok=True); os.makedirs(output_dir, exist_ok=True)
    files = glob(os.path.join(input_dir, "*.mp3")) + glob(os.path.join(input_dir, "*.wav")) + glob(os.path.join(input_dir, "*.m4a"))
    if not files: raise Exception("Input folder is empty!" if target_lang != "简体中文" else "没有找到音频文件！")

    style_text = ""
    if style_file_path and os.path.exists(style_file_path):
        try:
            with open(style_file_path, 'r', encoding='utf-8', errors='ignore') as f: style_text = f.read()
            emit("Loaded Style Dictionary..." if target_lang != "简体中文" else "✅ 已成功加载讲员风格...", 0)
        except Exception as e: pass

    provider = DualEngineProvider(api_key)
    all_finals =[]
    total_files = len(files)

    for file_idx, file_path in enumerate(files):
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        work_dir = os.path.join(output_dir, base_name)
        os.makedirs(work_dir, exist_ok=True)
        
        base_pct, file_weight = file_idx / total_files, 1.0 / total_files
        state_file = os.path.join(work_dir, "state.json")
        state = {"sliced": False, "slices":[], "results": {}}
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f: state = json.load(f)

        # 🎯 新增核心逻辑：前置全自动探测与极限瘦身
        if "compressed_file" not in state:
            emit(f"Checking Audio Format ({file_idx+1}/{total_files})..." if target_lang != "简体中文" else f"探测音频是否需要瘦身 ({file_idx+1}/{total_files})...", base_pct + 0.005)
            comp_file, did_compress = smart_compress(file_path, work_dir)
            state["compressed_file"] = comp_file
            state["did_compress"] = did_compress
            with open(state_file, 'w', encoding='utf-8') as f: json.dump(state, f)
        
        # 使用瘦身后的文件进行后续切片
        source_audio = state["compressed_file"]

        emit(f"Parsing Audio ({file_idx+1}/{total_files})..." if target_lang != "简体中文" else f"正在解析/切片音频 ({file_idx+1}/{total_files})...", base_pct + 0.01)
        if not state.get("sliced"):
            state["slices"] = zero_ram_slice(source_audio, os.path.join(work_dir, "slices"))
            state["sliced"] = True
            with open(state_file, 'w', encoding='utf-8') as f: json.dump(state, f)
        
        slices = state["slices"]
        total_slices = len(slices)
        
        for slice_idx, slice_path in enumerate(slices):
            slice_name = os.path.basename(slice_path)
            if slice_name not in state["results"]: state["results"][slice_name] = {"raw": "", "refined": ""}
            
            slice_base_pct = base_pct + 0.05 * file_weight + 0.95 * file_weight * (slice_idx / total_slices)
            if not state["results"][slice_name]["raw"]:
                emit(f"Transcribing ({slice_idx+1}/{total_slices})..." if target_lang != "简体中文" else f"智能转写中 ({slice_idx+1}/{total_slices})...", slice_base_pct)
                state["results"][slice_name]["raw"] = provider.transcribe_audio(slice_path)
                with open(state_file, 'w', encoding='utf-8') as f: json.dump(state, f)
            
            if not state["results"][slice_name]["refined"]:
                emit(f"Refining Text ({slice_idx+1}/{total_slices})..." if target_lang != "简体中文" else f"深度排版中 ({slice_idx+1}/{total_slices})...", slice_base_pct + (0.95 * file_weight / total_slices * 0.4))
                state["results"][slice_name]["refined"] = provider.refine_text(state["results"][slice_name]["raw"], style_text, target_lang)
                with open(state_file, 'w', encoding='utf-8') as f: json.dump(state, f)

        final_md = os.path.join(work_dir, f"{base_name}_Final.md")
        merged_text = [state["results"][os.path.basename(s)]["refined"] for s in slices]
        full_text = "\n\n".join(merged_text)
        with open(final_md, 'w', encoding='utf-8') as f: f.write(f"# {base_name}\n\n{full_text}")
        all_finals.append(f"# {base_name}\n\n{full_text}")

    if all_finals:
        with open(os.path.join(output_dir, "FINAL_BOOK_All.md"), 'w', encoding='utf-8') as f:
            f.write("\n\n---\n\n".join(all_finals))
    emit("Processing Complete!" if target_lang != "简体中文" else "全部处理完成！", 1.0)

import os
import subprocess
import json

def smart_compress(input_path, output_dir):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_file = os.path.join(output_dir, f"{base_name}_瘦身版.mp3")
    
    try:
        cmd =["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", input_path]
        # 🎯 修复 1：强制使用 UTF-8 解码，忽略特殊韩文/乱码错误，防止 Windows GBK 崩溃
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="ignore")
        data = json.loads(result.stdout)
        bitrate = int(data.get('format', {}).get('bit_rate', 0))
        channels = int(data.get('streams',[{}])[0].get('channels', 2))
        
        # 如果码率 <= 48k 且 是单声道 且 已经是 MP3，直接免压缩
        if 0 < bitrate <= 48000 and channels == 1 and input_path.lower().endswith(".mp3"):
            return input_path, False
    except Exception:
        pass 
        
    cmd =[
        "ffmpeg", "-y", "-i", input_path,
        "-c:a", "libmp3lame", "-b:a", "32k", "-ac", "1", "-ar", "22050",
        out_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_file, True

def zero_ram_slice(input_path, output_dir, segment_time=600):
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    clean_name = base_name.replace("_瘦身版", "")
    output_pattern = os.path.join(output_dir, f"{clean_name}_slice_%03d.mp3")
    
    cmd =[
        "ffmpeg", "-y", "-i", input_path,
        "-f", "segment", "-segment_time", str(segment_time)
    ]
    
    # 🎯 修复 2：如果输入已经是 MP3，使用光速物理流拷贝 (-c copy)，不改变码率，拒绝体积膨胀！
    if input_path.lower().endswith(".mp3"):
        cmd.extend(["-c", "copy"])
    else:
        cmd.extend(["-c:a", "libmp3lame", "-b:a", "32k"])
        
    cmd.append(output_pattern)
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    slices =[os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".mp3")]
    return sorted(slices)

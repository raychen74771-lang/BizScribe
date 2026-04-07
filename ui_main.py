import sys
import os

# ==========================================
# 🛡️ 恩流 (FlowScribe) - 工业级防弹启动器 (V9.4)
# ==========================================
# 1. 修复 PyInstaller 无头模式下的 NoneType write 崩溃
class DummyStream:
    def write(self, text): pass
    def flush(self): pass
if sys.stdout is None: sys.stdout = DummyStream()
if sys.stderr is None: sys.stderr = DummyStream()

# 2. 🎯 终极寻址雷达：兼容 PyInstaller 6.x 的 _internal 隐藏目录
if getattr(sys, 'frozen', False):
    # 打包后的 .exe 运行环境，核心依赖在 _MEIPASS 目录
    base_path = sys._MEIPASS
else:
    # 源码运行环境
    base_path = os.path.dirname(os.path.abspath(__file__))

# 强制将 ffmpeg 所在目录推入系统的最高优先级 PATH！
os.environ["PATH"] = base_path + os.pathsep + os.environ.get("PATH", "")

# 3. 网络装甲：免疫系统代理干扰
for k in['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(k, None)
# ==========================================

import shutil
import threading
import customtkinter as ctk
from tkinter import filedialog
from dotenv import load_dotenv, set_key
from src.core.engine import run_pipeline
import glob

I18N = {
    "zh": {
        "title": "BizScribe 商业契约坍缩引擎", "settings": "⚙️ 设置", "style_btn": "⚖️ 前置契约/SOW",
        "drop_text": "请点击下方按钮添加需转译的音频\n(支持格式: .mp3, .wav, .m4a)",
        "add_btn": "➕ 添加本地音频", "files_count": "当前待处理音频: {} 个",
        "target_lang": "输出语言:", "status_wait": "等待开始...",
        "start": "▶️ 启动转换", "clean": "🗑️ 清理所有音频", "open": "📁 查看结果",
        "set_title": "⚙️ 设置", "set_save": "保存并关闭"
    },
    "en": {
        "title": "BizScribe Contract Engine", "settings": "⚙️ Settings", "style_btn": "⚖️ Prior SOW/Context",
        "drop_text": "Click below to add audio files\n(Supported: .mp3, .wav, .m4a)",
        "add_btn": "➕ Add Local Audio", "files_count": "Pending Files: {}",
        "target_lang": "Output:", "status_wait": "Waiting...",
        "start": "▶️ Start Pipeline", "clean": "🗑️ Clean Up", "open": "📁 Open Results",
        "set_title": "⚙️ Settings", "set_save": "Save & Close"
    }
}

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, current_key):
        super().__init__(master)
        self.lang = master.current_lang
        self.title(I18N[self.lang]["set_title"])
        self.geometry("400x150")
        self.attributes("-topmost", True)
        self.grab_set() 
        ctk.CTkLabel(self, text="DeepSeek API Key:").pack(pady=(20, 5))
        self.key_entry = ctk.CTkEntry(self, width=300, show="*")
        self.key_entry.insert(0, current_key)
        self.key_entry.pack(pady=5)
        ctk.CTkButton(self, text=I18N[self.lang]["set_save"], command=self.save_key).pack(pady=10)
        self.master_app = master

    def save_key(self):
        new_key = self.key_entry.get().strip()
        set_key(".env", "DEEPSEEK_API_KEY", new_key)
        os.environ["DEEPSEEK_API_KEY"] = new_key
        self.master_app.api_key = new_key
        self.destroy()

class FlowScribeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "zh"
        self.title("BizScribe Enterprise V1.0")
        self.geometry("620x500") 
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        load_dotenv()
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.style_file_path = None 
        
        self.build_ui()
        self.refresh_file_list()

    def switch_lang(self):
        self.current_lang = "en" if self.current_lang == "zh" else "zh"
        self.refresh_ui_texts()

    def build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        self.title_lbl = ctk.CTkLabel(header_frame, text=I18N[self.current_lang]["title"], font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.pack(side="left")
        
        self.lang_btn = ctk.CTkButton(header_frame, text="中/EN", width=50, fg_color="#555", command=self.switch_lang)
        self.lang_btn.pack(side="right", padx=(10, 0))
        self.set_btn = ctk.CTkButton(header_frame, text=I18N[self.current_lang]["settings"], width=60, command=self.open_settings)
        self.set_btn.pack(side="right", padx=(10, 0))
        self.style_btn = ctk.CTkButton(header_frame, text=I18N[self.current_lang]["style_btn"], width=80, fg_color="#4A4A4A", hover_color="#333333", command=self.add_style_file)
        self.style_btn.pack(side="right")

        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        lang_select_frame = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        lang_select_frame.pack(pady=(10, 0))
        self.target_lbl = ctk.CTkLabel(lang_select_frame, text=I18N[self.current_lang]["target_lang"])
        self.target_lbl.pack(side="left", padx=5)
        self.target_lang_var = ctk.StringVar(value="简体中文")
        self.lang_dropdown = ctk.CTkOptionMenu(lang_select_frame, variable=self.target_lang_var, values=["简体中文", "English", "한국어", "Español"])
        self.lang_dropdown.pack(side="left")

        self.drop_lbl = ctk.CTkLabel(self.file_frame, text=I18N[self.current_lang]["drop_text"], text_color="gray")
        self.drop_lbl.pack(pady=(15, 10))
        self.add_btn = ctk.CTkButton(self.file_frame, text=I18N[self.current_lang]["add_btn"], fg_color="transparent", border_width=1, command=self.add_files)
        self.add_btn.pack(pady=5)
        self.files_lbl = ctk.CTkLabel(self.file_frame, text=I18N[self.current_lang]["files_count"].format(0), font=ctk.CTkFont(weight="bold"))
        self.files_lbl.pack(pady=(10, 10))

        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=5)
        self.status_lbl = ctk.CTkLabel(self.progress_frame, text=I18N[self.current_lang]["status_wait"], text_color="cyan")
        self.status_lbl.pack(anchor="w")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))
        self.start_btn = ctk.CTkButton(btn_frame, text=I18N[self.current_lang]["start"], height=40, command=self.start_pipeline, font=ctk.CTkFont(weight="bold"))
        self.start_btn.pack(side="left", expand=True, padx=5)
        self.clean_btn = ctk.CTkButton(btn_frame, text=I18N[self.current_lang]["clean"], height=40, command=self.cleanup_files, fg_color="#8B0000", hover_color="#5C0000", state="disabled")
        self.clean_btn.pack(side="left", expand=True, padx=5)
        self.open_btn = ctk.CTkButton(btn_frame, text=I18N[self.current_lang]["open"], height=40, command=self.open_output_dir, fg_color="#228B22", hover_color="#006400", state="disabled")
        self.open_btn.pack(side="left", expand=True, padx=5)

    def refresh_ui_texts(self):
        t = I18N[self.current_lang]
        self.title_lbl.configure(text=t["title"])
        self.set_btn.configure(text=t["settings"])
        if not self.style_file_path: self.style_btn.configure(text=t["style_btn"])
        self.drop_lbl.configure(text=t["drop_text"])
        self.add_btn.configure(text=t["add_btn"])
        self.target_lbl.configure(text=t["target_lang"])
        self.start_btn.configure(text=t["start"])
        self.clean_btn.configure(text=t["clean"])
        self.open_btn.configure(text=t["open"])
        self.refresh_file_list()

    def open_settings(self): SettingsDialog(self, self.api_key)

    def add_files(self):
        files = filedialog.askopenfilenames(title="Select Audio", filetypes=[("Audio", "*.mp3 *.wav *.m4a")])
        if files:
            os.makedirs("workspace/input", exist_ok=True)
            for f in files: shutil.copy(f, "workspace/input/")
            self.refresh_file_list()

    def add_style_file(self):
        file_path = filedialog.askopenfilename(title="Select Style File", filetypes=[("Text", "*.txt *.md")])
        if file_path:
            self.style_file_path = file_path
            short_name = os.path.basename(file_path)
            if len(short_name) > 10: short_name = short_name[:8] + "..."
            self.style_btn.configure(text=f"🎭 {short_name}", fg_color="#228B22", hover_color="#006400")

    def refresh_file_list(self):
        os.makedirs("workspace/input", exist_ok=True)
        files = glob.glob("workspace/input/*.mp3") + glob.glob("workspace/input/*.wav") + glob.glob("workspace/input/*.m4a")
        self.files_lbl.configure(text=I18N[self.current_lang]["files_count"].format(len(files)) + "\n" + "\n".join([os.path.basename(f) for f in files[:2]]) + ("..." if len(files)>2 else ""))

    def update_progress(self, msg, pct):
        self.after(0, lambda: self.status_lbl.configure(text=msg))
        self.after(0, lambda: self.progress_bar.set(pct))

    def start_pipeline(self):
        if not self.api_key.startswith("sk-"):
            self.open_settings()
            return
        files = glob.glob("workspace/input/*.mp3") + glob.glob("workspace/input/*.wav") + glob.glob("workspace/input/*.m4a")
        if not files: return

        self.start_btn.configure(state="disabled")
        self.clean_btn.configure(state="disabled")
        self.open_btn.configure(state="disabled")
        self.style_btn.configure(state="disabled") 
        self.update_progress("🚀 Initializing..." if self.current_lang=="en" else "🚀 引擎初始化中...", 0)
        
        thread = threading.Thread(target=self.run_thread)
        thread.daemon = True
        thread.start()

    def run_thread(self):
        try:
            target_lang = self.target_lang_var.get()
            run_pipeline(self.api_key, self.style_file_path, target_lang, progress_callback=self.update_progress)
            self.after(0, lambda: self.clean_btn.configure(state="normal"))
            self.after(0, lambda: self.open_btn.configure(state="normal"))
        except Exception as e:
            self.update_progress(f"❌ Error: {str(e)}", 1)
            self.after(0, lambda: self.progress_bar.configure(progress_color="red"))
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            self.after(0, lambda: self.style_btn.configure(state="normal"))

    def cleanup_files(self):
        self.update_progress("🧹 Cleaning..." if self.current_lang=="en" else "🧹 清理中...", 0)
        input_dir, output_dir = "workspace/input", "workspace/output"
        if os.path.exists(input_dir):
            for f in os.listdir(input_dir): os.remove(os.path.join(input_dir, f))
        if os.path.exists(output_dir):
            for d in os.listdir(output_dir):
                folder_path = os.path.join(output_dir, d)
                if os.path.isdir(folder_path):
                    slices_dir = os.path.join(folder_path, "slices")
                    if os.path.exists(slices_dir): shutil.rmtree(slices_dir)
        self.refresh_file_list()
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=["#3B8ED0", "#1F6AA5"]) 
        self.update_progress("✨ Done!" if self.current_lang=="en" else "✨ 清理完成！", 0)
        self.clean_btn.configure(state="disabled")
        self.style_file_path = None
        self.style_btn.configure(text=I18N[self.current_lang]["style_btn"], fg_color="#4A4A4A", hover_color="#333333")
        
    def open_output_dir(self):
        out_dir = os.path.abspath("workspace/output")
        os.makedirs(out_dir, exist_ok=True)
        os.startfile(out_dir)

if __name__ == "__main__":
    app = FlowScribeApp()
    app.mainloop()

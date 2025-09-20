import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import logging
from urllib.parse import urlparse
import os
from datetime import datetime
import json
import subprocess
import platform

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class VideoMasterProApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoMaster Pro - 专业视频下载大师 v1.0")
        # 增大界面尺寸
        self.root.geometry("1300x950")
        self.root.minsize(1200, 900)
        
        # 苹果风格配色方案
        self.colors = {
            'bg': '#F2F2F7',           # 苹果浅灰背景
            'card_bg': '#FFFFFF',       # 卡片白色背景
            'primary': '#007AFF',       # 苹果蓝
            'secondary': '#34C759',     # 苹果绿
            'accent': '#FF3B30',        # 苹果红
            'text_primary': '#1D1D1F',  # 主要文字
            'text_secondary': '#8E8E93', # 次要文字
            'border': '#C7C7CC',        # 边框颜色
            'hover': '#E5E5EA'          # 悬停颜色
        }
        
        # 设置主窗口背景为苹果风格
        self.root.configure(bg=self.colors['bg'])

        # Center the main window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1300) // 2
        y = (screen_height - 950) // 2
        self.root.geometry(f"1300x950+{x}+{y}")

        # 初始化变量
        self.download_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.download_tasks = []
        self.current_task_index = 0
        self.total_tasks = 0
        self.abort_all_tasks = False
        self.video_info = {}
        self.is_downloading = False
        self.download_threads = {}

        self.setup_logging()
        self.create_widgets()
        self.load_download_history()

        self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()

        self.root.after(100, self.process_results)

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue

            def emit(self, record):
                self.log_queue.put(("info", self.format(record)))

        self.log_handler = QueueHandler(self.result_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)

    def create_card(self, parent, title, icon=""):
        """创建苹果风格的卡片容器"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=0)
        
        # 添加阴影效果（通过多层边框模拟）
        shadow = tk.Frame(parent, bg='#E0E0E0', height=2)
        
        # 标题栏
        title_frame = tk.Frame(card, bg=self.colors['card_bg'], height=50)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text=f"{icon} {title}", bg=self.colors['card_bg'], 
                              fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 14, 'bold'))
        title_label.pack(side=tk.LEFT, padx=25, pady=15)
        
        return card

    def create_widgets(self):
        # 主滚动容器
        main_canvas = tk.Canvas(self.root, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.colors['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 主容器 - 减少左右边距，使内容更居中
        main_container = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=20)

        # URL输入卡片 - 优化内边距
        url_card = self.create_card(main_container, "视频链接", "🔗")
        url_card.pack(fill=tk.X, pady=(0, 15))

        url_frame = tk.Frame(url_card, bg=self.colors['card_bg'])
        url_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(url_frame, text="YouTube 链接:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=0, column=0, sticky=tk.W, pady=6)
        
        self.url_entry = tk.Entry(url_frame, width=55, font=('Microsoft YaHei UI', 12), relief='flat', bd=6)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=6, padx=(12, 8))
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")

        fetch_btn = tk.Button(url_frame, text="📥 获取信息", command=self.fetch_video_info,
                             bg=self.colors['primary'], fg='white', font=('Microsoft YaHei UI', 11, 'bold'),
                             relief='flat', padx=18, pady=8, cursor='hand2')
        fetch_btn.grid(row=0, column=2, padx=12)
        
        # 配置列权重，使输入框可以扩展
        url_frame.grid_columnconfigure(1, weight=1)

        tk.Label(url_frame, text="批量链接 (每行一个):", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=1, column=0, sticky=tk.W, pady=(15, 6))
        
        self.urls_text = scrolledtext.ScrolledText(url_frame, wrap=tk.WORD, height=3, width=55, 
                                                  font=('Microsoft YaHei UI', 11), relief='flat', bd=6)
        self.urls_text.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=(15, 6), padx=(12, 0))

        tk.Label(url_frame, text="代理地址 (可选):", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=2, column=0, sticky=tk.W, pady=(15, 6))
        
        self.proxy_entry = tk.Entry(url_frame, width=55, font=('Microsoft YaHei UI', 12), relief='flat', bd=6)
        self.proxy_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=(15, 6), padx=(12, 0))
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")

        # 保存路径卡片
        path_card = self.create_card(main_container, "保存设置", "📁")
        path_card.pack(fill=tk.X, pady=(0, 15))

        path_frame = tk.Frame(path_card, bg=self.colors['card_bg'])
        path_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(path_frame, text="保存路径:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=0, column=0, sticky=tk.W, pady=6)
        
        self.save_path_var = tk.StringVar(value=os.getcwd())
        path_entry = tk.Entry(path_frame, textvariable=self.save_path_var, width=45, 
                             font=('Microsoft YaHei UI', 12), relief='flat', bd=6)
        path_entry.grid(row=0, column=1, sticky=tk.EW, pady=6, padx=(12, 8))

        browse_btn = tk.Button(path_frame, text="📂 浏览", command=self.browse_save_path,
                              bg=self.colors['secondary'], fg='white', font=('Microsoft YaHei UI', 11, 'bold'),
                              relief='flat', padx=18, pady=8, cursor='hand2')
        browse_btn.grid(row=0, column=2, padx=12)
        
        # 配置列权重
        path_frame.grid_columnconfigure(1, weight=1)

        # 视频信息预览卡片
        info_card = self.create_card(main_container, "视频信息", "ℹ️")
        info_card.pack(fill=tk.X, pady=(0, 15))

        info_frame = tk.Frame(info_card, bg=self.colors['card_bg'])
        info_frame.pack(fill=tk.X, padx=20, pady=15)

        self.title_var = tk.StringVar(value="标题: 等待获取...")
        self.duration_var = tk.StringVar(value="时长: --")
        self.views_var = tk.StringVar(value="观看次数: --")
        self.uploader_var = tk.StringVar(value="上传者: --")

        tk.Label(info_frame, textvariable=self.title_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Label(info_frame, textvariable=self.duration_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_secondary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=1, sticky=tk.W, pady=5, padx=25)
        tk.Label(info_frame, textvariable=self.views_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_secondary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=2, sticky=tk.W, pady=5, padx=25)
        tk.Label(info_frame, textvariable=self.uploader_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_secondary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=3, sticky=tk.W, pady=5, padx=25)

        # 下载选项卡片
        options_card = self.create_card(main_container, "下载选项", "⚙️")
        options_card.pack(fill=tk.X, pady=(0, 15))

        options_frame = tk.Frame(options_card, bg=self.colors['card_bg'])
        options_frame.pack(fill=tk.X, padx=20, pady=15)

        # 第一行：格式选择和基本选项
        tk.Label(options_frame, text="格式:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=0, column=0, sticky=tk.W, pady=8)
        
        self.format_id_var = tk.StringVar(value="bv*+ba/b")
        format_entry = tk.Entry(options_frame, textvariable=self.format_id_var, width=18,
                               font=('Microsoft YaHei UI', 11), relief='flat', bd=5)
        format_entry.grid(row=0, column=1, sticky=tk.W, pady=8, padx=(12, 15))

        query_btn = tk.Button(options_frame, text="🔍 查询格式", command=self.query_formats,
                             bg=self.colors['accent'], fg='white', font=('Microsoft YaHei UI', 11, 'bold'),
                             relief='flat', padx=18, pady=6, cursor='hand2')
        query_btn.grid(row=0, column=2, padx=(0, 20))

        # 字幕选项
        self.subtitle_var = tk.BooleanVar(value=False)
        subtitle_cb = tk.Checkbutton(options_frame, text="📝 下载字幕", variable=self.subtitle_var,
                                   bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                                   font=('Microsoft YaHei UI', 11), selectcolor=self.colors['card_bg'])
        subtitle_cb.grid(row=0, column=3, sticky=tk.W, pady=8, padx=(0, 20))

        # 线程数设置
        tk.Label(options_frame, text="线程数:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=0, column=4, sticky=tk.W, pady=8)
        
        self.threads_var = tk.StringVar(value="4")
        threads_combo = ttk.Combobox(options_frame, textvariable=self.threads_var, 
                                   values=["1", "2", "4", "8", "16"], width=8, font=('Microsoft YaHei UI', 11))
        threads_combo.grid(row=0, column=5, sticky=tk.W, pady=8, padx=(12, 0))

        # 第二行：转码选项
        self.transcode_var = tk.BooleanVar(value=False)
        transcode_cb = tk.Checkbutton(options_frame, text="🔄 下载后转码", variable=self.transcode_var,
                                    bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                                    font=('Microsoft YaHei UI', 11), selectcolor=self.colors['card_bg'])
        transcode_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(15, 8))

        tk.Label(options_frame, text="转码格式:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=1, column=2, sticky=tk.W, pady=(15, 8))
        
        self.transcode_format = tk.StringVar(value="mp4")
        transcode_combo = ttk.Combobox(options_frame, textvariable=self.transcode_format,
                                     values=["mp4", "mkv", "avi", "mov", "webm"], width=12,
                                     font=('Microsoft YaHei UI', 11))
        transcode_combo.grid(row=1, column=3, sticky=tk.W, pady=(15, 8), padx=(12, 0))

        # 操作按钮区域 - 增加对称性
        button_card = self.create_card(main_container, "操作控制", "🎮")
        button_card.pack(fill=tk.X, pady=(0, 15))

        button_frame = tk.Frame(button_card, bg=self.colors['card_bg'])
        button_frame.pack(fill=tk.X, padx=20, pady=15)

        # 创建按钮，增加间距和对称性
        start_btn = tk.Button(button_frame, text="🚀 开始下载", command=self.start_download,
                             bg=self.colors['primary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                             relief='flat', padx=25, pady=12, cursor='hand2', width=15)
        start_btn.pack(side=tk.LEFT, padx=(0, 15))

        stop_btn = tk.Button(button_frame, text="⏹️ 终止下载", command=self.stop_download,
                            bg=self.colors['accent'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                            relief='flat', padx=25, pady=12, cursor='hand2', width=15)
        stop_btn.pack(side=tk.LEFT, padx=(0, 15))

        clear_btn = tk.Button(button_frame, text="🗑️ 清空日志", command=self.clear_logs,
                             bg=self.colors['secondary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                             relief='flat', padx=25, pady=12, cursor='hand2', width=15)
        clear_btn.pack(side=tk.LEFT, padx=(0, 15))

        history_btn = tk.Button(button_frame, text="📚 查看历史", command=self.show_history,
                               bg='#8E44AD', fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                               relief='flat', padx=25, pady=12, cursor='hand2', width=15)
        history_btn.pack(side=tk.LEFT, padx=(0, 0))

        # 进度显示卡片 - 优化布局对称性
        progress_card = self.create_card(main_container, "下载进度", "📊")
        progress_card.pack(fill=tk.X, pady=(0, 15))

        progress_frame = tk.Frame(progress_card, bg=self.colors['card_bg'])
        progress_frame.pack(fill=tk.X, padx=20, pady=15)

        self.progress_label = tk.Label(progress_frame, text="准备就绪", bg=self.colors['card_bg'],
                                     fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12))
        self.progress_label.pack(anchor=tk.W, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', 
                                          maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.subtitle_var = tk.BooleanVar(value=False)
        subtitle_check = tk.Checkbutton(options_frame, text="📝 下载字幕", variable=self.subtitle_var,
                                       bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                                       font=('Microsoft YaHei UI', 11), selectcolor=self.colors['card_bg'])
        subtitle_check.grid(row=0, column=3, sticky=tk.W, pady=6, padx=20)

        # 第二行：高级选项
        tk.Label(options_frame, text="线程数:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12)).grid(row=1, column=0, sticky=tk.W, pady=(12, 6))
        
        self.threads_var = tk.StringVar(value="4")
        threads_combo = ttk.Combobox(options_frame, textvariable=self.threads_var, 
                                    values=["1", "2", "4", "8", "16"], width=8, font=('Microsoft YaHei UI', 11))
        threads_combo.grid(row=1, column=1, sticky=tk.W, pady=(12, 6), padx=(12, 8))

        self.transcode_var = tk.BooleanVar(value=False)
        transcode_check = tk.Checkbutton(options_frame, text="🔄 下载后转码", variable=self.transcode_var,
                                        bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                                        font=('Microsoft YaHei UI', 11), selectcolor=self.colors['card_bg'])
        transcode_check.grid(row=1, column=2, sticky=tk.W, pady=(12, 6), padx=12)

        self.transcode_format = tk.StringVar(value="mp4")
        transcode_combo = ttk.Combobox(options_frame, textvariable=self.transcode_format, 
                                      values=["mp4", "mkv", "avi", "mov", "webm"], width=10,
                                      font=('Microsoft YaHei UI', 11))
        transcode_combo.grid(row=1, column=3, sticky=tk.W, pady=(12, 6), padx=20)

        # 控制按钮 - 居中布局
        button_frame = tk.Frame(main_container, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=18)

        # 创建按钮容器，使按钮居中
        button_container = tk.Frame(button_frame, bg=self.colors['bg'])
        button_container.pack(expand=True)

        start_btn = tk.Button(button_container, text="🚀 开始下载", command=self.start_download,
                             bg=self.colors['primary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                             relief='flat', padx=30, pady=12, cursor='hand2')
        start_btn.pack(side=tk.LEFT, padx=(0, 12))

        stop_btn = tk.Button(button_container, text="⏹️ 停止下载", command=self.stop_download,
                            bg=self.colors['accent'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                            relief='flat', padx=30, pady=12, cursor='hand2')
        stop_btn.pack(side=tk.LEFT, padx=12)

        clear_btn = tk.Button(button_container, text="🗑️ 清空日志", command=self.clear_logs,
                             bg=self.colors['text_secondary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                             relief='flat', padx=30, pady=12, cursor='hand2')
        clear_btn.pack(side=tk.LEFT, padx=12)

        history_btn = tk.Button(button_container, text="📋 查看历史", command=self.show_history,
                               bg=self.colors['secondary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                               relief='flat', padx=30, pady=12, cursor='hand2')
        history_btn.pack(side=tk.LEFT, padx=12)

        # 进度卡片
        progress_card = self.create_card(main_container, "下载进度", "📊")
        progress_card.pack(fill=tk.X, pady=(0, 15))

        progress_frame = tk.Frame(progress_card, bg=self.colors['card_bg'])
        progress_frame.pack(fill=tk.X, padx=20, pady=15)

        self.progress_label = tk.Label(progress_frame, text="准备就绪", bg=self.colors['card_bg'], 
                                      fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 12))
        self.progress_label.pack(anchor=tk.W, pady=(0, 12))

        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', length=600)
        self.progress_bar.pack(fill=tk.X, pady=(0, 6))

        # 日志卡片
        log_card = self.create_card(main_container, "运行日志", "📝")
        log_card.pack(fill=tk.BOTH, expand=True)

        log_frame = tk.Frame(log_card, bg=self.colors['card_bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=14, 
                                                 font=('Consolas', 10), bg='#1E1E1E', fg='#FFFFFF',
                                                 relief='flat', bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        self.log_text.tag_configure("error", foreground="#FF6B6B")
        self.log_text.tag_configure("success", foreground="#51CF66")
        self.log_text.tag_configure("info", foreground="#FFFFFF")
        self.log_text.tag_configure("progress", foreground="#74C0FC")

    def browse_save_path(self):
        """浏览并选择保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)

    def validate_url(self, url):
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc, parsed.path])
        except ValueError:
            return False

    def fetch_video_info(self):
        """获取视频信息并预览"""
        url = self.url_entry.get().strip()
        proxy = self.proxy_entry.get().strip() or None

        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的 YouTube 链接")
            return

        self.logger.info(f"获取视频信息: {url}")

        def _fetch():
            try:
                # 使用外部 yt-dlp.exe
                ydl_path = resource_path(os.path.join("dependencies", "yt-dlp.exe"))
                if not os.path.exists(ydl_path):
                    ydl_path = "yt-dlp"  # 尝试系统路径

                cmd = [ydl_path, "--dump-json", "--no-download"]
                if proxy:
                    cmd.extend(["--proxy", proxy])
                cmd.append(url)
                
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    raise Exception(f"yt-dlp 执行失败: {result.stderr}")
                
                info_dict = json.loads(result.stdout)

                title = info_dict.get('title', '未知标题')
                duration = info_dict.get('duration', 0)
                views = info_dict.get('view_count', 0)
                uploader = info_dict.get('uploader', '未知上传者')

                # 格式化时长
                duration_str = "未知"
                if duration:
                    hours, remainder = divmod(int(duration), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if hours > 0:
                        duration_str = f"{hours}小时{minutes}分{seconds}秒"
                    else:
                        duration_str = f"{minutes}分{seconds}秒"

                # 格式化观看次数
                views_str = f"{views:,}" if views else "未知"

                self.title_var.set(f"标题: {title}")
                self.duration_var.set(f"时长: {duration_str}")
                self.views_var.set(f"观看次数: {views_str}")
                self.uploader_var.set(f"上传者: {uploader}")

                # 保存视频信息
                self.video_info[url] = info_dict

                self.result_queue.put(("success", f"成功获取视频信息: {title}"))
            except Exception as e:
                self.result_queue.put(("error", f"获取视频信息失败: {str(e)}"))

        # 在单独线程中获取信息
        threading.Thread(target=_fetch, daemon=True).start()

    def query_formats(self):
        """查询视频格式"""
        url = self.url_entry.get().strip()
        proxy = self.proxy_entry.get().strip() or None

        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的 YouTube 链接")
            return

        self.logger.info(f"查询视频格式: {url}")

        def _query():
            try:
                # 使用外部 yt-dlp.exe
                ydl_path = resource_path(os.path.join("dependencies", "yt-dlp.exe"))
                if not os.path.exists(ydl_path):
                    ydl_path = "yt-dlp"  # 尝试系统路径

                cmd = [ydl_path, "--list-formats", "--no-download"]
                if proxy:
                    cmd.extend(["--proxy", proxy])
                cmd.append(url)
                
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    raise Exception(f"yt-dlp 执行失败: {result.stderr}")
                
                # 显示格式列表
                self.result_queue.put(("info", f"可用格式:\n{result.stdout}"))

                # 同时获取 JSON 信息用于推荐
                cmd_json = [ydl_path, "--dump-json", "--no-download"]
                if proxy:
                    cmd_json.extend(["--proxy", proxy])
                cmd_json.append(url)
                
                result_json = subprocess.run(cmd_json, capture_output=True, text=True, encoding='utf-8')
                if result_json.returncode == 0:
                    info_dict = json.loads(result_json.stdout)
                    formats = info_dict.get('formats', [info_dict])

                    # 推荐格式ID：优先选择有大小的最高质量，避免N/A
                    best_video = None
                    best_audio = None

                    for f in formats:
                        # 视频格式
                        if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                            height = f.get('height')
                            if height is not None:
                                height = int(height)
                                if f.get('filesize') is not None:
                                    if best_video is None or height > int(best_video.get('height', 0)):
                                        best_video = f

                        # 音频格式
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            abr = f.get('abr')
                            if abr is not None:
                                abr = int(abr)
                                if f.get('filesize') is not None:
                                    if best_audio is None or abr > int(best_audio.get('abr', 0)):
                                        best_audio = f

                    if best_video and best_audio:
                        recommended_format = f"{best_video['format_id']}+{best_audio['format_id']}"
                        self.root.after(0, lambda: self.format_id_var.set(recommended_format))
                        self.root.after(0, lambda: self.result_queue.put(("info", f"推荐格式ID: {recommended_format} (最佳视频+最佳音频)")))

            except Exception as e:
                self.result_queue.put(("error", f"查询格式失败: {str(e)}"))

        # 在单独线程中查询格式
        threading.Thread(target=_query, daemon=True).start()

    def start_download(self):
        """开始下载视频或音频"""
        urls = []
        single_url = self.url_entry.get().strip()
        multi_urls = self.urls_text.get(1.0, tk.END).strip().split('\n')

        if single_url and self.validate_url(single_url):
            urls.append(single_url)

        for url in multi_urls:
            url = url.strip()
            if url and self.validate_url(url) and url not in urls:
                urls.append(url)

        if not urls:
            messagebox.showerror("错误", "请输入有效的 YouTube 链接")
            return

        proxy = self.proxy_entry.get().strip() or None
        save_path = self.save_path_var.get()
        download_subtitles = self.subtitle_var.get()
        thread_count = int(self.threads_var.get())
        transcode = self.transcode_var.get()
        transcode_format = self.transcode_format.get()
        format_id = self.format_id_var.get().strip()

        if not format_id:
            messagebox.showerror("错误", "请输入有效的格式ID")
            return

        # 准备下载任务
        self.download_tasks = urls.copy()
        self.current_task_index = 0
        self.total_tasks = len(urls)
        self.abort_all_tasks = False
        self.update_progress(0, "准备下载...")

        # 创建下载队列
        self.download_queue = queue.Queue()
        for url in urls:
            self.logger.info(f"添加下载任务: {url} (格式: {format_id})")
            self.download_queue.put(("download", url, proxy, save_path, format_id, download_subtitles, thread_count, transcode, transcode_format))

    def stop_download(self):
        """终止正在进行的下载"""
        if not self.is_downloading:
            messagebox.showinfo("提示", "当前没有正在进行的下载")
            return

        self.abort_all_tasks = True
        self.logger.info("正在终止所有下载任务...")

        # 等待所有线程结束
        for task_id, thread in list(self.download_threads.items()):
            if thread.is_alive():
                self.logger.info(f"等待任务 {task_id} 终止...")
                thread.join(timeout=1.0)

        self.is_downloading = False
        self.download_threads = {}
        self.update_progress(0, "所有下载已终止")
        self.logger.info("所有下载任务已终止")

    def update_progress(self, percent, message):
        """更新进度条和进度信息"""
        self.progress_bar['value'] = percent
        self.progress_label.config(text=message)
        self.root.update_idletasks()

    def process_queue(self):
        """处理下载队列"""
        while True:
            try:
                if self.abort_all_tasks:
                    # 清空队列
                    while not self.download_queue.empty():
                        self.download_queue.get()
                        self.download_queue.task_done()
                    continue

                task = self.download_queue.get(timeout=1)
                if task[0] == "download":
                    self.current_task_index += 1
                    self.update_progress(
                        (self.current_task_index-1) / self.total_tasks * 100, 
                        f"准备下载 {self.current_task_index}/{self.total_tasks}"
                    )

                    # 为每个下载任务创建唯一ID
                    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    # 在单独的线程中执行下载
                    thread = threading.Thread(
                        target=self._download, 
                        args=(task_id, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8]),
                        daemon=True
                    )
                    self.download_threads[task_id] = thread
                    thread.start()
                    self.download_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"处理任务时出错: {str(e)}")

    def _download(self, task_id, url, proxy, save_path, format_id, download_subtitles, thread_count, transcode, transcode_format):
        """下载视频或音频的实际处理函数"""
        self.is_downloading = True

        try:
            self.logger.info(f"开始下载到: {save_path}")

            # 更新进度条
            self.update_progress(
                (self.current_task_index-1) / self.total_tasks * 100, 
                f"下载中 {self.current_task_index}/{self.total_tasks}"
            )

            # 使用外部 yt-dlp.exe
            ydl_path = resource_path(os.path.join("dependencies", "yt-dlp.exe"))
            if not os.path.exists(ydl_path):
                ydl_path = "yt-dlp"  # 尝试系统路径

            cmd = [ydl_path, "-f", format_id, "-o", f"{save_path}/%(title)s.%(ext)s"]
            if proxy:
                cmd.extend(["--proxy", proxy])
            if download_subtitles:
                cmd.extend(["--write-subs", "--write-auto-subs", "--sub-langs", "en,zh-Hans,zh-Hant"])
            cmd.append(url)
            
            # 执行下载
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                     universal_newlines=True, encoding='utf-8')
            
            # 监控下载进度
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output and '[download]' in output:
                    self.result_queue.put(("progress", output.strip()))

            return_code = process.wait()
            
            if return_code != 0:
                stderr_output = process.stderr.read()
                raise Exception(f"下载失败，返回代码: {return_code}, 错误: {stderr_output}")

            if self.abort_all_tasks:
                self.result_queue.put(("info", f"下载已取消"))
                return

            self.logger.info(f"下载完成")
            self.update_progress(100, "下载完成")
            self.result_queue.put(("success", f"下载完成"))
            self.update_progress(
                self.current_task_index / self.total_tasks * 100, 
                f"完成 {self.current_task_index}/{self.total_tasks}"
            )

            # 保存下载历史
            self.save_download_history(url, "视频", format_id, save_path)

            # 如果启用了转码，执行转码
            if transcode:
                original_file = f"{save_path}/视频.{format_id.split('+')[0] if '+' in format_id else 'mp4'}"
                transcoded_file = f"{save_path}/视频.{transcode_format}"

                self.result_queue.put(("info", f"开始转码: {original_file} -> {transcoded_file}"))
                self.transcode_file(original_file, transcoded_file)

        except Exception as e:
            self.logger.error(f"下载失败: {str(e)}")
            self.update_progress(0, "下载失败")
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower() or "FFmpeg" in error_msg:
                self.result_queue.put(("error", f"下载失败: 需要ffmpeg但未安装。请安装ffmpeg并确保其在系统PATH中。"))
            elif 'Network' in error_msg or '403' in error_msg:
                self.result_queue.put(("error", "连接 YouTube 失败，可能是网络限制或无代理所致。"))
            else:
                self.result_queue.put(("error", f"下载失败: {error_msg}"))
        finally:
            self.is_downloading = False
            if task_id in self.download_threads:
                del self.download_threads[task_id]

    def process_results(self):
        """处理结果队列"""
        try:
            while not self.result_queue.empty():
                result = self.result_queue.get()
                if result[0] == "info":
                    self._append_log(result[1], "info")
                elif result[0] == "error":
                    self._append_log(f"错误: {result[1]}", "error")
                elif result[0] == "success":
                    self._append_log(f"成功: {result[1]}", "success")
                elif result[0] == "progress":
                    self._update_progress(result[1])
        except Exception as e:
            self._append_log(f"处理结果时出错: {str(e)}", "error")

        # 每隔100毫秒检查一次结果队列
        self.root.after(100, self.process_results)

    def _append_log(self, message, tag="info"):
        """向日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def _update_progress(self, message):
        """更新进度信息"""
        self.log_text.config(state=tk.NORMAL)
        # 清除最后一行（进度信息）
        self.log_text.delete("end-2l", "end-1c")
        self.log_text.insert(tk.END, message + "\n", "progress")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def clear_logs(self):
        """清空日志区域"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def load_download_history(self):
        """加载下载历史"""
        try:
            if os.path.exists("download_history.json"):
                with open("download_history.json", "r", encoding="utf-8") as f:
                    self.download_history = json.load(f)
            else:
                self.download_history = []
        except Exception as e:
            self.download_history = []
            self.logger.error(f"加载下载历史失败: {str(e)}")

    def save_download_history(self, url, title, format_id, save_path):
        """保存下载历史"""
        try:
            history_entry = {
                "url": url,
                "title": title,
                "format_id": format_id,
                "save_path": save_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            self.download_history.append(history_entry)

            # 只保留最近100条记录
            if len(self.download_history) > 100:
                self.download_history = self.download_history[-100:]

            with open("download_history.json", "w", encoding="utf-8") as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存下载历史失败: {str(e)}")

    def show_history(self):
        """显示下载历史"""
        if not hasattr(self, 'download_history') or not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载历史记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("1000x600")
        history_window.minsize(900, 500)

        # 设置窗口居中
        screen_width = history_window.winfo_screenwidth()
        screen_height = history_window.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 600) // 2
        history_window.geometry(f"1000x600+{x}+{y}")

        # 创建表格
        columns = ("序号", "标题", "URL", "格式", "保存路径", "时间")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")

        # 设置列宽和标题
        for col in columns:
            tree.heading(col, text=col)
            if col == "标题":
                tree.column(col, width=250)
            elif col == "URL":
                tree.column(col, width=300)
            elif col == "保存路径":
                tree.column(col, width=200)
            elif col == "时间":
                tree.column(col, width=150)
            else:
                tree.column(col, width=80)

        # 添加数据
        for i, entry in enumerate(reversed(self.download_history), 1):
            tree.insert("", "end", values=(
                i,
                entry.get("title", "未知"),
                entry.get("url", ""),
                entry.get("format_id", ""),
                entry.get("save_path", ""),
                entry.get("timestamp", "")
            ))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # 添加双击打开文件位置功能
        def open_file_location(event):
            if tree.selection():
                item = tree.selection()[0]
                values = tree.item(item, "values")
                path = values[4]

                if path and os.path.exists(path):
                    if platform.system() == "Windows":
                        os.startfile(path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", path])
                    else:  # Linux
                        subprocess.run(["xdg-open", path])
                else:
                    messagebox.showwarning("警告", "路径不存在或无效")

        tree.bind("<Double-1>", open_file_location)

    def transcode_file(self, input_file, output_file):
        """转码文件"""
        try:
            # 检查ffmpeg是否存在
            ffmpeg_path = resource_path(os.path.join("dependencies", "ffmpeg.exe"))
            if not os.path.exists(ffmpeg_path):
                ffmpeg_path = "ffmpeg"  # 尝试系统路径

            # 构建ffmpeg命令
            cmd = [
                ffmpeg_path,
                "-i", input_file,
                "-c:v", "libx264",  # 使用x264编码
                "-preset", "medium",  # 编码速度预设
                "-crf", "23",        # 质量控制
                "-c:a", "aac",       # 音频编码
                "-y",                # 覆盖已存在文件
                output_file
            ]

            # 执行转码
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            return_code = process.wait()

            if return_code == 0:
                self.result_queue.put(("success", f"转码完成: {output_file}"))
            else:
                stderr_output = process.stderr.read()
                self.result_queue.put(("error", f"转码失败，返回代码: {return_code}, 错误: {stderr_output}"))

        except Exception as e:
            self.result_queue.put(("error", f"转码过程中出错: {str(e)}"))

def show_splash_screen(root):
    """显示启动画面"""
    splash = tk.Toplevel(root)
    splash.title("加载中...")
    splash.geometry("500x350")
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)

    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 500) // 2
    y = (screen_height - 350) // 2
    splash.geometry(f"500x350+{x}+{y}")

    # 设置渐变背景
    splash.configure(bg='#F2F2F7')

    # 标题
    title_label = tk.Label(splash, text="VideoMaster Pro", 
                          font=('Microsoft YaHei UI', 24, 'bold'), 
                          fg="#007AFF", bg='#F2F2F7')
    title_label.pack(pady=(50, 10))

    # 副标题
    subtitle_label = tk.Label(splash, text="专业视频下载大师", 
                             font=('Microsoft YaHei UI', 14), 
                             fg="#8E8E93", bg='#F2F2F7')
    subtitle_label.pack(pady=(0, 30))

    # 进度条
    progress = ttk.Progressbar(splash, orient='horizontal', mode='indeterminate', length=400)
    progress.pack(pady=20)
    progress.start(10)

    # 状态标签
    status_label = tk.Label(splash, text="正在加载组件...", 
                           font=('Microsoft YaHei UI', 12), 
                           fg="#1D1D1F", bg='#F2F2F7')
    status_label.pack(pady=10)

    # 版本信息
    version_label = tk.Label(splash, text="Version 1.0", 
                            font=('Microsoft YaHei UI', 10), 
                            fg="#C7C7CC", bg='#F2F2F7')
    version_label.pack(side=tk.BOTTOM, pady=20)

    def close_splash():
        progress.stop()
        splash.destroy()
        root.deiconify()
        root.focus_force()

    root.after(3500, close_splash)

def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    show_splash_screen(root)
    app = VideoMasterProApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()

    def show_history(self):
        """显示下载历史"""
        if not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载历史记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("900x600")
        history_window.minsize(800, 500)

        # 创建表格
        columns = ("序号", "标题", "URL", "格式", "保存路径", "时间")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")

        # 设置列宽和标题
        for col in columns:
            tree.heading(col, text=col)
            if col == "标题":
                tree.column(col, width=250)
            elif col == "URL":
                tree.column(col, width=350)
            elif col == "保存路径":
                tree.column(col, width=200)
            else:
                tree.column(col, width=100)

        # 添加数据
        for i, entry in enumerate(reversed(self.download_history), 1):
            tree.insert("", "end", values=(
                i,
                entry["title"],
                entry["url"],
                entry["format_id"],
                entry["save_path"],
                entry["timestamp"]
            ))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # 添加双击打开文件位置功能
        def open_file_location(event):
            item = tree.selection()[0]
            values = tree.item(item, "values")
            path = values[4]

            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])

        tree.bind("<Double-1>", open_file_location)

    def transcode_file(self, input_file, output_file):
        """转码文件"""
        try:
            # 检查ffmpeg是否存在
            ffmpeg_path = resource_path(os.path.join("dependencies", "ffmpeg.exe"))
            if not os.path.exists(ffmpeg_path):
                try:
                    subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    ffmpeg_cmd = "ffmpeg"
                except (subprocess.SubprocessError, FileNotFoundError):
                    self.result_queue.put(("error", "转码失败: 未找到ffmpeg。请确保ffmpeg已安装并添加到系统PATH中。"))
                    return
            else:
                ffmpeg_cmd = ffmpeg_path

            # 构建ffmpeg命令
            cmd = [
                ffmpeg_cmd,
                "-i", input_file,
                "-c:v", "libx264",  # 使用x264编码
                "-preset", "medium",  # 编码速度预设
                "-crf", "23",        # 质量控制
                "-c:a", "aac",       # 音频编码
                "-strict", "experimental",
                "-y",                # 覆盖已存在文件
                output_file
            ]

            # 执行转码
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 监控转码进度
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # 可以在这里解析输出以获取进度信息
                    pass

            return_code = process.wait()

            if return_code == 0:
                self.result_queue.put(("success", f"转码完成: {output_file}"))
                # 删除原始文件（可选）
                # os.remove(input_file)
            else:
                self.result_queue.put(("error", f"转码失败，返回代码: {return_code}"))

        except Exception as e:
            self.result_queue.put(("error", f"转码过程中出错: {str(e)}"))

def show_splash_screen(root):
    splash = tk.Toplevel(root)
    splash.title("VideoMaster Pro")
    splash.geometry("600x400")
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)

    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 600) // 2
    y = (screen_height - 400) // 2
    splash.geometry(f"600x400+{x}+{y}")

    # 渐变背景
    canvas = tk.Canvas(splash, width=600, height=400, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # 创建渐变效果
    for i in range(400):
        color_ratio = i / 400
        r = int(0x00 + (0x74 - 0x00) * color_ratio)
        g = int(0x7A + (0xC0 - 0x7A) * color_ratio)
        b = int(0xFF + (0xFC - 0xFF) * color_ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        canvas.create_line(0, i, 600, i, fill=color, width=1)

    # 标题
    canvas.create_text(300, 140, text="VideoMaster Pro", 
                      font=('Microsoft YaHei UI', 32, 'bold'), fill='white')
    canvas.create_text(300, 180, text="专业视频下载大师", 
                      font=('Microsoft YaHei UI', 18), fill='white')
    canvas.create_text(300, 210, text="v1.0 优化版", 
                      font=('Microsoft YaHei UI', 14), fill='white')

    # 进度条
    progress_bg = canvas.create_rectangle(200, 280, 400, 300, fill='white', outline='')
    progress_bar = canvas.create_rectangle(200, 280, 200, 300, fill='#007AFF', outline='')

    # 状态文本
    status_text = canvas.create_text(300, 330, text="正在启动...", 
                                   font=('Microsoft YaHei UI', 14), fill='white')

    def animate_progress():
        for i in range(101):
            progress_width = int(200 * i / 100)
            canvas.coords(progress_bar, 200, 280, 200 + progress_width, 300)
            
            if i < 30:
                canvas.itemconfig(status_text, text="🔧 初始化组件...")
            elif i < 60:
                canvas.itemconfig(status_text, text="⚙️ 加载配置...")
            elif i < 90:
                canvas.itemconfig(status_text, text="🎨 准备界面...")
            else:
                canvas.itemconfig(status_text, text="✅ 启动完成!")
            
            splash.update()
            splash.after(25)

    def close_splash():
        animate_progress()
        splash.after(800)
        splash.destroy()
        root.deiconify()
        root.focus_force()

    splash.after(100, close_splash)

def main():
    root = tk.Tk()
    root.withdraw()
    show_splash_screen(root)
    app = VideoMasterProApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
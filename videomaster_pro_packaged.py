import os
import sys
import tempfile
import shutil

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_tool_path(tool_name):
    """获取工具的路径"""
    if hasattr(sys, '_MEIPASS'):
        tool_path = resource_path(tool_name)
        if os.path.exists(tool_path):
            temp_dir = tempfile.gettempdir()
            temp_tool_path = os.path.join(temp_dir, tool_name)
            if not os.path.exists(temp_tool_path):
                shutil.copy2(tool_path, temp_tool_path)
            return temp_tool_path
    else:
        if os.path.exists(tool_name):
            return os.path.abspath(tool_name)
    return tool_name


import yt_dlp
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

class VideoMasterProApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoMaster Pro - 紧凑版 (完整功能)")
        self.root.geometry("1000x700")
        self.root.minsize(950, 650)
        
        # 居中窗口
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"1000x700+{x}+{y}")
        
        # 颜色主题
        self.colors = {
            'bg': '#f5f5f7',
            'card': '#ffffff',
            'primary': '#007aff',
            'secondary': '#5856d6',
            'success': '#34c759',
            'warning': '#ff9500',
            'danger': '#ff3b30',
            'text': '#1d1d1f',
            'text_secondary': '#86868b'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
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
        self.last_formats_data = None  # 存储格式数据用于重新打开窗口
        
        self.setup_logging()
        self.create_widgets()
        self.load_download_history()
        
        # 启动处理线程
        self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()
        
        # 启动结果处理
        self.process_results()
        
        # 绑定鼠标滚轮事件
        self.bind_mousewheel()
    
    def bind_mousewheel(self):
        """绑定鼠标滚轮事件"""
        def _on_mousewheel(event):
            if hasattr(self, 'main_canvas') and self.main_canvas.winfo_exists():
                self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.root.bind("<MouseWheel>", _on_mousewheel)
    
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                self.log_queue.put(('log', record.levelname, self.format(record)))
        
        self.log_handler = QueueHandler(self.result_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)
    
    def create_card(self, parent, title, **kwargs):
        """创建卡片样式的框架"""
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=0)
        
        if title:
            title_frame = tk.Frame(card, bg=self.colors['card'])
            title_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
            
            title_label = tk.Label(
                title_frame, 
                text=title, 
                font=('SF Pro Display', 14, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text']
            )
            title_label.pack(anchor=tk.W)
        
        content_frame = tk.Frame(card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        return card, content_frame
    
    def create_widgets(self):
        """创建界面组件 - 紧凑布局"""
        # 创建可滚动的主框架
        main_canvas = tk.Canvas(self.root, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局滚动组件
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.main_canvas = main_canvas
        
        # 主容器
        main_container = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. URL输入卡片
        url_card, url_content = self.create_card(main_container, "🎬 视频链接")
        url_card.pack(fill=tk.X, pady=(0, 15))
        
        # URL输入行
        url_row = tk.Frame(url_content, bg=self.colors['card'])
        url_row.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(url_row, text="链接:", font=('SF Pro Display', 11), 
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.url_entry = tk.Entry(url_row, font=('SF Pro Display', 11), relief='flat', bd=5)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")
        
        fetch_btn = tk.Button(url_row, text="获取信息", font=('SF Pro Display', 10, 'bold'),
                             bg=self.colors['primary'], fg='white', relief='flat', bd=0,
                             padx=20, command=self.fetch_video_info)
        fetch_btn.pack(side=tk.RIGHT)
        
        # 批量URL输入
        tk.Label(url_content, text="批量链接 (每行一个):", font=('SF Pro Display', 11),
                bg=self.colors['card'], fg=self.colors['text']).pack(anchor=tk.W, pady=(10, 5))
        
        self.urls_text = scrolledtext.ScrolledText(url_content, wrap=tk.WORD, height=3,
                                                  font=('SF Pro Display', 10), relief='flat', bd=5)
        self.urls_text.pack(fill=tk.X, pady=(0, 10))
        
        # 代理设置
        proxy_row = tk.Frame(url_content, bg=self.colors['card'])
        proxy_row.pack(fill=tk.X)
        
        tk.Label(proxy_row, text="代理:", font=('SF Pro Display', 11),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.proxy_entry = tk.Entry(proxy_row, font=('SF Pro Display', 11), relief='flat', bd=5)
        self.proxy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")
        
        # 2. 双列布局 - 视频信息和下载选项
        middle_frame = tk.Frame(main_container, bg=self.colors['bg'])
        middle_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 左列 - 视频信息
        left_column = tk.Frame(middle_frame, bg=self.colors['bg'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        
        info_card, info_content = self.create_card(left_column, "📺 视频信息")
        info_card.pack(fill=tk.BOTH, expand=True)
        
        self.title_var = tk.StringVar(value="标题: 等待获取...")
        self.duration_var = tk.StringVar(value="时长: --")
        self.views_var = tk.StringVar(value="观看: --")
        self.uploader_var = tk.StringVar(value="作者: --")
        
        for var in [self.title_var, self.duration_var, self.views_var, self.uploader_var]:
            label = tk.Label(info_content, textvariable=var, font=('SF Pro Display', 10),
                           bg=self.colors['card'], fg=self.colors['text'], anchor=tk.W)
            label.pack(fill=tk.X, pady=2)
        
        # 右列 - 下载选项
        right_column = tk.Frame(middle_frame, bg=self.colors['bg'])
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        
        options_card, options_content = self.create_card(right_column, "⚙️ 下载选项")
        options_card.pack(fill=tk.BOTH, expand=True)
        
        # 格式选择
        format_row = tk.Frame(options_content, bg=self.colors['card'])
        format_row.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(format_row, text="格式:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.format_id_var = tk.StringVar(value="bv*+ba/b")
        self.format_entry = tk.Entry(format_row, textvariable=self.format_id_var, 
                                    font=('SF Pro Display', 10), width=12, relief='flat', bd=3)
        self.format_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        # 绑定点击事件重新打开格式窗口
        self.format_entry.bind("<Button-1>", self.reopen_formats_window)
        
        query_btn = tk.Button(format_row, text="查询", font=('SF Pro Display', 9),
                             bg=self.colors['secondary'], fg='white', relief='flat', bd=0,
                             padx=15, command=self.query_formats)
        query_btn.pack(side=tk.RIGHT)
        
        # 其他选项
        options_row1 = tk.Frame(options_content, bg=self.colors['card'])
        options_row1.pack(fill=tk.X, pady=(0, 5))
        
        self.subtitle_var = tk.BooleanVar(value=False)
        subtitle_cb = tk.Checkbutton(options_row1, text="字幕", variable=self.subtitle_var,
                                   font=('SF Pro Display', 10), bg=self.colors['card'])
        subtitle_cb.pack(side=tk.LEFT)
        
        tk.Label(options_row1, text="线程:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(20, 5))
        
        self.threads_var = tk.StringVar(value="4")
        threads_combo = ttk.Combobox(options_row1, textvariable=self.threads_var,
                                   values=["1", "2", "4", "8"], width=5, font=('SF Pro Display', 9))
        threads_combo.pack(side=tk.LEFT)
        
        options_row2 = tk.Frame(options_content, bg=self.colors['card'])
        options_row2.pack(fill=tk.X)
        
        self.transcode_var = tk.BooleanVar(value=False)
        transcode_cb = tk.Checkbutton(options_row2, text="转码", variable=self.transcode_var,
                                    font=('SF Pro Display', 10), bg=self.colors['card'])
        transcode_cb.pack(side=tk.LEFT)
        
        self.transcode_format = tk.StringVar(value="mp4")
        transcode_combo = ttk.Combobox(options_row2, textvariable=self.transcode_format,
                                     values=["mp4", "mkv", "avi"], width=8, font=('SF Pro Display', 9))
        transcode_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 3. 保存路径卡片
        path_card, path_content = self.create_card(main_container, "📁 保存路径")
        path_card.pack(fill=tk.X, pady=(0, 15))
        
        path_row = tk.Frame(path_content, bg=self.colors['card'])
        path_row.pack(fill=tk.X)
        
        self.save_path_var = tk.StringVar(value=os.getcwd())
        path_entry = tk.Entry(path_row, textvariable=self.save_path_var,
                             font=('SF Pro Display', 11), relief='flat', bd=5)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(path_row, text="浏览", font=('SF Pro Display', 10, 'bold'),
                              bg=self.colors['warning'], fg='white', relief='flat', bd=0,
                              padx=20, command=self.browse_save_path)
        browse_btn.pack(side=tk.RIGHT)
        
        # 4. 控制按钮
        button_frame = tk.Frame(main_container, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        buttons = [
            ("开始下载", self.colors['success'], self.start_download),
            ("停止下载", self.colors['danger'], self.stop_download),
            ("清空日志", self.colors['text_secondary'], self.clear_logs),
            ("下载历史", self.colors['primary'], self.show_history)
        ]
        
        for i, (text, color, command) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, font=('SF Pro Display', 11, 'bold'),
                           bg=color, fg='white', relief='flat', bd=0, padx=25, pady=8,
                           command=command)
            btn.pack(side=tk.LEFT, padx=(0, 10) if i < len(buttons)-1 else 0)
        
        # 5. 进度显示
        progress_card, progress_content = self.create_card(main_container, "📊 下载进度")
        progress_card.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_label = tk.Label(progress_content, text="准备就绪",
                                     font=('SF Pro Display', 11), bg=self.colors['card'],
                                     fg=self.colors['text'])
        self.progress_label.pack(anchor=tk.W, pady=(0, 8))
        
        self.progress_bar = ttk.Progressbar(progress_content, orient='horizontal',
                                          mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # 6. 日志显示
        log_card, log_content = self.create_card(main_container, "📋 运行日志")
        log_card.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_content, wrap=tk.WORD, height=8,
                                                font=('Consolas', 9), relief='flat', bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 配置日志颜色
        self.log_text.tag_configure("ERROR", foreground=self.colors['danger'])
        self.log_text.tag_configure("SUCCESS", foreground=self.colors['success'])
        self.log_text.tag_configure("INFO", foreground=self.colors['text'])
        self.log_text.tag_configure("WARNING", foreground=self.colors['warning'])
    
    def browse_save_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)
    
    def validate_url(self, url):
        """验证URL"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except:
            return False
    
    def fetch_video_info(self):
        """获取视频信息"""
        url = self.url_entry.get().strip()
        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        def _fetch():
            try:
                proxy = self.proxy_entry.get().strip() or None
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'proxy': proxy
                }
                
                # 使用外部 yt-dlp.exe
        yt_dlp_path = get_tool_path("yt-dlp.exe")
        
        # 构建命令行参数
        cmd = [yt_dlp_path]
        if proxy:
            cmd.extend(["--proxy", proxy])
        cmd.extend(["--quiet", "--no-warnings"])
        
        # 临时使用 yt_dlp 库进行信息获取
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    title = info.get('title', '未知')
                    duration = info.get('duration', 0)
                    views = info.get('view_count', 0)
                    uploader = info.get('uploader', '未知')
                    
                    # 格式化时长
                    if duration:
                        hours, remainder = divmod(int(duration), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = "未知"
                    
                    # 格式化观看次数
                    views_str = f"{views:,}" if views else "未知"
                    
                    self.root.after(0, lambda: [
                        self.title_var.set(f"标题: {title[:50]}..."),
                        self.duration_var.set(f"时长: {duration_str}"),
                        self.views_var.set(f"观看: {views_str}"),
                        self.uploader_var.set(f"作者: {uploader}")
                    ])
                    
                    self.video_info[url] = info
                    self.result_queue.put(('success', f"获取视频信息成功: {title}"))
                    
            except Exception as e:
                self.result_queue.put(('error', f"获取视频信息失败: {str(e)}"))
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def query_formats(self):
        """查询可用格式并显示选择窗口"""
        url = self.url_entry.get().strip()
        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        def _query():
            try:
                proxy = self.proxy_entry.get().strip() or None
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'proxy': proxy
                }
                
                # 使用外部 yt-dlp.exe
        yt_dlp_path = get_tool_path("yt-dlp.exe")
        
        # 构建命令行参数
        cmd = [yt_dlp_path]
        if proxy:
            cmd.extend(["--proxy", proxy])
        cmd.extend(["--quiet", "--no-warnings"])
        
        # 临时使用 yt_dlp 库进行信息获取
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    
                    # 推荐格式计算
                    video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('height')]
                    audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('abr')]
                    
                    recommended_format = None
                    if video_formats and audio_formats:
                        video_formats.sort(key=lambda f: f.get('height', 0), reverse=True)
                        audio_formats.sort(key=lambda f: f.get('abr', 0), reverse=True)
                        best_video = video_formats[0]
                        best_audio = audio_formats[0]
                        recommended_format = f"{best_video['format_id']}+{best_audio['format_id']}"
                    
                    # 保存格式数据并显示窗口
                    self.last_formats_data = (info.get('title', '未知标题'), formats, recommended_format)
                    self.root.after(0, lambda: self.show_formats_window(info.get('title', '未知标题'), formats, recommended_format))
                    
            except Exception as e:
                self.result_queue.put(('error', f"查询格式失败: {str(e)}"))
        
        threading.Thread(target=_query, daemon=True).start()
    
    def show_formats_window(self, title, formats, recommended_format):
        """显示格式选择窗口"""
        formats_window = tk.Toplevel(self.root)
        formats_window.title(f"格式选择 - {title[:50]}")
        formats_window.configure(bg=self.colors['bg'])
        
        # 设置窗口大小并居中
        popup_width = 900
        popup_height = 600
        
        # 获取主窗口位置
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        # 计算居中位置
        center_x = main_x + (main_width - popup_width) // 2
        center_y = main_y + (main_height - popup_height) // 2
        
        formats_window.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
        formats_window.minsize(800, 500)
        formats_window.transient(self.root)
        formats_window.grab_set()
        
        # 主框架
        main_frame = tk.Frame(formats_window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(main_frame, text=f"📺 {title}", 
                              font=('SF Pro Display', 14, 'bold'),
                              bg=self.colors['bg'], fg=self.colors['text'])
        title_label.pack(pady=(0, 15))
        
        # 创建表格
        columns = ("ID", "格式", "分辨率", "帧率", "视频编码", "音频编码", "大小(MB)", "备注")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        tree.heading("ID", text="ID")
        tree.column("ID", width=80, anchor=tk.W)
        tree.heading("格式", text="格式")
        tree.column("格式", width=60, anchor=tk.CENTER)
        tree.heading("分辨率", text="分辨率")
        tree.column("分辨率", width=100)
        tree.heading("帧率", text="帧率")
        tree.column("帧率", width=60, anchor=tk.CENTER)
        tree.heading("视频编码", text="视频编码")
        tree.column("视频编码", width=120)
        tree.heading("音频编码", text="音频编码")
        tree.column("音频编码", width=120)
        tree.heading("大小(MB)", text="大小(MB)")
        tree.column("大小(MB)", width=100, anchor=tk.E)
        tree.heading("备注", text="备注")
        tree.column("备注", width=120)
        
        # 格式化文件大小
        def format_size(size_in_bytes):
            if size_in_bytes is None or not isinstance(size_in_bytes, (int, float)):
                return "N/A"
            return f"{size_in_bytes / (1024*1024):.1f}"
        
        # 添加数据
        for f in sorted(formats, key=lambda x: (x.get('height', 0) or 0, x.get('fps', 0) or 0), reverse=True):
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            
            resolution = 'N/A'
            if vcodec != 'none':
                height = f.get('height')
                width = f.get('width')
                if height:
                    resolution = f"{height}p"
                elif width and height:
                    resolution = f"{width}x{height}"
            
            # 备注
            note = ''
            if vcodec != 'none' and acodec == 'none':
                note = '纯视频'
            elif vcodec == 'none' and acodec != 'none':
                note = '纯音频'
            elif vcodec != 'none' and acodec != 'none':
                note = '视频+音频'
            
            filesize = f.get('filesize') or f.get('filesize_approx')
            
            tree.insert("", "end", values=(
                f.get('format_id', ''),
                f.get('ext', ''),
                resolution,
                f.get('fps', '') or '',
                vcodec if vcodec != 'none' else '',
                acodec if acodec != 'none' else '',
                format_size(filesize),
                note
            ))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 双击选择事件
        def on_double_click(event):
            try:
                item = tree.selection()[0]
                format_id = tree.item(item, "values")[0]
                self.format_id_var.set(format_id)
                formats_window.destroy()
                self.result_queue.put(('success', f"已选择格式: {format_id}"))
            except IndexError:
                pass
        
        tree.bind("<Double-1>", on_double_click)
        
        # 推荐格式区域
        if recommended_format:
            recommend_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', bd=1)
            recommend_frame.pack(fill=tk.X, pady=(0, 15))
            
            rec_inner = tk.Frame(recommend_frame, bg=self.colors['card'])
            rec_inner.pack(fill=tk.X, padx=15, pady=10)
            
            tk.Label(rec_inner, text="💡 推荐格式:", font=('SF Pro Display', 11, 'bold'),
                    bg=self.colors['card'], fg=self.colors['primary']).pack(side=tk.LEFT)
            
            rec_entry = tk.Entry(rec_inner, font=('SF Pro Display', 11), 
                               fg=self.colors['primary'], relief='flat', bd=0)
            rec_entry.insert(0, recommended_format)
            rec_entry.config(state='readonly')
            rec_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
            
            def use_recommendation():
                self.format_id_var.set(recommended_format)
                formats_window.destroy()
                self.result_queue.put(('success', f"已采用推荐格式: {recommended_format}"))
            
            use_btn = tk.Button(rec_inner, text="使用推荐", font=('SF Pro Display', 10, 'bold'),
                               bg=self.colors['success'], fg='white', relief='flat', bd=0,
                               padx=20, command=use_recommendation)
            use_btn.pack(side=tk.RIGHT)
        
        # 底部按钮
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X)
        
        def use_selected():
            try:
                item = tree.selection()[0]
                format_id = tree.item(item, "values")[0]
                self.format_id_var.set(format_id)
                formats_window.destroy()
                self.result_queue.put(('success', f"已选择格式: {format_id}"))
            except IndexError:
                messagebox.showwarning("提示", "请先选择一个格式")
        
        select_btn = tk.Button(button_frame, text="使用选中格式", font=('SF Pro Display', 10, 'bold'),
                              bg=self.colors['primary'], fg='white', relief='flat', bd=0,
                              padx=20, command=use_selected)
        select_btn.pack(side=tk.LEFT)
        
        cancel_btn = tk.Button(button_frame, text="取消", font=('SF Pro Display', 10),
                              bg=self.colors['text_secondary'], fg='white', relief='flat', bd=0,
                              padx=20, command=formats_window.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def reopen_formats_window(self, event=None):
        """重新打开格式选择窗口"""
        if hasattr(self, 'last_formats_data') and self.last_formats_data:
            title, formats, recommended_format = self.last_formats_data
            self.show_formats_window(title, formats, recommended_format)
        else:
            self.result_queue.put(('info', "请先点击查询获取格式数据"))
    
    def start_download(self):
        """开始下载"""
        urls = []
        
        # 获取单个URL
        single_url = self.url_entry.get().strip()
        if single_url and self.validate_url(single_url):
            urls.append(single_url)
        
        # 获取批量URL
        batch_urls = self.urls_text.get(1.0, tk.END).strip().split('\n')
        for url in batch_urls:
            url = url.strip()
            if url and self.validate_url(url) and url not in urls:
                urls.append(url)
        
        if not urls:
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        # 准备下载参数
        proxy = self.proxy_entry.get().strip() or None
        save_path = self.save_path_var.get()
        format_id = self.format_id_var.get().strip() or "bv*+ba/b"
        download_subtitles = self.subtitle_var.get()
        thread_count = int(self.threads_var.get())
        transcode = self.transcode_var.get()
        transcode_format = self.transcode_format.get()
        
        # 设置任务
        self.download_tasks = urls.copy()
        self.current_task_index = 0
        self.total_tasks = len(urls)
        self.abort_all_tasks = False
        
        # 添加到队列
        for url in urls:
            self.download_queue.put((
                'download', url, proxy, save_path, format_id,
                download_subtitles, thread_count, transcode, transcode_format
            ))
        
        self.result_queue.put(('info', f"开始下载 {len(urls)} 个视频"))
    
    def stop_download(self):
        """停止下载"""
        self.abort_all_tasks = True
        self.result_queue.put(('warning', "正在停止所有下载任务..."))
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show_history(self):
        """显示下载历史"""
        if not hasattr(self, 'download_history') or not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载记录")
            return
        
        # 创建历史窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("900x500")
        history_window.configure(bg=self.colors['bg'])
        
        # 创建表格
        columns = ("时间", "标题", "格式", "状态")
        tree = ttk.Treeview(history_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        
        # 添加数据
        for entry in reversed(self.download_history[-50:]):  # 最近50条
            tree.insert("", "end", values=(
                entry.get('timestamp', ''),
                entry.get('title', '')[:50],
                entry.get('format_id', ''),
                '完成'
            ))
        
        # 滚动条
        scrollbar_h = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar_h.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        scrollbar_h.pack(side=tk.RIGHT, fill=tk.Y, pady=20)
    
    def process_queue(self):
        """处理下载队列"""
        while True:
            try:
                if self.abort_all_tasks:
                    # 清空队列
                    while not self.download_queue.empty():
                        try:
                            self.download_queue.get_nowait()
                        except:
                            break
                    continue
                
                task = self.download_queue.get(timeout=1)
                if task[0] == 'download':
                    self.current_task_index += 1
                    self._download(*task[1:])
                
            except queue.Empty:
                continue
            except Exception as e:
                self.result_queue.put(('error', f"处理队列错误: {str(e)}"))
    
    def _download(self, url, proxy, save_path, format_id, download_subtitles, thread_count, transcode, transcode_format):
        """执行下载"""
        try:
            self.is_downloading = True
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                'quiet': True,
                'no_warnings': True,
                'proxy': proxy,
                'writesubtitles': download_subtitles,
                'writeautomaticsub': download_subtitles,
                'progress_hooks': [self._progress_hook]
            }
            
            # 使用外部 yt-dlp.exe
        yt_dlp_path = get_tool_path("yt-dlp.exe")
        
        # 构建命令行参数
        cmd = [yt_dlp_path]
        if proxy:
            cmd.extend(["--proxy", proxy])
        cmd.extend(["--quiet", "--no-warnings"])
        
        # 临时使用 yt_dlp 库进行信息获取
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not self.abort_all_tasks:
                    title = info.get('title', 'Unknown')
                    self.result_queue.put(('success', f"下载完成: {title}"))
                    self.save_download_history(url, title, format_id, save_path)
        
        except Exception as e:
            self.result_queue.put(('error', f"下载失败: {str(e)}"))
        finally:
            self.is_downloading = False
    
    def _progress_hook(self, d):
        """下载进度回调"""
        if self.abort_all_tasks:
            return
        
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            
            try:
                progress_val = float(percent.strip('%'))
                overall_progress = (self.current_task_index - 1 + progress_val/100) / self.total_tasks * 100
                
                self.root.after(0, lambda: [
                    setattr(self.progress_bar, 'value', overall_progress),
                    self.progress_label.config(text=f"下载中 {self.current_task_index}/{self.total_tasks}: {percent} ({speed})")
                ])
            except:
                pass
        
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.progress_label.config(text="处理文件中..."))
    
    def load_download_history(self):
        """加载下载历史"""
        try:
            if os.path.exists("download_history.json"):
                with open("download_history.json", "r", encoding="utf-8") as f:
                    self.download_history = json.load(f)
            else:
                self.download_history = []
        except:
            self.download_history = []
    
    def save_download_history(self, url, title, format_id, save_path):
        """保存下载历史"""
        try:
            entry = {
                "url": url,
                "title": title,
                "format_id": format_id,
                "save_path": save_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.download_history.append(entry)
            
            # 保留最近100条
            if len(self.download_history) > 100:
                self.download_history = self.download_history[-100:]
            
            with open("download_history.json", "w", encoding="utf-8") as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存历史失败: {str(e)}")
    
    def process_results(self):
        """处理结果队列"""
        try:
            while not self.result_queue.empty():
                try:
                    result = self.result_queue.get_nowait()
                    
                    if len(result) >= 2:
                        msg_type = result[0]
                        message = result[1]
                        
                        if msg_type == 'log' and len(result) >= 3:
                            level = result[1]
                            message = result[2]
                            self._append_log(f"[{level}] {message}", level.upper())
                        else:
                            self._append_log(message, msg_type.upper())
                
                except queue.Empty:
                    break
                except Exception as e:
                    self._append_log(f"处理结果错误: {str(e)}", "ERROR")
        
        except Exception as e:
            print(f"Process results error: {e}")
        
        # 继续处理
        self.root.after(100, self.process_results)
    
    def _append_log(self, message, tag="INFO"):
        """添加日志"""
        try:
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
        except:
            pass

def show_splash_screen(root):
    """显示启动画面"""
    splash = tk.Toplevel(root)
    splash.title("VideoMaster Pro")
    splash.geometry("450x300")
    splash.overrideredirect(True)
    splash.configure(bg='#f5f5f7')
    
    # 居中
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 450) // 2
    y = (screen_height - 300) // 2
    splash.geometry(f"450x300+{x}+{y}")
    
    # 标题
    title_label = tk.Label(splash, text="VideoMaster Pro", 
                          font=('SF Pro Display', 24, 'bold'),
                          bg='#f5f5f7', fg='#007aff')
    title_label.pack(pady=(60, 20))
    
    # 副标题
    subtitle_label = tk.Label(splash, text="紧凑版 - 完整功能", 
                             font=('SF Pro Display', 12),
                             bg='#f5f5f7', fg='#86868b')
    subtitle_label.pack(pady=(0, 40))
    
    # 进度条
    progress = ttk.Progressbar(splash, mode='indeterminate', length=300)
    progress.pack(pady=20)
    progress.start(10)
    
    # 状态
    status_label = tk.Label(splash, text="正在加载...", 
                           font=('SF Pro Display', 10),
                           bg='#f5f5f7', fg='#1d1d1f')
    status_label.pack(pady=10)
    
    def close_splash():
        progress.stop()
        splash.destroy()
        root.deiconify()
        root.focus_force()
    
    splash.after(2500, close_splash)

def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    show_splash_screen(root)
    app = VideoMasterProApp(root)
    
    root.mainloop()

if __name__ == '__main__':
    main()
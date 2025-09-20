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
        self.root.title("VideoMaster Pro - 专业视频下载大师 v2.0")
        self.root.geometry("1100x850")
        self.root.minsize(1000, 800)
        
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
        x = (screen_width - 1100) // 2
        y = (screen_height - 850) // 2
        self.root.geometry(f"1100x850+{x}+{y}")

        # 设置现代化字体和样式
        self.setup_apple_styles()

        # 初始化变量
        self.download_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self.download_tasks = []
        self.current_task_index = 0
        self.total_tasks = 0
        self.abort_all_tasks = False

        self.video_info = {}

        self.setup_logging()

        self.create_widgets()

        self.load_download_history()

        self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()

        self.root.after(100, self.process_results)

        self.ydl_instance = None
        self.is_downloading = False
        self.download_threads = {}

        # 默认置顶
        self.is_topmost = True
        self.root.attributes('-topmost', True)

    def setup_apple_styles(self):
        """设置苹果风格样式"""
        try:
            # 设置现代化颜色方案
            self.style = ttk.Style()
            
            # 配置各种控件的样式
            self.style.configure('TLabel', 
                background=self.colors['bg'],
                foreground=self.colors['text_primary'],
                font=('Microsoft YaHei UI', 10))
            
            self.style.configure('TButton', 
                font=('Microsoft YaHei UI', 10, 'bold'),
                borderwidth=1,
                relief='solid',
                focuscolor='none')
            
            self.style.map('TButton',
                background=[('active', self.colors['hover']),
                           ('pressed', self.colors['primary'])],
                foreground=[('active', self.colors['text_primary']),
                           ('pressed', 'white')])
            
            self.style.configure('TEntry', 
                fieldbackground=self.colors['card_bg'],
                borderwidth=1,
                relief='solid',
                font=('Microsoft YaHei UI', 10))
            
            self.style.configure('TCombobox', 
                fieldbackground=self.colors['card_bg'],
                font=('Microsoft YaHei UI', 10))
            
            self.style.configure('TLabelFrame', 
                background=self.colors['bg'],
                foreground=self.colors['text_primary'],
                font=('Microsoft YaHei UI', 11, 'bold'))
            
            self.style.configure('TLabelFrame.Label', 
                background=self.colors['bg'],
                foreground=self.colors['text_primary'],
                font=('Microsoft YaHei UI', 11, 'bold'))
            
            self.style.configure('TFrame', 
                background=self.colors['bg'])
            
            self.style.configure('TCheckbutton', 
                background=self.colors['bg'],
                foreground=self.colors['text_primary'],
                font=('Microsoft YaHei UI', 10))
            
            self.style.configure('TProgressbar',
                background=self.colors['primary'],
                troughcolor=self.colors['hover'],
                borderwidth=0,
                lightcolor=self.colors['primary'],
                darkcolor=self.colors['primary'])
                
        except Exception as e:
            # 如果样式设置失败，使用默认样式
            pass

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue

            def emit(self, record):
                self.log_queue.put((record.levelname, self.format(record)))

        self.result_queue = queue.Queue()
        self.log_handler = QueueHandler(self.result_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题栏
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="VideoMaster Pro", 
                               font=('Microsoft YaHei UI', 18, 'bold'),
                               foreground=self.colors['primary'])
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, text="专业视频下载大师", 
                                  font=('Microsoft YaHei UI', 12),
                                  foreground=self.colors['text_secondary'])
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # 置顶按钮
        self.topmost_button = ttk.Button(title_frame, text="📌", width=3,
                                        command=self.toggle_topmost)
        self.topmost_button.pack(side=tk.RIGHT)

        # 视频信息区域
        url_frame = ttk.LabelFrame(main_frame, text="🎬 视频信息", padding=15)
        url_frame.pack(fill=tk.X, pady=5)

        ttk.Label(url_frame, text="YouTube 链接:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=60, font=('Microsoft YaHei UI', 10))
        self.url_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")

        fetch_button = ttk.Button(url_frame, text="获取信息", command=self.fetch_video_info)
        fetch_button.grid(row=0, column=2, padx=5, rowspan=2, sticky=tk.NS)

        ttk.Label(url_frame, text="批量链接 (每行一个):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.urls_text = scrolledtext.ScrolledText(url_frame, wrap=tk.WORD, height=3, 
                                                  font=('Microsoft YaHei UI', 10))
        self.urls_text.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        ttk.Label(url_frame, text="代理地址 (可选):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.proxy_entry = ttk.Entry(url_frame, width=60, font=('Microsoft YaHei UI', 10))
        self.proxy_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")

        # 保存路径区域
        path_frame = ttk.LabelFrame(main_frame, text="💾 保存路径", padding=15)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.save_path_var = tk.StringVar(value=os.getcwd())
        ttk.Entry(path_frame, textvariable=self.save_path_var, width=50, 
                 font=('Microsoft YaHei UI', 10)).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(path_frame, text="浏览", command=self.browse_save_path).grid(row=0, column=2, padx=5)

        # 视频信息预览区域
        info_frame = ttk.LabelFrame(main_frame, text="📋 视频预览", padding=15)
        info_frame.pack(fill=tk.X, pady=5)

        self.title_var = tk.StringVar(value="标题: 等待获取...")
        self.duration_var = tk.StringVar(value="时长: --")
        self.views_var = tk.StringVar(value="观看次数: --")
        self.uploader_var = tk.StringVar(value="上传者: --")

        ttk.Label(info_frame, textvariable=self.title_var, 
                 foreground=self.colors['primary']).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.duration_var, 
                 foreground=self.colors['primary']).grid(row=0, column=1, sticky=tk.W, pady=2, padx=20)
        ttk.Label(info_frame, textvariable=self.views_var, 
                 foreground=self.colors['primary']).grid(row=0, column=2, sticky=tk.W, pady=2, padx=20)
        ttk.Label(info_frame, textvariable=self.uploader_var, 
                 foreground=self.colors['primary']).grid(row=0, column=3, sticky=tk.W, pady=2, padx=20)

        # 下载选项区域
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ 下载选项", padding=15)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="格式ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.format_id_var = tk.StringVar(value="bv*+ba/b")
        format_entry = ttk.Entry(options_frame, textvariable=self.format_id_var, width=15,
                                font=('Microsoft YaHei UI', 10))
        format_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        format_entry.bind("<Button-1>", lambda e: self.query_formats())
        
        ttk.Button(options_frame, text="查询格式", command=self.query_formats).grid(row=0, column=2, padx=5)

        self.subtitle_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="下载字幕", variable=self.subtitle_var).grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)

        ttk.Label(options_frame, text="线程数:").grid(row=0, column=4, sticky=tk.W, pady=5)
        self.threads_var = tk.StringVar(value="4")
        ttk.Combobox(options_frame, textvariable=self.threads_var, values=["1", "2", "4", "8", "16"], 
                    width=5, font=('Microsoft YaHei UI', 10)).grid(row=0, column=5, sticky=tk.W, pady=5, padx=5)

        self.transcode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="转码", variable=self.transcode_var).grid(row=0, column=6, sticky=tk.W, pady=5, padx=5)
        self.transcode_format = tk.StringVar(value="mp4")
        ttk.Combobox(options_frame, textvariable=self.transcode_format, 
                    values=["mp4", "mkv", "avi", "mov", "webm"], width=8,
                    font=('Microsoft YaHei UI', 10)).grid(row=0, column=7, sticky=tk.W, pady=5, padx=5)

        # 控制按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)

        ttk.Button(button_frame, text="🚀 开始下载", command=self.start_download, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⏹️ 终止下载", command=self.stop_download, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ 清空日志", command=self.clear_logs, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📚 查看历史", command=self.show_history, width=15).pack(side=tk.LEFT, padx=5)

        # 下载进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="📊 下载进度", padding=15)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="准备就绪", 
                                       foreground=self.colors['primary'])
        self.progress_label.pack(anchor=tk.W, pady=2)

        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', 
                                           mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # 信息窗口日志区域
        log_frame = ttk.LabelFrame(main_frame, text="📝 信息日志", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10,
                                                 font=('Microsoft YaHei UI', 9),
                                                 bg=self.colors['card_bg'])
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # 配置日志颜色标签
        self.log_text.tag_configure("error", foreground=self.colors['accent'])
        self.log_text.tag_configure("success", foreground=self.colors['secondary'])
        self.log_text.tag_configure("info", foreground=self.colors['primary'])
        self.log_text.tag_configure("progress", foreground=self.colors['text_secondary'])

    def toggle_topmost(self):
        """切换窗口置顶状态"""
        self.is_topmost = not self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)
        self.topmost_button.config(text="📌" if self.is_topmost else "📍")

    def center_child_window(self, child_window, width, height):
        """将子窗口居中显示在主窗口上方"""
        # 获取主窗口位置和大小
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        # 计算子窗口位置
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2
        
        child_window.geometry(f"{width}x{height}+{x}+{y}")

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
                ydl_opts = {
                    'socket_timeout': 10,
                    'proxy': proxy,
                    'quiet': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)

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
                views_str = f"{views:,}"

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
                ydl_opts = {
                    'socket_timeout': 10,
                    'proxy': proxy,
                    'quiet': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    formats = info_dict.get('formats', [info_dict])

                # 在主线程中显示格式选择窗口
                self.root.after(0, lambda: self.show_format_selection_window(info_dict, formats))

            except Exception as e:
                self.result_queue.put(("error", f"查询格式失败: {str(e)}"))

        # 在单独线程中查询格式
        threading.Thread(target=_query, daemon=True).start()

    def show_format_selection_window(self, info_dict, formats):
        """显示格式选择窗口"""
        format_window = tk.Toplevel(self.root)
        format_window.title(f"格式选择 - {info_dict.get('title', '未知视频')}")
        format_window.configure(bg=self.colors['bg'])
        
        # 设置窗口大小并居中
        self.center_child_window(format_window, 900, 600)
        format_window.resizable(True, True)
        format_window.transient(self.root)
        format_window.grab_set()

        # 主框架
        main_frame = ttk.Frame(format_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, 
                               text=f"可用格式 - {info_dict.get('title', '未知视频')[:50]}...",
                               font=('Microsoft YaHei UI', 14, 'bold'),
                               foreground=self.colors['primary'])
        title_label.pack(pady=(0, 15))

        # 创建表格框架
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 创建Treeview表格
        columns = ("格式ID", "扩展名", "分辨率", "帧率", "音频编码", "视频编码", "文件大小")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # 设置列标题和宽度
        for col in columns:
            tree.heading(col, text=col)
            if col == "格式ID":
                tree.column(col, width=80)
            elif col == "扩展名":
                tree.column(col, width=80)
            elif col == "分辨率":
                tree.column(col, width=100)
            elif col == "帧率":
                tree.column(col, width=60)
            elif col == "音频编码":
                tree.column(col, width=100)
            elif col == "视频编码":
                tree.column(col, width=100)
            elif col == "文件大小":
                tree.column(col, width=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充格式数据
        best_video = None
        best_audio = None

        for f in formats:
            format_id = f.get('format_id', '?')
            ext = f.get('ext', '?')
            resolution = f.get('resolution', '?')
            if resolution == '?' and f.get('height'):
                resolution = f"{f.get('height')}p"
            fps = f.get('fps', '?')
            acodec = f.get('acodec', '?')
            vcodec = f.get('vcodec', '?')
            filesize = f.get('filesize')
            if filesize:
                filesize = f"{filesize / (1024*1024):.1f}MB"
            else:
                filesize = "未知"

            tree.insert("", "end", values=(format_id, ext, resolution, fps, acodec, vcodec, filesize))

            # 寻找最佳格式
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                height = f.get('height')
                if height is not None and f.get('filesize') is not None:
                    if best_video is None or height > best_video.get('height', 0):
                        best_video = f

            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                abr = f.get('abr')
                if abr is not None and f.get('filesize') is not None:
                    if best_audio is None or abr > best_audio.get('abr', 0):
                        best_audio = f

        # 推荐格式
        recommended_format = "bv*+ba/b"
        if best_video and best_audio:
            recommended_format = f"{best_video['format_id']}+{best_audio['format_id']}"

        # 推荐信息
        recommend_frame = ttk.Frame(main_frame)
        recommend_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(recommend_frame, 
                 text=f"推荐格式: {recommended_format} (最佳视频+最佳音频)",
                 font=('Microsoft YaHei UI', 11, 'bold'),
                 foreground=self.colors['secondary']).pack(anchor=tk.W)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        def use_recommended():
            self.format_id_var.set(recommended_format)
            format_window.destroy()

        def use_selected():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                format_id = item['values'][0]
                self.format_id_var.set(format_id)
                format_window.destroy()
            else:
                messagebox.showwarning("提示", "请先选择一个格式")

        ttk.Button(button_frame, text="使用推荐格式", command=use_recommended).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="使用选中格式", command=use_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=format_window.destroy).pack(side=tk.RIGHT, padx=5)

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

        # 获取用户输入的格式ID
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

        # 终止当前下载
        if self.ydl_instance:
            self.ydl_instance._download_retcode = -1  # 设置退出码强制终止

        # 等待所有线程结束
        for task_id, thread in list(self.download_threads.items()):
            if thread.is_alive():
                self.logger.info(f"等待任务 {task_id} 终止...")
                thread.join(timeout=1.0)

        self.is_downloading = False
        self.ydl_instance = None
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

                    # 在单独的线程中执行下载，以便可以独立控制每个任务
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
            # 检查是否需要提取音频
            is_audio = format_id.lower().startswith('audio') or format_id == 'bestaudio'

            # 检查ffmpeg是否可用（如果需要合并格式或提取音频）
            needs_ffmpeg = (
                '+' in format_id or  # 格式包含+表示需要合并
                (format_id.lower().startswith('audio') or format_id == 'bestaudio')  # 音频提取需要ffmpeg
            )

            if needs_ffmpeg and not self.check_ffmpeg():
                raise RuntimeError("需要ffmpeg来合并格式或提取音频，但未找到ffmpeg。请安装ffmpeg并确保其在系统PATH中。")

            ydl_opts = {
                'format': format_id,
                'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                'noplaylist': True,
                'continuedl': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 10,
                'proxy': proxy,
                'concurrent_fragments': thread_count,
                'progress_hooks': [self._download_hook],
                'logger': self.logger,
                'writesubtitles': download_subtitles,
                'writeautomaticsub': download_subtitles,
                'subtitleslangs': ['en', 'zh-Hans', 'zh-Hant'],  # 下载多种语言字幕
            }

            # 如果是音频下载，添加音频处理选项
            if is_audio:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3' if format_id == 'bestaudio' else 'best',
                    'preferredquality': '192',
                }]

            self.logger.info(f"开始下载到: {save_path}")

            # 更新进度条
            self.update_progress(
                (self.current_task_index-1) / self.total_tasks * 100, 
                f"下载中 {self.current_task_index}/{self.total_tasks}"
            )

            # 保存ydl实例用于终止下载
            self.ydl_instance = yt_dlp.YoutubeDL(ydl_opts)

            # 开始下载
            info_dict = self.ydl_instance.extract_info(url, download=True)

            if self.abort_all_tasks:
                self.result_queue.put(("info", f"下载已取消: {info_dict.get('title')}"))
                return

            self.logger.info(f"下载完成: {info_dict.get('title')}")
            self.update_progress(100, "下载完成")
            self.result_queue.put(("success", f"下载完成: {info_dict.get('title')}"))
            self.update_progress(
                self.current_task_index / self.total_tasks * 100, 
                f"完成 {self.current_task_index}/{self.total_tasks}"
            )

            # 保存下载历史
            self.save_download_history(url, info_dict.get('title'), format_id, save_path)

            # 如果启用了转码，执行转码
            if transcode:
                original_file = f"{save_path}/{info_dict.get('title', 'video')}.{info_dict.get('ext', 'mp4')}"
                transcoded_file = f"{save_path}/{info_dict.get('title', 'video')}.{transcode_format}"

                self.result_queue.put(("info", f"开始转码: {original_file} -> {transcoded_file}"))
                self.transcode_file(original_file, transcoded_file)

        except Exception as e:
            self.logger.error(f"下载失败: {str(e)}")
            self.update_progress(0, "下载失败")
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower() or "FFmpeg" in error_msg:
                self.result_queue.put(("error", f"下载失败: 需要ffmpeg但未安装。请安装ffmpeg并确保其在系统PATH中。"))
            elif 'yt_dlp.utils.DownloadError' in str(type(e)) or 'Network' in error_msg or '403' in error_msg:
                self.result_queue.put(("error", "连接 YouTube 失败，可能是网络限制或无代理所致。"))
            else:
                self.result_queue.put(("error", f"下载失败: {error_msg}"))
        finally:
            self.is_downloading = False
            self.ydl_instance = None
            if task_id in self.download_threads:
                del self.download_threads[task_id]

    def _download_hook(self, d):
        """下载进度回调函数"""
        if self.abort_all_tasks:
            return

        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '?')
            speed = d.get('_speed_str', '?')
            eta = d.get('_eta_str', '?')
            self.result_queue.put(("progress", f"下载中: {percent} 速度: {speed} 剩余时间: {eta}"))

            # 更新进度条
            if '%' in percent:
                try:
                    progress = float(percent.strip('%'))
                    overall_progress = (self.current_task_index-1 + progress/100) / self.total_tasks * 100
                    self.update_progress(overall_progress, f"下载中 {self.current_task_index}/{self.total_tasks}: {percent}")
                except:
                    pass
        elif d['status'] == 'finished':
            self.result_queue.put(("info", "正在处理文件..."))

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
            if os.path.exists("videomaster_history.json"):
                with open("videomaster_history.json", "r", encoding="utf-8") as f:
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

            with open("videomaster_history.json", "w", encoding="utf-8") as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存下载历史失败: {str(e)}")

    def show_history(self):
        """显示下载历史"""
        if not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载历史记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("VideoMaster Pro - 下载历史")
        history_window.configure(bg=self.colors['bg'])
        
        # 设置窗口大小并居中
        self.center_child_window(history_window, 1000, 600)
        history_window.resizable(True, True)
        history_window.transient(self.root)

        # 主框架
        main_frame = ttk.Frame(history_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="📚 下载历史记录",
                               font=('Microsoft YaHei UI', 16, 'bold'),
                               foreground=self.colors['primary'])
        title_label.pack(pady=(0, 15))

        # 创建表格
        columns = ("序号", "标题", "URL", "格式", "保存路径", "时间")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)

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
                entry["title"][:40] + "..." if len(entry["title"]) > 40 else entry["title"],
                entry["url"][:50] + "..." if len(entry["url"]) > 50 else entry["url"],
                entry["format_id"],
                entry["save_path"],
                entry["timestamp"]
            ))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加双击打开文件位置功能
        def open_file_location(event):
            selection = tree.selection()
            if selection:
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
            try:
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.result_queue.put(("error", "转码失败: 未找到ffmpeg。请确保ffmpeg已安装并添加到系统PATH中。"))
                return

            # 构建ffmpeg命令
            cmd = [
                "ffmpeg",
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

    def check_ffmpeg(self):
        """检查系统中是否安装了ffmpeg"""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

def show_splash_screen(root):
    splash = tk.Toplevel(root)
    splash.title("VideoMaster Pro")
    splash.geometry("500x350")
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    splash.configure(bg='#F2F2F7')

    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 500) // 2
    y = (screen_height - 350) // 2
    splash.geometry(f"500x350+{x}+{y}")

    # 主标题
    title_label = tk.Label(splash, text="VideoMaster Pro", 
                          font=('Microsoft YaHei UI', 24, 'bold'), 
                          fg="#007AFF", bg='#F2F2F7')
    title_label.pack(pady=30)

    # 副标题
    subtitle_label = tk.Label(splash, text="专业视频下载大师", 
                             font=('Microsoft YaHei UI', 14), 
                             fg="#8E8E93", bg='#F2F2F7')
    subtitle_label.pack(pady=10)

    # 版本信息
    version_label = tk.Label(splash, text="Version 2.0", 
                            font=('Microsoft YaHei UI', 12), 
                            fg="#8E8E93", bg='#F2F2F7')
    version_label.pack(pady=5)

    # 进度条
    progress = ttk.Progressbar(splash, orient='horizontal', mode='indeterminate', length=350)
    progress.pack(pady=30)
    progress.start(10)

    # 状态标签
    status_label = tk.Label(splash, text="正在启动...", 
                           font=('Microsoft YaHei UI', 11), 
                           fg="#1D1D1F", bg='#F2F2F7')
    status_label.pack(pady=10)

    # 版权信息
    copyright_label = tk.Label(splash, text="© 2025 VideoMaster Pro. All rights reserved.", 
                              font=('Microsoft YaHei UI', 9), 
                              fg="#8E8E93", bg='#F2F2F7')
    copyright_label.pack(side=tk.BOTTOM, pady=20)

    def close_splash():
        progress.stop()
        splash.destroy()
        root.deiconify()
        root.focus_force()  # 强制焦点到主窗口

    root.after(3500, close_splash)

def main():
    root = tk.Tk()
    root.withdraw()
    show_splash_screen(root)
    app = VideoMasterProApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
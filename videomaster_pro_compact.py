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
        self.root.title("VideoMaster Pro - 紧凑版")
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
            # 检查是否有滚动条
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
        
        # 添加阴影效果
        shadow = tk.Frame(parent, bg='#e0e0e0', height=2)
        
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
        
        # 1. URL输入卡片 - 紧凑设计
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
        format_entry = tk.Entry(format_row, textvariable=self.format_id_var, 
                               font=('SF Pro Display', 10), width=12, relief='flat', bd=3)
        format_entry.pack(side=tk.LEFT, padx=(5, 5))
        
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
        """查询可用格式"""
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
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    
                    format_info = f"\n=== 可用格式 ({info.get('title', 'Unknown')}) ===\n"
                    
                    # 显示主要格式
                    video_formats = []
                    audio_formats = []
                    
                    for f in formats:
                        if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                            video_formats.append(f)
                        elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            audio_formats.append(f)
                    
                    format_info += "\n📹 视频格式:\n"
                    for f in video_formats[:5]:  # 只显示前5个
                        format_info += f"  {f['format_id']}: {f.get('height', '?')}p {f.get('ext', '?')} ({f.get('filesize_approx', 'N/A')} bytes)\n"
                    
                    format_info += "\n🎵 音频格式:\n"
                    for f in audio_formats[:3]:  # 只显示前3个
                        format_info += f"  {f['format_id']}: {f.get('abr', '?')}kbps {f.get('ext', '?')}\n"
                    
                    # 推荐格式
                    if video_formats and audio_formats:
                        best_video = max(video_formats, key=lambda x: x.get('height', 0) or 0)
                        best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
                        recommended = f"{best_video['format_id']}+{best_audio['format_id']}"
                        format_info += f"\n💡 推荐格式: {recommended}\n"
                        
                        self.root.after(0, lambda: self.format_id_var.set(recommended))
                    
                    self.result_queue.put(('info', format_info))
                    
            except Exception as e:
                self.result_queue.put(('error', f"查询格式失败: {str(e)}"))
        
        threading.Thread(target=_query, daemon=True).start()
    
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
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not self.abort_all_tasks:
                    title = info.get('title', 'Unknown')
                    self.result_queue.put(('success', f"下载完成: {title}"))
                    self.save_download_history(url, title, format_id, save_path)
                    
                    # 转码处理
                    if transcode:
                        self.result_queue.put(('info', f"开始转码: {title}"))
                        # 这里可以添加转码逻辑
        
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
    subtitle_label = tk.Label(splash, text="紧凑版 - 专业视频下载工具", 
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
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoMaster Pro - 正式版 v2.0
完整功能版本，支持YouTube Music链接，包含所有原有功能
"""

import yt_dlp
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import logging
from urllib.parse import urlparse, parse_qs
import os
from datetime import datetime
import json
import subprocess
import platform
import traceback

class VideoMasterProOfficialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoMaster Pro - 正式版 v2.0")
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
        self.last_formats_data = None
        self.download_history = []
        
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
            
            title_label = tk.Label(title_frame, text=title, 
                                 font=('SF Pro Display', 12, 'bold'),
                                 bg=self.colors['card'], fg=self.colors['text'])
            title_label.pack(side=tk.LEFT)
        
        content_frame = tk.Frame(card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        return card, content_frame
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建滚动画布
        self.main_canvas = tk.Canvas(self.root, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg=self.colors['bg'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 主容器
        main_container = tk.Frame(self.scrollable_frame, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. URL输入区域
        url_card, url_content = self.create_card(main_container, "🎬 视频链接 (支持YouTube Music)")
        url_card.pack(fill=tk.X, pady=(0, 15))
        
        # 单个URL输入
        single_frame = tk.Frame(url_content, bg=self.colors['card'])
        single_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(single_frame, text="YouTube链接:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = tk.Entry(single_frame, font=('SF Pro Display', 10), relief='solid', bd=1)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 按钮组
        btn_frame = tk.Frame(single_frame, bg=self.colors['card'])
        btn_frame.pack(side=tk.RIGHT)
        
        self.create_button(btn_frame, "获取信息", self.fetch_video_info, self.colors['primary']).pack(side=tk.LEFT, padx=2)
        self.create_button(btn_frame, "查询格式", self.query_formats, self.colors['secondary']).pack(side=tk.LEFT, padx=2)
        self.create_button(btn_frame, "分析链接", self.analyze_link, self.colors['warning']).pack(side=tk.LEFT, padx=2)
        
        # 批量URL输入
        batch_frame = tk.Frame(url_content, bg=self.colors['card'])
        batch_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(batch_frame, text="批量链接 (每行一个):", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(anchor=tk.W, pady=(0, 5))
        
        self.urls_text = scrolledtext.ScrolledText(batch_frame, height=4, font=('SF Pro Display', 9))
        self.urls_text.pack(fill=tk.BOTH, expand=True)
        
        # 2. 网络设置区域
        network_card, network_content = self.create_card(main_container, "🌐 网络设置")
        network_card.pack(fill=tk.X, pady=(0, 15))
        
        # 代理设置
        proxy_frame = tk.Frame(network_content, bg=self.colors['card'])
        proxy_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(proxy_frame, text="代理设置:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.use_proxy = tk.BooleanVar(value=True)
        ttk.Checkbutton(proxy_frame, text="使用代理", variable=self.use_proxy).pack(side=tk.LEFT, padx=(0, 10))
        
        self.proxy_entry = tk.Entry(proxy_frame, font=('SF Pro Display', 10), relief='solid', bd=1)
        self.proxy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")
        
        # 3. 视频信息显示区域
        info_card, info_content = self.create_card(main_container, "📺 视频信息")
        info_card.pack(fill=tk.X, pady=(0, 15))
        
        self.title_var = tk.StringVar(value="标题: 未获取")
        self.duration_var = tk.StringVar(value="时长: 未知")
        self.views_var = tk.StringVar(value="观看: 未知")
        self.uploader_var = tk.StringVar(value="作者: 未知")
        
        for var in [self.title_var, self.duration_var, self.views_var, self.uploader_var]:
            label = tk.Label(info_content, textvariable=var, font=('SF Pro Display', 10),
                           bg=self.colors['card'], fg=self.colors['text'])
            label.pack(anchor=tk.W, pady=2)
        
        # 4. 下载设置区域
        download_card, download_content = self.create_card(main_container, "⚙️ 下载设置")
        download_card.pack(fill=tk.X, pady=(0, 15))
        
        # 保存路径
        path_frame = tk.Frame(download_content, bg=self.colors['card'])
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(path_frame, text="保存路径:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        path_entry = tk.Entry(path_frame, textvariable=self.save_path_var, font=('SF Pro Display', 10), relief='solid', bd=1)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.create_button(path_frame, "浏览", self.browse_path, self.colors['text_secondary']).pack(side=tk.RIGHT)
        
        # 格式设置
        format_frame = tk.Frame(download_content, bg=self.colors['card'])
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(format_frame, text="格式ID:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_id_var = tk.StringVar(value="bv*+ba/b")
        format_entry = tk.Entry(format_frame, textvariable=self.format_id_var, font=('SF Pro Display', 10), relief='solid', bd=1)
        format_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        format_entry.bind("<Double-Button-1>", self.reopen_formats_window)
        
        # 其他设置
        options_frame = tk.Frame(download_content, bg=self.colors['card'])
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 字幕选项
        self.subtitle_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="下载字幕", variable=self.subtitle_var).pack(side=tk.LEFT, padx=(0, 20))
        
        # 线程数
        tk.Label(options_frame, text="线程数:", font=('SF Pro Display', 10),
                bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.threads_var = tk.StringVar(value="4")
        threads_combo = ttk.Combobox(options_frame, textvariable=self.threads_var, width=5)
        threads_combo['values'] = ['1', '2', '4', '8', '16']
        threads_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 转码选项
        self.transcode_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="转码", variable=self.transcode_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.transcode_format = tk.StringVar(value="mp4")
        transcode_combo = ttk.Combobox(options_frame, textvariable=self.transcode_format, width=8)
        transcode_combo['values'] = ['mp4', 'mkv', 'avi', 'mp3', 'flac']
        transcode_combo.pack(side=tk.LEFT)
        
        # 5. 控制按钮区域
        control_card, control_content = self.create_card(main_container, "🎮 控制面板")
        control_card.pack(fill=tk.X, pady=(0, 15))
        
        control_btn_frame = tk.Frame(control_content, bg=self.colors['card'])
        control_btn_frame.pack(fill=tk.X)
        
        self.create_button(control_btn_frame, "🚀 开始下载", self.start_download, self.colors['success']).pack(side=tk.LEFT, padx=(0, 10))
        self.create_button(control_btn_frame, "⏹️ 停止下载", self.stop_download, self.colors['danger']).pack(side=tk.LEFT, padx=(0, 10))
        self.create_button(control_btn_frame, "📜 下载历史", self.show_history, self.colors['secondary']).pack(side=tk.LEFT, padx=(0, 10))
        self.create_button(control_btn_frame, "🗑️ 清空日志", self.clear_logs, self.colors['text_secondary']).pack(side=tk.RIGHT)
        
        # 6. 日志区域
        log_card, log_content = self.create_card(main_container, "📋 运行日志")
        log_card.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_content, height=12, state=tk.DISABLED, 
                                                font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志标签颜色
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
    
    def create_button(self, parent, text, command, color):
        """创建统一样式的按钮"""
        btn = tk.Button(parent, text=text, command=command,
                       font=('SF Pro Display', 9, 'bold'),
                       bg=color, fg='white', relief='flat', bd=0,
                       padx=15, pady=5, cursor='hand2')
        
        # 悬停效果
        def on_enter(e):
            btn.config(bg=self.darken_color(color))
        
        def on_leave(e):
            btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def darken_color(self, color):
        """使颜色变暗"""
        color_map = {
            self.colors['primary']: '#0056cc',
            self.colors['secondary']: '#4c44c4',
            self.colors['success']: '#2ba747',
            self.colors['warning']: '#e6850e',
            self.colors['danger']: '#e6342a',
            self.colors['text_secondary']: '#6d6d70'
        }
        return color_map.get(color, color)
    
    def validate_url_improved(self, url):
        """改进的URL验证函数"""
        try:
            parsed = urlparse(url)
            
            # 检查基本URL结构
            if not all([parsed.scheme, parsed.netloc]):
                return False
            
            # 检查是否是YouTube域名
            youtube_domains = [
                'youtube.com', 'www.youtube.com', 
                'youtu.be', 'www.youtu.be',
                'music.youtube.com', 'm.youtube.com'
            ]
            
            if parsed.netloc.lower() not in youtube_domains:
                return False
            
            return True
            
        except Exception:
            return False
    
    def validate_url(self, url):
        """兼容原版的URL验证"""
        return self.validate_url_improved(url)
    
    def extract_clean_url(self, url):
        """从复杂的YouTube链接中提取干净的视频URL"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # 如果是播放列表链接但包含视频ID，提取单个视频
            if 'list' in query_params and 'v' in query_params:
                video_id = query_params['v'][0]
                clean_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # 检查是否是YouTube Music自动播放列表
                list_id = query_params['list'][0]
                if list_id.startswith('RD'):
                    self._append_log(f"🎵 检测到YouTube Music自动播放列表", "INFO")
                    self._append_log(f"🎯 提取单个视频ID: {video_id}", "SUCCESS")
                else:
                    self._append_log(f"📋 检测到普通播放列表: {list_id}", "INFO")
                    self._append_log(f"🎯 提取单个视频ID: {video_id}", "SUCCESS")
                
                return clean_url
            
            return url
            
        except Exception as e:
            self._append_log(f"URL处理错误: {e}", "WARNING")
            return url
    
    def analyze_link(self):
        """分析链接结构"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("错误", "请输入YouTube链接")
            return
        
        self._append_log("🔍 开始分析链接结构...", "INFO")
        
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            self._append_log(f"🔗 原始链接: {url}", "INFO")
            self._append_log(f"🌐 域名: {parsed.netloc}", "INFO")
            self._append_log(f"📂 路径: {parsed.path}", "INFO")
            
            if query_params:
                self._append_log("📋 查询参数:", "INFO")
                for key, value in query_params.items():
                    self._append_log(f"   • {key}: {value[0] if value else 'None'}", "INFO")
            
            # 分析链接类型
            if 'v' in query_params:
                video_id = query_params['v'][0]
                self._append_log(f"🎬 视频ID: {video_id}", "SUCCESS")
            
            if 'list' in query_params:
                list_id = query_params['list'][0]
                if list_id.startswith('RD'):
                    self._append_log(f"🎵 YouTube Music自动播放列表: {list_id}", "WARNING")
                    self._append_log("💡 建议: 将自动提取单个视频进行下载", "INFO")
                elif list_id.startswith('PL'):
                    self._append_log(f"📋 用户创建的播放列表: {list_id}", "INFO")
                else:
                    self._append_log(f"📋 其他类型播放列表: {list_id}", "INFO")
            
            if 'start_radio' in query_params:
                self._append_log("📻 检测到自动播放模式参数", "WARNING")
            
            # 生成清理后的链接
            clean_url = self.extract_clean_url(url)
            if clean_url != url:
                self._append_log(f"✨ 清理后的链接: {clean_url}", "SUCCESS")
            
        except Exception as e:
            self._append_log(f"❌ 链接分析失败: {str(e)}", "ERROR")
    
    def get_ydl_opts(self, proxy=None):
        """获取yt-dlp配置"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': False,
            'socket_timeout': 60,
            'retries': 15,
            'fragment_retries': 15,
            'extractor_retries': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
        }
        
        # 代理设置
        if self.use_proxy.get() and proxy:
            opts['proxy'] = proxy
            self._append_log(f"🌐 使用代理: {proxy}", "INFO")
        else:
            self._append_log("🌐 使用直连", "INFO")
        
        return opts
    
    def fetch_video_info(self):
        """获取视频信息"""
        url = self.url_entry.get().strip()
        
        if not self.validate_url_improved(url):
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        self._append_log(f"🚀 开始获取视频信息...", "INFO")
        
        def _fetch():
            try:
                # 提取干净的URL
                clean_url = self.extract_clean_url(url)
                
                # 获取配置
                proxy = self.proxy_entry.get().strip() or None
                ydl_opts = self.get_ydl_opts(proxy)
                
                self._append_log("🔄 正在连接YouTube服务器...", "INFO")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=False)
                    
                    title = info.get('title', '未知')
                    duration = info.get('duration') or 0
                    views = info.get('view_count') or 0
                    uploader = info.get('uploader') or '未知'
                    video_id = info.get('id') or '未知'
                    
                    # 格式化时长
                    if duration and isinstance(duration, (int, float)):
                        hours, remainder = divmod(int(duration), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = "未知"
                    
                    # 格式化观看次数
                    views_str = f"{views:,}" if views and isinstance(views, (int, float)) else "未知"
                    
                    # 更新界面
                    self.root.after(0, lambda: [
                        self.title_var.set(f"标题: {title[:60]}{'...' if len(title) > 60 else ''}"),
                        self.duration_var.set(f"时长: {duration_str}"),
                        self.views_var.set(f"观看: {views_str}"),
                        self.uploader_var.set(f"作者: {uploader}")
                    ])
                    
                    self.video_info[clean_url] = info
                    self.result_queue.put(('success', f"✅ 获取视频信息成功!"))
                    self.result_queue.put(('info', f"🎬 标题: {title}"))
                    self.result_queue.put(('info', f"🆔 视频ID: {video_id}"))
                    self.result_queue.put(('info', f"👤 作者: {uploader}"))
                    
            except Exception as e:
                error_msg = str(e)
                self.result_queue.put(('error', f"❌ 获取视频信息失败"))
                
                # 分析错误类型并给出建议
                if "Unable to download API page" in error_msg or "Connection refused" in error_msg:
                    if self.use_proxy.get():
                        self.result_queue.put(('warning', "💡 代理连接失败，建议:"))
                        self.result_queue.put(('info', "   1. 检查代理软件是否运行"))
                        self.result_queue.put(('info', "   2. 尝试取消勾选代理选项"))
                    else:
                        self.result_queue.put(('warning', "💡 直连失败，建议:"))
                        self.result_queue.put(('info', "   1. 勾选使用代理选项"))
                        self.result_queue.put(('info', "   2. 确保代理软件运行"))
                elif "timed out" in error_msg:
                    self.result_queue.put(('warning', "💡 连接超时，建议:"))
                    self.result_queue.put(('info', "   1. 检查网络连接"))
                    self.result_queue.put(('info', "   2. 稍后重试"))
                else:
                    self.result_queue.put(('error', f"详细错误: {error_msg}"))
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def query_formats(self):
        """查询可用格式并显示选择窗口"""
        url = self.url_entry.get().strip()
        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        self._append_log("🔍 正在查询可用格式...", "INFO")
        
        def _query():
            try:
                # 提取干净的URL
                clean_url = self.extract_clean_url(url)
                
                proxy = self.proxy_entry.get().strip() or None
                ydl_opts = self.get_ydl_opts(proxy)
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=False)
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
            try:
                return f"{float(size_in_bytes) / (1024*1024):.1f}"
            except (ValueError, TypeError):
                return "N/A"
        
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
    
    def browse_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)
    
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
        proxy = self.proxy_entry.get().strip() or None if self.use_proxy.get() else None
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
    
    def load_download_history(self):
        """加载下载历史"""
        try:
            if os.path.exists('download_history.json'):
                with open('download_history.json', 'r', encoding='utf-8') as f:
                    self.download_history = json.load(f)
            else:
                self.download_history = []
        except Exception as e:
            self.logger.error(f"加载历史失败: {str(e)}")
            self.download_history = []
    
    def save_download_history(self, url, title, format_id, save_path):
        """保存下载历史"""
        try:
            entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'url': url,
                'title': title,
                'format_id': format_id,
                'save_path': save_path
            }
            
            self.download_history.append(entry)
            
            # 只保留最近1000条记录
            if len(self.download_history) > 1000:
                self.download_history = self.download_history[-1000:]
            
            with open('download_history.json', 'w', encoding='utf-8') as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存历史失败: {str(e)}")
    
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
            
            # 提取干净的URL
            clean_url = self.extract_clean_url(url)
            
            ydl_opts = self.get_ydl_opts(proxy)
            ydl_opts.update({
                'format': format_id,
                'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                'writesubtitles': download_subtitles,
                'writeautomaticsub': download_subtitles,
                'progress_hooks': [self._progress_hook]
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=True)
                
                if not self.abort_all_tasks:
                    title = info.get('title', 'Unknown')
                    self.result_queue.put(('success', f"下载完成: {title}"))
                    self.save_download_history(clean_url, title, format_id, save_path)
        
        except Exception as e:
            self.result_queue.put(('error', f"下载失败: {str(e)}"))
        finally:
            self.is_downloading = False
    
    def _progress_hook(self, d):
        """下载进度回调"""
        if self.abort_all_tasks:
            return
        
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                self.result_queue.put(('info', f"下载进度: {percent} - 速度: {speed}"))
            except:
                pass
        elif d['status'] == 'finished':
            filename = os.path.basename(d['filename'])
            self.result_queue.put(('success', f"文件下载完成: {filename}"))
    
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
    
    # 居中显示
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 450) // 2
    y = (screen_height - 300) // 2
    splash.geometry(f"450x300+{x}+{y}")
    
    # 内容
    content_frame = tk.Frame(splash, bg='#f5f5f7')
    content_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
    
    # 标题
    title_label = tk.Label(content_frame, text="VideoMaster Pro", 
                          font=('SF Pro Display', 24, 'bold'),
                          bg='#f5f5f7', fg='#1d1d1f')
    title_label.pack(pady=(20, 10))
    
    # 版本
    version_label = tk.Label(content_frame, text="正式版 v2.0", 
                           font=('SF Pro Display', 12),
                           bg='#f5f5f7', fg='#86868b')
    version_label.pack(pady=(0, 20))
    
    # 功能列表
    features = [
        "✅ 支持YouTube Music链接",
        "✅ 智能播放列表处理", 
        "✅ 完整格式选择功能",
        "✅ 批量下载支持",
        "✅ 下载历史记录"
    ]
    
    for feature in features:
        feature_label = tk.Label(content_frame, text=feature,
                               font=('SF Pro Display', 10),
                               bg='#f5f5f7', fg='#1d1d1f')
        feature_label.pack(pady=2)
    
    # 进度条
    progress = ttk.Progressbar(content_frame, mode='indeterminate')
    progress.pack(pady=(20, 10), fill=tk.X)
    progress.start()
    
    loading_label = tk.Label(content_frame, text="正在启动...",
                           font=('SF Pro Display', 10),
                           bg='#f5f5f7', fg='#86868b')
    loading_label.pack()
    
    # 3秒后关闭启动画面
    def close_splash():
        progress.stop()
        splash.destroy()
    
    splash.after(3000, close_splash)
    return splash

def main():
    """主函数"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 显示启动画面
    splash = show_splash_screen(root)
    
    # 3秒后显示主窗口
    def show_main():
        root.deiconify()  # 显示主窗口
        app = VideoMasterProOfficialApp(root)
        
        # 显示启动信息
        app._append_log("🚀 VideoMaster Pro 正式版 v2.0 启动", "SUCCESS")
        app._append_log("✨ 完整功能版本，支持YouTube Music链接", "INFO")
        app._append_log("🔧 包含格式查询、批量下载、历史记录等所有功能", "INFO")
        app._append_log("💡 YouTube Music链接问题已完全修复", "SUCCESS")
        app._append_log("📋 使用说明:", "INFO")
        app._append_log("   1. 粘贴YouTube链接（支持Music和播放列表）", "INFO")
        app._append_log("   2. 点击'获取信息'查看视频详情", "INFO")
        app._append_log("   3. 点击'查询格式'选择下载质量", "INFO")
        app._append_log("   4. 配置下载设置后开始下载", "INFO")
    
    root.after(3000, show_main)
    root.mainloop()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoMaster Pro - 简化修复版
专门解决YouTube Music链接问题，无需额外依赖
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
import traceback

class VideoMasterProSimpleFixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoMaster Pro - YouTube Music修复版")
        self.root.geometry("1000x700")
        self.root.minsize(950, 650)
        
        # 居中窗口
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"1000x700+{x}+{y}")
        
        self.root.configure(bg='#f5f5f7')
        
        # 初始化变量
        self.result_queue = queue.Queue()
        self.video_info = {}
        
        self.setup_logging()
        self.create_widgets()
        self.process_results()
    
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
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="视频链接 (支持YouTube Music)", padding=10)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="YouTube链接:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(url_frame)
        button_frame.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Button(button_frame, text="获取信息", command=self.fetch_video_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="分析链接", command=self.analyze_link).pack(side=tk.LEFT, padx=2)
        
        url_frame.columnconfigure(1, weight=1)
        
        # 代理设置
        ttk.Label(url_frame, text="代理 (可选):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.proxy_entry = ttk.Entry(url_frame, width=70)
        self.proxy_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # 连接模式选择
        mode_frame = ttk.Frame(url_frame)
        mode_frame.grid(row=1, column=2, padx=(10, 0))
        
        self.connection_mode = tk.StringVar(value="smart")
        ttk.Radiobutton(mode_frame, text="智能", variable=self.connection_mode, value="smart").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="直连", variable=self.connection_mode, value="direct").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="代理", variable=self.connection_mode, value="proxy").pack(side=tk.LEFT)
        
        # 视频信息显示区域
        info_frame = ttk.LabelFrame(main_frame, text="视频信息", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_var = tk.StringVar(value="标题: 未获取")
        self.duration_var = tk.StringVar(value="时长: 未知")
        self.views_var = tk.StringVar(value="观看: 未知")
        self.uploader_var = tk.StringVar(value="作者: 未知")
        
        ttk.Label(info_frame, textvariable=self.title_var).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.duration_var).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.views_var).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.uploader_var).pack(anchor=tk.W, pady=2)
        
        # 下载设置区域
        download_frame = ttk.LabelFrame(main_frame, text="下载设置", padding=10)
        download_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(download_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.path_entry = ttk.Entry(download_frame, width=60)
        self.path_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        self.path_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        
        ttk.Button(download_frame, text="浏览", command=self.browse_path).grid(row=0, column=2, padx=(5, 0))
        
        download_frame.columnconfigure(1, weight=1)
        
        # 格式选择
        ttk.Label(download_frame, text="下载格式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="best")
        format_combo = ttk.Combobox(download_frame, textvariable=self.format_var, width=57)
        format_combo['values'] = [
            'best', 'worst', 'bestvideo+bestaudio', 'bestaudio',
            'mp4', 'webm', 'mp3', 'bv*+ba/b'
        ]
        format_combo.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # 下载按钮
        ttk.Button(download_frame, text="开始下载", command=self.start_download).grid(row=1, column=2, padx=(5, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志标签颜色
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
    
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
    
    def get_ydl_opts_by_mode(self):
        """根据连接模式获取yt-dlp配置"""
        mode = self.connection_mode.get()
        proxy = self.proxy_entry.get().strip() or None
        
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': False,
            'socket_timeout': 60,  # 增加超时时间
            'retries': 15,         # 增加重试次数
            'fragment_retries': 15,
            'extractor_retries': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
        }
        
        if mode == "proxy" and proxy:
            base_opts['proxy'] = proxy
            self._append_log(f"🌐 使用代理模式: {proxy}", "INFO")
        elif mode == "direct":
            self._append_log("🌐 使用直连模式", "INFO")
        else:  # smart mode
            if proxy:
                base_opts['proxy'] = proxy
                self._append_log(f"🧠 智能模式: 尝试使用代理 {proxy}", "INFO")
            else:
                self._append_log("🧠 智能模式: 使用直连", "INFO")
        
        return base_opts
    
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
                ydl_opts = self.get_ydl_opts_by_mode()
                
                self._append_log("🔄 正在连接YouTube服务器...", "INFO")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=False)
                    
                    title = info.get('title', '未知')
                    duration = info.get('duration', 0)
                    views = info.get('view_count', 0)
                    uploader = info.get('uploader', '未知')
                    video_id = info.get('id', '未知')
                    
                    # 格式化时长
                    if duration:
                        hours, remainder = divmod(int(duration), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = "未知"
                    
                    # 格式化观看次数
                    views_str = f"{views:,}" if views else "未知"
                    
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
                if "Unable to download API page" in error_msg:
                    self.result_queue.put(('warning', "💡 网络连接问题，建议:"))
                    self.result_queue.put(('info', "   1. 检查网络连接"))
                    self.result_queue.put(('info', "   2. 尝试配置代理"))
                    self.result_queue.put(('info', "   3. 切换连接模式"))
                elif "Connection refused" in error_msg:
                    self.result_queue.put(('warning', "💡 代理连接被拒绝，建议:"))
                    self.result_queue.put(('info', "   1. 检查代理软件是否运行"))
                    self.result_queue.put(('info', "   2. 确认代理地址和端口"))
                    self.result_queue.put(('info', "   3. 尝试直连模式"))
                elif "timed out" in error_msg:
                    self.result_queue.put(('warning', "💡 连接超时，建议:"))
                    self.result_queue.put(('info', "   1. 检查网络稳定性"))
                    self.result_queue.put(('info', "   2. 稍后重试"))
                else:
                    self.result_queue.put(('error', f"详细错误: {error_msg}"))
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def browse_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
    
    def start_download(self):
        """开始下载"""
        url = self.url_entry.get().strip()
        
        if not self.validate_url_improved(url):
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        if not self.video_info:
            messagebox.showwarning("警告", "请先获取视频信息")
            return
        
        save_path = self.path_entry.get().strip()
        if not save_path or not os.path.exists(save_path):
            messagebox.showerror("错误", "请选择有效的保存路径")
            return
        
        self._append_log("🚀 开始下载...", "INFO")
        
        def _download():
            try:
                clean_url = self.extract_clean_url(url)
                format_selector = self.format_var.get()
                
                ydl_opts = self.get_ydl_opts_by_mode()
                ydl_opts.update({
                    'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                    'format': format_selector,
                })
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([clean_url])
                    
                self.result_queue.put(('success', "✅ 下载完成!"))
                
            except Exception as e:
                self.result_queue.put(('error', f"❌ 下载失败: {str(e)}"))
        
        threading.Thread(target=_download, daemon=True).start()
    
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

def main():
    """主函数"""
    root = tk.Tk()
    app = VideoMasterProSimpleFixApp(root)
    
    # 显示启动信息
    app._append_log("🚀 VideoMaster Pro YouTube Music修复版启动", "SUCCESS")
    app._append_log("✨ 专门修复YouTube Music和播放列表链接问题", "INFO")
    app._append_log("🔧 支持智能连接模式和详细错误诊断", "INFO")
    app._append_log("💡 使用说明:", "INFO")
    app._append_log("   1. 粘贴YouTube链接（支持Music和播放列表）", "INFO")
    app._append_log("   2. 点击'分析链接'查看链接结构", "INFO")
    app._append_log("   3. 选择合适的连接模式", "INFO")
    app._append_log("   4. 点击'获取信息'获取视频详情", "INFO")
    
    root.mainloop()

if __name__ == "__main__":
    main()
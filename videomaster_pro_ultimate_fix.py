#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoMaster Pro - 终极修复版
解决YouTube Music链接和网络连接问题的完整解决方案
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
import requests
import time

class VideoMasterProUltimateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VideoMaster Pro - 终极修复版")
        self.root.geometry("1000x750")
        self.root.minsize(950, 700)
        
        # 居中窗口
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 750) // 2
        self.root.geometry(f"1000x750+{x}+{y}")
        
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
        self.video_info = {}
        self.is_downloading = False
        
        self.setup_logging()
        self.create_widgets()
        
        # 启动结果处理
        self.process_results()
        
        # 启动时检查网络
        self.check_network_on_startup()
    
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
        url_frame = ttk.LabelFrame(main_frame, text="视频链接", padding=10)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="YouTube链接:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")
        
        # 按钮区域
        button_frame = ttk.Frame(url_frame)
        button_frame.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Button(button_frame, text="获取信息", command=self.fetch_video_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="网络诊断", command=self.network_diagnosis).pack(side=tk.LEFT, padx=2)
        
        url_frame.columnconfigure(1, weight=1)
        
        # 网络设置区域
        network_frame = ttk.LabelFrame(main_frame, text="网络设置", padding=10)
        network_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 代理设置
        ttk.Label(network_frame, text="代理设置:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.proxy_var = tk.StringVar(value="auto")
        proxy_combo = ttk.Combobox(network_frame, textvariable=self.proxy_var, width=67)
        proxy_combo['values'] = [
            'auto', 'none', 
            'http://127.0.0.1:7890', 'http://127.0.0.1:7897',
            'http://127.0.0.1:1080', 'socks5://127.0.0.1:1080'
        ]
        proxy_combo.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        ttk.Button(network_frame, text="测试代理", command=self.test_proxy).grid(row=0, column=2, padx=(5, 0))
        
        network_frame.columnconfigure(1, weight=1)
        
        # 网络状态显示
        self.network_status_var = tk.StringVar(value="网络状态: 检查中...")
        ttk.Label(network_frame, textvariable=self.network_status_var, foreground="blue").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
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
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志标签颜色
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
    
    def check_network_on_startup(self):
        """启动时检查网络连接"""
        def _check():
            try:
                # 测试基本网络连接
                response = requests.get("https://www.google.com", timeout=5)
                if response.status_code == 200:
                    self.root.after(0, lambda: self.network_status_var.set("网络状态: ✅ 直连正常"))
                    self.result_queue.put(('success', "✅ 网络连接正常，可以直接访问YouTube"))
                else:
                    self.root.after(0, lambda: self.network_status_var.set("网络状态: ⚠️ 连接异常"))
            except:
                # 测试是否需要代理
                self.root.after(0, lambda: self.network_status_var.set("网络状态: ❌ 需要代理"))
                self.result_queue.put(('warning', "⚠️ 直连失败，可能需要配置代理"))
        
        threading.Thread(target=_check, daemon=True).start()
    
    def test_proxy(self):
        """测试代理连接"""
        proxy_setting = self.proxy_var.get().strip()
        
        if proxy_setting == 'none':
            self._append_log("🔄 测试直连...", "INFO")
            proxy = None
        elif proxy_setting == 'auto':
            self._append_log("🔄 自动检测最佳连接方式...", "INFO")
            proxy = None
        else:
            self._append_log(f"🔄 测试代理: {proxy_setting}", "INFO")
            proxy = proxy_setting
        
        def _test():
            try:
                proxies = {'http': proxy, 'https': proxy} if proxy else None
                
                # 测试Google连接
                response = requests.get("https://www.google.com", proxies=proxies, timeout=10)
                if response.status_code == 200:
                    self.result_queue.put(('success', f"✅ 代理测试成功: {proxy or '直连'}"))
                    
                    # 测试YouTube连接
                    youtube_response = requests.get("https://www.youtube.com", proxies=proxies, timeout=10)
                    if youtube_response.status_code == 200:
                        self.result_queue.put(('success', "✅ YouTube连接测试成功"))
                        self.root.after(0, lambda: self.network_status_var.set(f"网络状态: ✅ {proxy or '直连'} 可用"))
                    else:
                        self.result_queue.put(('warning', "⚠️ YouTube连接测试失败"))
                else:
                    self.result_queue.put(('error', f"❌ 代理测试失败: {proxy or '直连'}"))
                    
            except Exception as e:
                self.result_queue.put(('error', f"❌ 代理测试失败: {str(e)}"))
        
        threading.Thread(target=_test, daemon=True).start()
    
    def get_working_proxy(self):
        """获取可用的代理设置"""
        proxy_setting = self.proxy_var.get().strip()
        
        if proxy_setting == 'none':
            return None
        elif proxy_setting == 'auto':
            # 自动检测可用代理
            common_proxies = [
                None,  # 直连
                'http://127.0.0.1:7890',
                'http://127.0.0.1:7897',
                'http://127.0.0.1:1080',
                'socks5://127.0.0.1:1080'
            ]
            
            for proxy in common_proxies:
                try:
                    proxies = {'http': proxy, 'https': proxy} if proxy else None
                    response = requests.get("https://www.google.com", proxies=proxies, timeout=5)
                    if response.status_code == 200:
                        self._append_log(f"🎯 自动检测到可用连接: {proxy or '直连'}", "SUCCESS")
                        return proxy
                except:
                    continue
            
            self._append_log("⚠️ 自动检测失败，使用直连", "WARNING")
            return None
        else:
            return proxy_setting
    
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
            
            # 对于YouTube链接，检查是否包含视频ID
            if 'youtube.com' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                # 检查watch页面或embed页面
                if '/watch' in parsed.path and 'v' in query_params:
                    return True
                elif '/embed/' in parsed.path:
                    return True
                elif '/playlist' in parsed.path and 'list' in query_params:
                    return True
            elif 'youtu.be' in parsed.netloc:
                # youtu.be短链接格式
                return len(parsed.path) > 1
            
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
                    self._append_log(f"🎵 检测到YouTube Music自动播放列表，提取视频: {video_id}", "INFO")
                else:
                    self._append_log(f"📋 检测到播放列表，提取单视频: {video_id}", "INFO")
                
                return clean_url
            
            return url
            
        except Exception as e:
            self._append_log(f"URL处理错误: {e}", "WARNING")
            return url
    
    def get_enhanced_ydl_opts(self, proxy=None):
        """获取增强的yt-dlp配置"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': False,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'extractor_retries': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            # YouTube特殊配置
            'cookiefile': None,
            'age_limit': None,
            # 网络优化
            'concurrent_fragment_downloads': 1,
        }
        
        if proxy:
            opts['proxy'] = proxy
        
        return opts
    
    def fetch_video_info(self):
        """修复后的获取视频信息函数"""
        url = self.url_entry.get().strip()
        
        if not self.validate_url_improved(url):
            messagebox.showerror("错误", "请输入有效的YouTube链接")
            return
        
        self._append_log(f"🚀 开始获取视频信息: {url}", "INFO")
        
        def _fetch():
            try:
                # 提取干净的URL
                clean_url = self.extract_clean_url(url)
                
                # 获取可用代理
                proxy = self.get_working_proxy()
                if proxy:
                    self._append_log(f"🌐 使用代理: {proxy}", "INFO")
                else:
                    self._append_log("🌐 使用直连", "INFO")
                
                # 使用增强配置
                ydl_opts = self.get_enhanced_ydl_opts(proxy)
                
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
                self.result_queue.put(('error', f"❌ 获取视频信息失败: {error_msg}"))
                
                # 提供解决建议
                if "Unable to download API page" in error_msg:
                    self.result_queue.put(('warning', "💡 建议: 尝试配置代理或检查网络连接"))
                elif "timed out" in error_msg:
                    self.result_queue.put(('warning', "💡 建议: 网络超时，请检查网络连接或更换代理"))
                elif "Connection refused" in error_msg:
                    self.result_queue.put(('warning', "💡 建议: 代理连接被拒绝，请检查代理设置"))
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def network_diagnosis(self):
        """网络诊断功能"""
        self._append_log("🔍 开始网络诊断...", "INFO")
        
        def _diagnose():
            try:
                # 1. 测试基本网络
                self.result_queue.put(('info', "1️⃣ 测试基本网络连接..."))
                try:
                    response = requests.get("https://www.google.com", timeout=10)
                    self.result_queue.put(('success', "✅ 基本网络连接正常"))
                except:
                    self.result_queue.put(('error', "❌ 基本网络连接失败"))
                
                # 2. 测试YouTube连接
                self.result_queue.put(('info', "2️⃣ 测试YouTube连接..."))
                try:
                    response = requests.get("https://www.youtube.com", timeout=10)
                    self.result_queue.put(('success', "✅ YouTube直连成功"))
                except:
                    self.result_queue.put(('warning', "⚠️ YouTube直连失败，可能需要代理"))
                
                # 3. 测试常用代理
                self.result_queue.put(('info', "3️⃣ 测试常用代理端口..."))
                common_proxies = [
                    'http://127.0.0.1:7890',
                    'http://127.0.0.1:7897', 
                    'http://127.0.0.1:1080',
                    'socks5://127.0.0.1:1080'
                ]
                
                working_proxies = []
                for proxy in common_proxies:
                    try:
                        proxies = {'http': proxy, 'https': proxy}
                        response = requests.get("https://www.google.com", proxies=proxies, timeout=5)
                        if response.status_code == 200:
                            working_proxies.append(proxy)
                            self.result_queue.put(('success', f"✅ 代理可用: {proxy}"))
                    except:
                        self.result_queue.put(('error', f"❌ 代理不可用: {proxy}"))
                
                # 4. 给出建议
                self.result_queue.put(('info', "4️⃣ 诊断结果和建议:"))
                if working_proxies:
                    self.result_queue.put(('success', f"✅ 发现 {len(working_proxies)} 个可用代理"))
                    self.result_queue.put(('info', "💡 建议: 将代理设置改为 'auto' 或选择可用的代理"))
                else:
                    self.result_queue.put(('warning', "⚠️ 未发现可用代理"))
                    self.result_queue.put(('info', "💡 建议: 启动代理软件或使用直连"))
                
            except Exception as e:
                self.result_queue.put(('error', f"❌ 网络诊断失败: {str(e)}"))
        
        threading.Thread(target=_diagnose, daemon=True).start()
    
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
                proxy = self.get_working_proxy()
                format_selector = self.format_var.get()
                
                ydl_opts = self.get_enhanced_ydl_opts(proxy)
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
    app = VideoMasterProUltimateApp(root)
    
    # 显示启动信息
    app._append_log("🚀 VideoMaster Pro 终极修复版启动", "SUCCESS")
    app._append_log("✨ 支持YouTube Music和复杂播放列表链接", "INFO")
    app._append_log("🔧 包含智能网络诊断和代理自动检测", "INFO")
    app._append_log("🌐 正在检查网络连接...", "INFO")
    
    root.mainloop()

if __name__ == "__main__":
    main()
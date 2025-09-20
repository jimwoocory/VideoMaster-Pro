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

        # 获取 yt-dlp 可执行文件路径
        self.yt_dlp_path = resource_path("yt-dlp.exe")
        if not os.path.exists(self.yt_dlp_path):
            # 如果打包的文件不存在，尝试系统PATH中的yt-dlp
            self.yt_dlp_path = "yt-dlp"

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

    def run_yt_dlp_command(self, args, capture_output=True):
        """运行 yt-dlp 命令"""
        try:
            cmd = [self.yt_dlp_path] + args
            result = subprocess.run(cmd, capture_output=capture_output, text=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            raise Exception(f"yt-dlp 执行失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception("未找到 yt-dlp 可执行文件。请确保 yt-dlp 已正确安装或打包。")

    def get_video_info(self, url, proxy=None):
        """获取视频信息"""
        args = ['--dump-json', '--no-download']
        if proxy:
            args.extend(['--proxy', proxy])
        args.append(url)
        
        result = self.run_yt_dlp_command(args)
        return json.loads(result.stdout)

    def download_video(self, url, output_path, format_id="best", proxy=None, download_subtitles=False):
        """下载视频"""
        args = ['-f', format_id, '-o', f'{output_path}/%(title)s.%(ext)s']
        if proxy:
            args.extend(['--proxy', proxy])
        if download_subtitles:
            args.extend(['--write-subs', '--write-auto-subs', '--sub-langs', 'en,zh-Hans,zh-Hant'])
        args.append(url)
        
        # 使用 Popen 来实时获取输出
        cmd = [self.yt_dlp_path] + args
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, universal_newlines=True)
        
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.strip())
            # 解析进度信息
            if '[download]' in line and '%' in line:
                self.result_queue.put(("progress", line.strip()))
        
        process.wait()
        if process.returncode != 0:
            raise Exception(f"下载失败: {''.join(output_lines)}")
        
        return True

    def create_widgets(self):
        # 创建主容器，使用苹果风格的卡片布局
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # URL输入卡片
        url_card = self.create_card(main_container, "🎬 视频链接")
        url_card.pack(fill=tk.X, pady=(0, 15))

        url_frame = tk.Frame(url_card, bg=self.colors['card_bg'])
        url_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(url_frame, text="YouTube 链接:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.url_entry = tk.Entry(url_frame, width=60, font=('Microsoft YaHei UI', 11), relief='solid', bd=1)
        self.url_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 5))
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")

        fetch_btn = tk.Button(url_frame, text="获取信息", command=self.fetch_video_info,
                             bg=self.colors['primary'], fg='white', font=('Microsoft YaHei UI', 10, 'bold'),
                             relief='flat', padx=20, pady=8, cursor='hand2')
        fetch_btn.grid(row=0, column=2, padx=10, rowspan=2, sticky=tk.NS)

        tk.Label(url_frame, text="批量链接 (每行一个):", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11)).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.urls_text = scrolledtext.ScrolledText(url_frame, wrap=tk.WORD, height=3, width=60, 
                                                  font=('Microsoft YaHei UI', 10), relief='solid', bd=1)
        self.urls_text.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 5))

        tk.Label(url_frame, text="代理地址 (可选):", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11)).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.proxy_entry = tk.Entry(url_frame, width=60, font=('Microsoft YaHei UI', 11), relief='solid', bd=1)
        self.proxy_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 5))
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")

        # 保存路径卡片
        path_card = self.create_card(main_container, "📁 保存设置")
        path_card.pack(fill=tk.X, pady=(0, 15))

        path_frame = tk.Frame(path_card, bg=self.colors['card_bg'])
        path_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(path_frame, text="保存路径:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.save_path_var = tk.StringVar(value=os.getcwd())
        path_entry = tk.Entry(path_frame, textvariable=self.save_path_var, width=50, 
                             font=('Microsoft YaHei UI', 11), relief='solid', bd=1)
        path_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 5))
        
        browse_btn = tk.Button(path_frame, text="浏览", command=self.browse_save_path,
                              bg=self.colors['secondary'], fg='white', font=('Microsoft YaHei UI', 10, 'bold'),
                              relief='flat', padx=15, pady=8, cursor='hand2')
        browse_btn.grid(row=0, column=2, padx=10)

        # 视频信息预览卡片
        info_card = self.create_card(main_container, "ℹ️ 视频信息")
        info_card.pack(fill=tk.X, pady=(0, 15))

        info_frame = tk.Frame(info_card, bg=self.colors['card_bg'])
        info_frame.pack(fill=tk.X, padx=20, pady=15)

        self.title_var = tk.StringVar(value="标题: 等待获取...")
        self.duration_var = tk.StringVar(value="时长: --")
        self.views_var = tk.StringVar(value="观看次数: --")
        self.uploader_var = tk.StringVar(value="上传者: --")

        tk.Label(info_frame, textvariable=self.title_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 10)).grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Label(info_frame, textvariable=self.duration_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_secondary'], font=('Microsoft YaHei UI', 10)).grid(row=0, column=1, sticky=tk.W, pady=2, padx=20)
        tk.Label(info_frame, textvariable=self.views_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_secondary'], font=('Microsoft YaHei UI', 10)).grid(row=0, column=2, sticky=tk.W, pady=2, padx=20)
        tk.Label(info_frame, textvariable=self.uploader_var, bg=self.colors['card_bg'], 
                fg=self.colors['text_secondary'], font=('Microsoft YaHei UI', 10)).grid(row=0, column=3, sticky=tk.W, pady=2, padx=20)

        # 下载选项卡片
        options_card = self.create_card(main_container, "⚙️ 下载选项")
        options_card.pack(fill=tk.X, pady=(0, 15))

        options_frame = tk.Frame(options_card, bg=self.colors['card_bg'])
        options_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(options_frame, text="格式:", bg=self.colors['card_bg'], 
                fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.format_id_var = tk.StringVar(value="best")
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_id_var, 
                                   values=["best", "worst", "bestvideo+bestaudio", "bestaudio"], width=20)
        format_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 5))

        query_btn = tk.Button(options_frame, text="查询格式", command=self.query_formats,
                             bg=self.colors['accent'], fg='white', font=('Microsoft YaHei UI', 10, 'bold'),
                             relief='flat', padx=15, pady=8, cursor='hand2')
        query_btn.grid(row=0, column=2, padx=10)

        self.subtitle_var = tk.BooleanVar(value=False)
        subtitle_check = tk.Checkbutton(options_frame, text="下载字幕", variable=self.subtitle_var,
                                       bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                                       font=('Microsoft YaHei UI', 10), selectcolor=self.colors['card_bg'])
        subtitle_check.grid(row=0, column=3, sticky=tk.W, pady=5, padx=20)

        # 控制按钮
        button_frame = tk.Frame(main_container, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=15)

        start_btn = tk.Button(button_frame, text="🚀 开始下载", command=self.start_download,
                             bg=self.colors['primary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                             relief='flat', padx=30, pady=12, cursor='hand2')
        start_btn.pack(side=tk.LEFT, padx=(0, 10))

        stop_btn = tk.Button(button_frame, text="⏹️ 停止下载", command=self.stop_download,
                            bg=self.colors['accent'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                            relief='flat', padx=30, pady=12, cursor='hand2')
        stop_btn.pack(side=tk.LEFT, padx=10)

        clear_btn = tk.Button(button_frame, text="🗑️ 清空日志", command=self.clear_logs,
                             bg=self.colors['text_secondary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                             relief='flat', padx=30, pady=12, cursor='hand2')
        clear_btn.pack(side=tk.LEFT, padx=10)

        history_btn = tk.Button(button_frame, text="📋 查看历史", command=self.show_history,
                               bg=self.colors['secondary'], fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                               relief='flat', padx=30, pady=12, cursor='hand2')
        history_btn.pack(side=tk.LEFT, padx=10)

        # 进度卡片
        progress_card = self.create_card(main_container, "📊 下载进度")
        progress_card.pack(fill=tk.X, pady=(0, 15))

        progress_frame = tk.Frame(progress_card, bg=self.colors['card_bg'])
        progress_frame.pack(fill=tk.X, padx=20, pady=15)

        self.progress_label = tk.Label(progress_frame, text="准备就绪", bg=self.colors['card_bg'], 
                                      fg=self.colors['text_primary'], font=('Microsoft YaHei UI', 11))
        self.progress_label.pack(anchor=tk.W, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # 日志卡片
        log_card = self.create_card(main_container, "📝 运行日志")
        log_card.pack(fill=tk.BOTH, expand=True)

        log_frame = tk.Frame(log_card, bg=self.colors['card_bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, 
                                                 font=('Consolas', 10), bg='#1E1E1E', fg='#FFFFFF',
                                                 relief='flat', bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # 配置日志颜色标签
        self.log_text.tag_configure("error", foreground="#FF6B6B")
        self.log_text.tag_configure("success", foreground="#51CF66")
        self.log_text.tag_configure("info", foreground="#74C0FC")
        self.log_text.tag_configure("progress", foreground="#FFD43B")

    def create_card(self, parent, title):
        """创建苹果风格的卡片容器"""
        card_frame = tk.Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=0)
        
        # 标题栏
        title_frame = tk.Frame(card_frame, bg=self.colors['primary'], height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text=title, bg=self.colors['primary'], 
                              fg='white', font=('Microsoft YaHei UI', 12, 'bold'))
        title_label.pack(expand=True)
        
        return card_frame

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
                info_dict = self.get_video_info(url, proxy)

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
                args = ['-F']  # 列出所有格式
                if proxy:
                    args.extend(['--proxy', proxy])
                args.append(url)
                
                result = self.run_yt_dlp_command(args)
                formats_info = f"可用格式 for: {url}\n{result.stdout}"
                self.result_queue.put(("info", formats_info))

            except Exception as e:
                self.result_queue.put(("error", f"查询格式失败: {str(e)}"))

        # 在单独线程中查询格式
        threading.Thread(target=_query, daemon=True).start()

    def start_download(self):
        """开始下载视频"""
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
        format_id = self.format_id_var.get().strip() or "best"

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
            self.download_queue.put(("download", url, proxy, save_path, format_id, download_subtitles))

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
                        args=(task_id, task[1], task[2], task[3], task[4], task[5]),
                        daemon=True
                    )
                    self.download_threads[task_id] = thread
                    thread.start()
                self.download_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"处理任务时出错: {str(e)}")

    def _download(self, task_id, url, proxy, save_path, format_id, download_subtitles):
        """下载视频的实际处理函数"""
        self.is_downloading = True

        try:
            self.logger.info(f"开始下载到: {save_path}")

            # 更新进度条
            self.update_progress(
                (self.current_task_index-1) / self.total_tasks * 100, 
                f"下载中 {self.current_task_index}/{self.total_tasks}"
            )

            # 开始下载
            self.download_video(url, save_path, format_id, proxy, download_subtitles)

            if self.abort_all_tasks:
                self.result_queue.put(("info", f"下载已取消: {url}"))
                return

            self.logger.info(f"下载完成: {url}")
            self.update_progress(100, "下载完成")
            self.result_queue.put(("success", f"下载完成: {url}"))
            self.update_progress(
                self.current_task_index / self.total_tasks * 100, 
                f"完成 {self.current_task_index}/{self.total_tasks}"
            )

            # 保存下载历史
            self.save_download_history(url, "视频", format_id, save_path)

        except Exception as e:
            self.logger.error(f"下载失败: {str(e)}")
            self.update_progress(0, "下载失败")
            self.result_queue.put(("error", f"下载失败: {str(e)}"))
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
                    self._append_log(result[1], "progress")
        except Exception as e:
            self._append_log(f"处理结果时出错: {str(e)}", "error")

        # 每隔100毫秒检查一次结果队列
        self.root.after(100, self.process_results)

    def _append_log(self, message, tag="info"):
        """向日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
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
        if not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载历史记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("800x500")
        history_window.configure(bg=self.colors['bg'])

        # 创建表格
        columns = ("序号", "标题", "URL", "格式", "保存路径", "时间")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")

        # 设置列宽和标题
        for col in columns:
            tree.heading(col, text=col)
            if col == "标题":
                tree.column(col, width=200)
            elif col == "URL":
                tree.column(col, width=300)
            elif col == "保存路径":
                tree.column(col, width=150)
            else:
                tree.column(col, width=80)

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
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 添加双击打开文件位置功能
        def open_file_location(event):
            if tree.selection():
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


def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 显示启动画面
    splash = tk.Toplevel(root)
    splash.title("VideoMaster Pro")
    splash.geometry("400x300")
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    splash.configure(bg='#F2F2F7')

    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 300) // 2
    splash.geometry(f"400x300+{x}+{y}")

    # 启动画面内容
    tk.Label(splash, text="VideoMaster Pro", font=('Microsoft YaHei UI', 18, 'bold'), 
             fg='#1D1D1F', bg='#F2F2F7').pack(pady=50)
    tk.Label(splash, text="专业视频下载大师 v2.0", font=('Microsoft YaHei UI', 12), 
             fg='#8E8E93', bg='#F2F2F7').pack()
    
    progress = ttk.Progressbar(splash, orient='horizontal', mode='indeterminate', length=300)
    progress.pack(pady=30)
    progress.start(10)

    tk.Label(splash, text="正在启动...", font=('Microsoft YaHei UI', 10), 
             fg='#8E8E93', bg='#F2F2F7').pack()

    def close_splash():
        progress.stop()
        splash.destroy()
        root.deiconify()  # 显示主窗口
        root.focus_force()

    root.after(2000, close_splash)  # 2秒后关闭启动画面
    
    app = VideoMasterProApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
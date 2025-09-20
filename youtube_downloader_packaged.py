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

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro")
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
        self.root.attributes('-topmost', True)  # 默认置顶

        # 苹果风格字体配置
        self.fonts = {
            'title': ('SF Pro Display', 18, 'bold'),
            'heading': ('SF Pro Display', 14, 'bold'),
            'body': ('SF Pro Text', 12),
            'caption': ('SF Pro Text', 10),
            'button': ('SF Pro Text', 12, 'medium')
        }
        
        # 设置苹果风格样式
        self.style = ttk.Style()
        self.setup_apple_styles()

        # 初始化变量
        self.download_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self.download_tasks = []
        self.current_task_index = 0
        self.total_tasks = 0
        self.abort_all_tasks = False
        self.is_on_top = True
        self.last_formats_data = None

        self.video_info = {}

        # 设置打包后的工具路径
        self.ffmpeg_path = resource_path("ffmpeg.exe")
        self.ffprobe_path = resource_path("ffprobe.exe")
        self.yt_dlp_path = resource_path("yt-dlp.exe")

        self.setup_logging()

        self.create_widgets()

        self.load_download_history()

        self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()

        self.root.after(100, self.process_results)

        self.ydl_instance = None
        self.is_downloading = False
        self.download_threads = {}

    def setup_apple_styles(self):
        """设置苹果风格样式"""
        # 配置苹果风格的ttk样式
        self.style.configure('TLabel', 
                           font=self.fonts['body'],
                           background=self.colors['card_bg'],
                           foreground=self.colors['text_primary'])
        
        self.style.configure('TButton', 
                           font=self.fonts['button'],
                           background=self.colors['primary'],
                           foreground='white')
        
        self.style.configure('TEntry', 
                           font=self.fonts['body'],
                           fieldbackground=self.colors['card_bg'])
        
        self.style.configure('TFrame',
                           background=self.colors['card_bg'])

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
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        url_frame = ttk.LabelFrame(main_frame, text="视频信息", padding=10)
        url_frame.pack(fill=tk.X, pady=5)

        ttk.Label(url_frame, text="YouTube 链接:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")

        ttk.Button(url_frame, text="获取信息", command=self.fetch_video_info).grid(row=0, column=2, padx=5, rowspan=2, sticky=tk.NS)

        ttk.Label(url_frame, text="或批量输入URLs (每行一个):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.urls_text = scrolledtext.ScrolledText(url_frame, wrap=tk.WORD, height=3)
        self.urls_text.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        ttk.Label(url_frame, text="代理地址 (可选):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.proxy_entry = ttk.Entry(url_frame, width=60)
        self.proxy_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")

        path_frame = ttk.LabelFrame(main_frame, text="保存路径", padding=10)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.save_path_var = tk.StringVar(value=os.getcwd())
        ttk.Entry(path_frame, textvariable=self.save_path_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(path_frame, text="浏览", command=self.browse_save_path).grid(row=0, column=2, padx=5)

        info_frame = ttk.LabelFrame(main_frame, text="视频信息预览", padding=10)
        info_frame.pack(fill=tk.X, pady=5)

        self.title_var = tk.StringVar(value="标题: ")
        self.duration_var = tk.StringVar(value="时长: ")
        self.views_var = tk.StringVar(value="观看次数: ")
        self.uploader_var = tk.StringVar(value="上传者: ")

        ttk.Label(info_frame, textvariable=self.title_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.duration_var).grid(row=0, column=1, sticky=tk.W, pady=2, padx=20)
        ttk.Label(info_frame, textvariable=self.views_var).grid(row=0, column=2, sticky=tk.W, pady=2, padx=20)
        ttk.Label(info_frame, textvariable=self.uploader_var).grid(row=0, column=3, sticky=tk.W, pady=2, padx=20)

        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding=10)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="自定义格式ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.format_id_var = tk.StringVar(value="bv*+ba/b")
        self.format_id_entry = ttk.Entry(options_frame, textvariable=self.format_id_var, width=15)
        self.format_id_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.format_id_entry.bind("<Button-1>", self.reopen_formats_window)
        ttk.Button(options_frame, text="查询格式", command=self.query_formats).grid(row=0, column=2, padx=5)

        self.subtitle_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="下载字幕", variable=self.subtitle_var).grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)

        ttk.Label(options_frame, text="线程数:").grid(row=0, column=4, sticky=tk.W, pady=5)
        self.threads_var = tk.StringVar(value="4")
        ttk.Combobox(options_frame, textvariable=self.threads_var, values=["1", "2", "4", "8", "16"], width=5).grid(row=0, column=5, sticky=tk.W, pady=5, padx=5)

        self.transcode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="下载后转码", variable=self.transcode_var).grid(row=0, column=6, sticky=tk.W, pady=5, padx=5)
        self.transcode_format = tk.StringVar(value="mp4")
        ttk.Combobox(options_frame, textvariable=self.transcode_format, values=["mp4", "mkv", "avi", "mov", "webm"], width=10).grid(row=0, column=7, sticky=tk.W, pady=5, padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="开始下载", command=self.start_download, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="终止下载", command=self.stop_download, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空日志", command=self.clear_logs, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看历史", command=self.show_history, width=15).pack(side=tk.LEFT, padx=5)

        # 置顶按钮
        self.top_button = ttk.Button(main_frame, text="📌", command=self.toggle_on_top, width=3)
        self.top_button.place(relx=1.0, rely=0, anchor='ne', x=-15, y=5)

        progress_frame = ttk.LabelFrame(main_frame, text="下载进度", padding=10)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="准备就绪")
        self.progress_label.pack(anchor=tk.W, pady=2)

        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        log_frame = ttk.LabelFrame(main_frame, text="信息窗口日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="blue")
        self.log_text.tag_configure("progress", foreground="blue")

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
                    'quiet': True,
                    'ffmpeg_location': self.ffmpeg_path,
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
                    'quiet': True,
                    'ffmpeg_location': self.ffmpeg_path,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    formats = info_dict.get('formats', [info_dict])

                # 推荐格式ID：选择最高质量的视频和音频流进行合并
                best_video = None
                best_audio = None

                # 筛选出纯视频和纯音频格式
                video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('height')]
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('abr')]

                # 按分辨率降序排序视频
                if video_formats:
                    video_formats.sort(key=lambda f: f.get('height', 0), reverse=True)
                    best_video = video_formats[0]

                # 按音频比特率降序排序音频
                if audio_formats:
                    audio_formats.sort(key=lambda f: f.get('abr', 0), reverse=True)
                    best_audio = audio_formats[0]

                recommended_format = None
                if best_video and best_audio:
                    recommended_format = f"{best_video['format_id']}+{best_audio['format_id']}"

                # 将结构化数据和推荐格式一起传递
                self.result_queue.put(("formats_queried", (info_dict.get('title', '未知标题'), formats, recommended_format)))

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

            # 设置yt-dlp选项
            # 检查ffmpeg是否可用（如果需要合并格式或提取音频）
            needs_ffmpeg = (
                '+' in format_id or  # 格式包含+表示需要合并
                (format_id.lower().startswith('audio') or format_id == 'bestaudio')  # 音频提取需要ffmpeg
            )

            if needs_ffmpeg and not self.check_ffmpeg():
                raise RuntimeError("需要ffmpeg来合并格式或提取音频，但未找到ffmpeg。请确保ffmpeg已安装并添加到系统PATH中，或已随程序打包。")

            ydl_opts = {
                'format': format_id,
                'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                'noplaylist': True,
                'continuedl': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 10,
                'proxy': proxy,
                'ffmpeg_location': self.ffmpeg_path,
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
                self.result_queue.put(("error", f"下载失败: 需要ffmpeg但未安装。请安装ffmpeg并确保其在系统PATH中，或已随程序打包。"))
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
                elif result[0] == "formats_queried":
                    self.last_formats_data = result[1]  # 缓存查询结果
                    title, formats, recommended_format = self.last_formats_data
                    self.show_formats_window(title, formats, recommended_format)
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
        if not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载历史记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("800x500")
        history_window.minsize(700, 400)

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

    def show_formats_window(self, title, formats, recommended_format):
        """以表格形式显示可用格式"""
        formats_window = tk.Toplevel(self.root)
        formats_window.title(f"可用格式 - {title[:50]}")
        
        # 设置新的窗口尺寸
        popup_width = 900
        popup_height = 600
        formats_window.minsize(800, 500)

        formats_window.transient(self.root)
        formats_window.grab_set()

        # 将弹出窗口居中于主窗口之上
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        center_x = main_x + (main_width - popup_width) // 2
        center_y = main_y + (main_height - popup_height) // 2
        formats_window.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")

        # 创建 Treeview
        columns = ("ID", "Ext", "Resolution", "FPS", "VCodec", "ACodec", "Size (MB)", "Note")
        tree = ttk.Treeview(formats_window, columns=columns, show="headings")
        tree.tag_configure('blue_text', foreground='blue')

        # Helper for formatting filesize
        def format_size(size_in_bytes):
            if size_in_bytes is None or not isinstance(size_in_bytes, (int, float)):
                return "N/A"
            return f"{size_in_bytes / (1024*1024):.2f}"

        # 设置列标题和宽度
        tree.heading("ID", text="ID")
        tree.column("ID", width=80, anchor=tk.W)
        tree.heading("Ext", text="格式")
        tree.column("Ext", width=60, anchor=tk.CENTER)
        tree.heading("Resolution", text="分辨率")
        tree.column("Resolution", width=120)
        tree.heading("FPS", text="帧率")
        tree.column("FPS", width=60, anchor=tk.CENTER)
        tree.heading("VCodec", text="视频编码")
        tree.column("VCodec", width=150)
        tree.heading("ACodec", text="音频编码")
        tree.column("ACodec", width=120)
        tree.heading("Size (MB)", text="大小 (MB)")
        tree.column("Size (MB)", width=100, anchor=tk.E)
        tree.heading("Note", text="备注")
        tree.column("Note", width=150)

        # 添加数据
        for f in sorted(formats, key=lambda x: (x.get('height', 0) or 0, x.get('fps', 0) or 0), reverse=True):
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            
            resolution = 'N/A'
            if vcodec != 'none':
                resolution = f.get('resolution', f"{f.get('width')}x{f.get('height')}")

            # A more descriptive note
            note = f.get('format_note', '')
            if vcodec != 'none' and acodec == 'none':
                note = '纯视频'
            elif vcodec == 'none' and acodec != 'none':
                note = '纯音频'
            elif vcodec != 'none' and acodec != 'none':
                note = '视频+音频 (预合并)'

            filesize = f.get('filesize') or f.get('filesize_approx')

            tree.insert("", "end", values=(
                f.get('format_id', ''),
                f.get('ext', ''),
                resolution,
                f.get('fps', ''),
                vcodec,
                acodec,
                format_size(filesize),
                note
            ), tags=('blue_text',))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(formats_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加双击事件，将所选格式ID填入主窗口
        def on_double_click(event):
            try:
                item = tree.selection()[0]
                format_id = tree.item(item, "values")[0]
                self.format_id_var.set(format_id)
                formats_window.destroy()
                self.result_queue.put(("info", f"已选择格式ID: {format_id}"))
            except IndexError:
                pass # Ignore double clicks on empty space

        tree.bind("<Double-1>", on_double_click)

        # 添加推荐区域
        if recommended_format:
            recommend_frame = ttk.Frame(formats_window, padding=5)
            recommend_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

            ttk.Label(recommend_frame, text="最佳推荐:", font=('SimHei', 10, 'bold')).pack(side=tk.LEFT, padx=(10, 5))
            
            rec_entry = ttk.Entry(recommend_frame, font=('SimHei', 10, 'bold'), foreground="blue")
            rec_entry.insert(0, recommended_format)
            rec_entry.config(state='readonly')
            rec_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            def use_recommendation():
                self.format_id_var.set(recommended_format)
                formats_window.destroy()
                self.result_queue.put(("info", f"已采纳推荐格式: {recommended_format}"))

            ttk.Button(recommend_frame, text="使用此组合", command=use_recommendation).pack(side=tk.RIGHT, padx=(5, 10))

    def reopen_formats_window(self, event=None):
        """重新打开格式选择窗口（如果已有数据）"""
        if self.last_formats_data:
            title, formats, recommended_format = self.last_formats_data
            self.show_formats_window(title, formats, recommended_format)
        else:
            self.result_queue.put(("info", "请先点击\"查询格式\"获取数据。"))

    def toggle_on_top(self):
        """切换窗口置顶状态"""
        self.is_on_top = not self.is_on_top
        self.root.attributes('-topmost', self.is_on_top)
        if self.is_on_top:
            self.result_queue.put(("info", "窗口已置顶。"))
        else:
            self.result_queue.put(("info", "窗口已取消置顶。"))

    def transcode_file(self, input_file, output_file):
        """转码文件"""
        try:
            # 检查ffmpeg是否存在
            if not self.check_ffmpeg():
                self.result_queue.put(("error", "转码失败: 未找到ffmpeg。请确保ffmpeg已安装并添加到系统PATH中，或已随程序打包。"))
                return

            # 构建ffmpeg命令
            cmd = [
                self.ffmpeg_path,
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
        """检查ffmpeg是否可用"""
        try:
            subprocess.run([self.ffmpeg_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

def show_splash_screen(root):
    splash = tk.Toplevel(root)
    splash.title("")
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    
    # 现代化尺寸 - 更宽更优雅
    splash_width = 500
    splash_height = 350
    
    # 居中显示
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - splash_width) // 2
    y = (screen_height - splash_height) // 2
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
    
    # 创建渐变背景效果的Canvas
    canvas = tk.Canvas(splash, width=splash_width, height=splash_height, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 绘制现代渐变背景
    def create_gradient_background():
        # 创建从深蓝到浅蓝的渐变效果
        for i in range(splash_height):
            # 计算渐变色
            ratio = i / splash_height
            # 从深蓝 #1e3c72 到浅蓝 #2a5298
            r = int(30 + (42 - 30) * ratio)
            g = int(60 + (82 - 60) * ratio) 
            b = int(114 + (152 - 114) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, splash_width, i, fill=color, width=1)
    
    create_gradient_background()
    
    # 添加圆角边框效果
    def create_rounded_rect(x1, y1, x2, y2, radius=20, **kwargs):
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return canvas.create_polygon(points, smooth=True, **kwargs)
    
    # 创建半透明的内容区域
    content_bg = create_rounded_rect(40, 40, splash_width-40, splash_height-40, 
                                   radius=25, fill="#ffffff", stipple="gray25", outline="#ffffff")
    
    # Logo区域 - 使用现代化的图标设计
    logo_y = 80
    
    # 绘制现代化的YouTube图标
    def draw_modern_logo():
        # 主圆形背景
        canvas.create_oval(200, logo_y-30, 300, logo_y+30, 
                          fill="#FF0000", outline="#CC0000", width=2)
        
        # 播放按钮三角形
        triangle_points = [230, logo_y-15, 230, logo_y+15, 260, logo_y]
        canvas.create_polygon(triangle_points, fill="white", outline="white")
        
        # 添加光泽效果
        canvas.create_oval(205, logo_y-25, 240, logo_y-10, 
                          fill="#FF4444", stipple="gray25", outline="")
    
    draw_modern_logo()
    
    # 应用标题 - 现代化字体
    title_text = canvas.create_text(splash_width//2, logo_y+60, 
                                   text="YouTube 下载器", 
                                   font=('Microsoft YaHei UI', 24, 'bold'),
                                   fill="white", anchor="center")
    
    # 版本信息
    version_text = canvas.create_text(splash_width//2, logo_y+90,
                                     text="Professional Edition v2.0",
                                     font=('Microsoft YaHei UI', 10),
                                     fill="#E0E0E0", anchor="center")
    
    # 品牌标语
    slogan_text = canvas.create_text(splash_width//2, logo_y+120,
                                    text="高效 • 稳定 • 专业",
                                    font=('Microsoft YaHei UI', 12),
                                    fill="#B0C4DE", anchor="center")
    
    # 现代化进度指示器
    progress_y = splash_height - 80
    
    # 进度条背景
    progress_bg = create_rounded_rect(100, progress_y-8, 400, progress_y+8,
                                    radius=8, fill="#34495e", outline="")
    
    # 动态进度条
    progress_bar = create_rounded_rect(100, progress_y-8, 120, progress_y+8,
                                     radius=8, fill="#3498db", outline="")
    
    # 状态文本
    status_text = canvas.create_text(splash_width//2, progress_y+25,
                                    text="正在初始化应用程序...",
                                    font=('Microsoft YaHei UI', 10),
                                    fill="white", anchor="center")
    
    # 动画效果
    animation_step = 0
    progress_width = 0
    
    def animate_splash():
        nonlocal animation_step, progress_width
        animation_step += 1
        
        # Logo呼吸效果
        if animation_step % 20 < 10:
            scale = 1.0 + 0.05 * (animation_step % 10) / 10
        else:
            scale = 1.05 - 0.05 * (animation_step % 10) / 10
        
        # 进度条动画
        progress_width = min(300, progress_width + 3)
        canvas.coords(progress_bar, 100, progress_y-8, 100+progress_width, progress_y+8)
        
        # 更新状态文本
        status_messages = [
            "正在初始化应用程序...",
            "加载核心组件...", 
            "配置下载引擎...",
            "准备用户界面...",
            "启动完成！"
        ]
        
        message_index = min(len(status_messages)-1, animation_step // 15)
        canvas.itemconfig(status_text, text=status_messages[message_index])
        
        # 标题闪烁效果
        if animation_step % 30 < 15:
            canvas.itemconfig(title_text, fill="white")
        else:
            canvas.itemconfig(title_text, fill="#F0F8FF")
        
        if animation_step < 75:  # 延长显示时间到约4秒
            splash.after(50, animate_splash)
        else:
            close_splash()
    
    def close_splash():
        # 淡出效果
        def fade_out(alpha=1.0):
            if alpha > 0:
                # 简单的淡出效果
                canvas.configure(bg=f"#{int(30*alpha):02x}{int(60*alpha):02x}{int(114*alpha):02x}")
                splash.after(30, lambda: fade_out(alpha - 0.1))
            else:
                splash.destroy()
                root.deiconify()
                root.focus_force()
        
        fade_out()
    
    # 开始动画
    splash.after(100, animate_splash)
    
    # 点击跳过
    def skip_splash(event=None):
        close_splash()
    
    canvas.bind("<Button-1>", skip_splash)
    
    # 添加底部版权信息
    canvas.create_text(splash_width//2, splash_height-20,
                      text="© 2024 YouTube Downloader Pro. All rights reserved.",
                      font=('Microsoft YaHei UI', 8),
                      fill="#708090", anchor="center")

def main():
    root = tk.Tk()
    root.withdraw()
    show_splash_screen(root)
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
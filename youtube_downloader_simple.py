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

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 下载器 Pro")
        self.root.geometry("1000x800")
        self.root.minsize(900, 750)
        
        # Center the main window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 800) // 2
        self.root.geometry(f"1000x800+{x}+{y}")
        
        # 设置现代化样式
        self.setup_modern_styles()
        
        # 初始化变量
        self.download_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.download_tasks = []
        self.current_task_index = 0
        self.total_tasks = 0
        self.abort_all_tasks = False
        self.video_info = {}
        self.is_downloading = False
        self.ydl_instance = None
        self.download_threads = {}
        
        self.setup_logging()
        self.create_widgets()
        self.load_download_history()
        
        # 启动处理线程
        self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()
        self.root.after(100, self.process_results)

    def setup_modern_styles(self):
        """设置现代化样式"""
        self.style = ttk.Style()
        
        # 使用现代化的颜色方案
        self.colors = {
            'primary': '#007AFF',      # 苹果蓝
            'secondary': '#5856D6',    # 苹果紫
            'success': '#34C759',      # 苹果绿
            'warning': '#FF9500',      # 苹果橙
            'danger': '#FF3B30',       # 苹果红
            'background': '#F2F2F7',   # 浅灰背景
            'surface': '#FFFFFF',      # 白色表面
            'text': '#1C1C1E',         # 深色文字
            'text_secondary': '#8E8E93' # 次要文字
        }
        
        # 配置基本样式（使用系统默认样式名）
        try:
            self.style.configure('TLabel', font=('Microsoft YaHei UI', 10))
            self.style.configure('TButton', font=('Microsoft YaHei UI', 9))
            self.style.configure('TEntry', font=('Microsoft YaHei UI', 9))
            self.style.configure('TLabelFrame', font=('Microsoft YaHei UI', 10, 'bold'))
        except:
            # 如果字体不可用，使用默认字体
            pass

    def setup_logging(self):
        """设置日志系统"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                self.log_queue.put(("log", record.levelname, self.format(record)))
        
        self.log_handler = QueueHandler(self.result_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)

    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="视频链接", padding=15)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="YouTube 链接:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=")
        
        ttk.Button(url_frame, text="获取信息", command=self.fetch_video_info).grid(row=0, column=2, padx=(10, 0))
        
        url_frame.columnconfigure(1, weight=1)
        
        # 视频信息预览
        info_frame = ttk.LabelFrame(main_frame, text="视频信息", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_var = tk.StringVar(value="标题: 请先获取视频信息")
        self.duration_var = tk.StringVar(value="时长: --")
        self.views_var = tk.StringVar(value="观看次数: --")
        
        ttk.Label(info_frame, textvariable=self.title_var).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.duration_var).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.views_var).pack(anchor=tk.W, pady=2)
        
        # 下载选项
        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行选项
        row1_frame = ttk.Frame(options_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1_frame, text="格式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="best")
        format_combo = ttk.Combobox(row1_frame, textvariable=self.format_var, 
                                  values=["best", "bestvideo+bestaudio", "worst", "bestaudio"], 
                                  width=20, state="readonly")
        format_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(row1_frame, text="保存路径:").pack(side=tk.LEFT)
        self.save_path_var = tk.StringVar(value=os.getcwd())
        ttk.Entry(row1_frame, textvariable=self.save_path_var, width=30).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(row1_frame, text="浏览", command=self.browse_save_path).pack(side=tk.LEFT, padx=(5, 0))
        
        # 第二行选项
        row2_frame = ttk.Frame(options_frame)
        row2_frame.pack(fill=tk.X)
        
        self.subtitle_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2_frame, text="下载字幕", variable=self.subtitle_var).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row2_frame, text="代理:").pack(side=tk.LEFT)
        self.proxy_entry = ttk.Entry(row2_frame, width=25)
        self.proxy_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.proxy_entry.insert(0, "http://127.0.0.1:7897")
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="开始下载", command=self.start_download).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="停止下载", command=self.stop_download).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="查看历史", command=self.show_history).pack(side=tk.LEFT)
        
        # 进度条
        progress_frame = ttk.LabelFrame(main_frame, text="下载进度", padding=15)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="准备就绪")
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志信息", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, 
                                                font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 配置日志颜色
        self.log_text.tag_configure("error", foreground="#FF3B30")
        self.log_text.tag_configure("success", foreground="#34C759")
        self.log_text.tag_configure("info", foreground="#007AFF")
        self.log_text.tag_configure("warning", foreground="#FF9500")

    def browse_save_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)

    def validate_url(self, url):
        """验证URL格式"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc]) and 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc
        except ValueError:
            return False

    def fetch_video_info(self):
        """获取视频信息"""
        url = self.url_entry.get().strip()
        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的 YouTube 链接")
            return
        
        self.log_message("正在获取视频信息...", "info")
        
        def _fetch():
            try:
                proxy = self.proxy_entry.get().strip() or None
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'proxy': proxy
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                
                title = info_dict.get('title', '未知标题')
                duration = info_dict.get('duration', 0)
                views = info_dict.get('view_count', 0)
                
                # 格式化时长
                if duration:
                    hours, remainder = divmod(int(duration), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if hours > 0:
                        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "未知"
                
                # 格式化观看次数
                views_str = f"{views:,}" if views else "未知"
                
                # 更新界面
                self.root.after(0, lambda: self.title_var.set(f"标题: {title}"))
                self.root.after(0, lambda: self.duration_var.set(f"时长: {duration_str}"))
                self.root.after(0, lambda: self.views_var.set(f"观看次数: {views_str}"))
                
                self.video_info[url] = info_dict
                self.result_queue.put(("success", f"成功获取视频信息: {title}"))
                
            except Exception as e:
                self.result_queue.put(("error", f"获取视频信息失败: {str(e)}"))
        
        threading.Thread(target=_fetch, daemon=True).start()

    def start_download(self):
        """开始下载"""
        url = self.url_entry.get().strip()
        if not self.validate_url(url):
            messagebox.showerror("错误", "请输入有效的 YouTube 链接")
            return
        
        if self.is_downloading:
            messagebox.showwarning("警告", "已有下载任务在进行中")
            return
        
        self.is_downloading = True
        self.log_message("开始下载...", "info")
        
        def _download():
            try:
                proxy = self.proxy_entry.get().strip() or None
                save_path = self.save_path_var.get()
                format_id = self.format_var.get()
                download_subtitles = self.subtitle_var.get()
                
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                    'proxy': proxy,
                    'writesubtitles': download_subtitles,
                    'writeautomaticsub': download_subtitles,
                    'progress_hooks': [self._download_hook],
                }
                
                self.ydl_instance = yt_dlp.YoutubeDL(ydl_opts)
                info_dict = self.ydl_instance.extract_info(url, download=True)
                
                if not self.abort_all_tasks:
                    title = info_dict.get('title', '未知视频')
                    self.result_queue.put(("success", f"下载完成: {title}"))
                    self.save_download_history(url, title, format_id, save_path)
                
            except Exception as e:
                self.result_queue.put(("error", f"下载失败: {str(e)}"))
            finally:
                self.is_downloading = False
                self.ydl_instance = None
                self.root.after(0, lambda: self.progress_bar.configure(value=0))
                self.root.after(0, lambda: self.progress_label.configure(text="准备就绪"))
        
        threading.Thread(target=_download, daemon=True).start()

    def _download_hook(self, d):
        """下载进度回调"""
        if self.abort_all_tasks:
            return
        
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%')
            speed_str = d.get('_speed_str', '未知')
            
            try:
                percent = float(percent_str.strip('%'))
                self.root.after(0, lambda: self.progress_bar.configure(value=percent))
                self.root.after(0, lambda: self.progress_label.configure(
                    text=f"下载中: {percent_str} | 速度: {speed_str}"))
            except:
                pass
        
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.progress_label.configure(text="处理文件中..."))

    def stop_download(self):
        """停止下载"""
        if not self.is_downloading:
            messagebox.showinfo("提示", "当前没有正在进行的下载")
            return
        
        self.abort_all_tasks = True
        if self.ydl_instance:
            # 尝试停止下载
            pass
        
        self.log_message("正在停止下载...", "warning")

    def process_queue(self):
        """处理下载队列"""
        while True:
            try:
                task = self.download_queue.get(timeout=1)
                # 处理任务
                self.download_queue.task_done()
            except queue.Empty:
                continue

    def process_results(self):
        """处理结果队列"""
        try:
            while not self.result_queue.empty():
                result = self.result_queue.get()
                if result[0] == "log":
                    level, message = result[1], result[2]
                    self.log_message(message, level.lower())
                elif result[0] in ["info", "success", "error", "warning"]:
                    self.log_message(result[1], result[0])
        except Exception as e:
            pass
        
        self.root.after(100, self.process_results)

    def log_message(self, message, level="info"):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, formatted_message, level)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def clear_logs(self):
        """清空日志"""
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
            self.log_message(f"加载历史记录失败: {str(e)}", "error")

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
            
            # 只保留最近50条记录
            if len(self.download_history) > 50:
                self.download_history = self.download_history[-50:]
            
            with open("download_history.json", "w", encoding="utf-8") as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"保存历史记录失败: {str(e)}", "error")

    def show_history(self):
        """显示下载历史"""
        if not self.download_history:
            messagebox.showinfo("下载历史", "暂无下载历史记录")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("800x500")
        
        # 居中显示
        x = self.root.winfo_x() + (self.root.winfo_width() - 800) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        history_window.geometry(f"800x500+{x}+{y}")
        
        # 创建表格
        columns = ("时间", "标题", "格式", "保存路径")
        tree = ttk.Treeview(history_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            if col == "标题":
                tree.column(col, width=300)
            elif col == "保存路径":
                tree.column(col, width=200)
            else:
                tree.column(col, width=100)
        
        # 添加数据
        for entry in reversed(self.download_history):
            tree.insert("", "end", values=(
                entry["timestamp"],
                entry["title"][:50] + "..." if len(entry["title"]) > 50 else entry["title"],
                entry["format_id"],
                entry["save_path"]
            ))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def main():
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
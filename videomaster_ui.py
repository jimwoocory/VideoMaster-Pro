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
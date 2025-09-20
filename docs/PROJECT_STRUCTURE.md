# 项目结构说明

## 📁 目录结构

```
VideoMaster-Pro/
├── 📄 README.md                    # 项目主文档
├── 📄 CHANGELOG.md                 # 更新日志
├── 📄 RELEASE_INFO.json            # 发布信息
├── 📄 requirements.txt             # Python依赖
├── 📄 .gitignore                   # Git忽略文件
├── 📄 .gitattributes               # Git LFS配置
│
├── 📁 src/                         # 源代码目录
│   ├── videomaster_pro_official.py # 主程序
│   ├── requirements.txt            # 依赖列表
│   └── setup_and_run.bat          # 一键运行脚本
│
├── 📁 build_scripts/               # 打包脚本目录
│   ├── build_complete_with_ffmpeg.py # 完整版打包
│   ├── build_official.py          # 标准打包
│   ├── quick_build.py              # 快速打包
│   └── download_ffmpeg.py          # FFmpeg下载脚本
│
├── 📁 tools/                       # 工具文件目录
│   ├── ffmpeg.exe                  # 视频处理工具 (167.3MB)
│   ├── ffprobe.exe                 # 媒体分析工具 (167.1MB)
│   └── yt-dlp.exe                  # YouTube下载引擎 (17.5MB)
│
├── 📁 releases/                    # 发布版本目录
│   ├── dist/                       # PyInstaller输出
│   │   └── VideoMaster_Pro_Complete.exe # 完整版可执行文件 (158.2MB)
│   └── VideoMaster_Pro_Complete_Portable/ # 便携版
│       ├── VideoMaster_Pro_Complete.exe
│       ├── README.md
│       ├── 启动程序.bat
│       └── ffmpeg/                 # 工具备份
│
├── 📁 docs/                        # 文档目录
│   └── (待添加使用文档)
│
└── 📁 tests/                       # 测试目录
    └── (待添加测试文件)
```

## 🎯 核心文件说明

### 源代码文件
- `videomaster_pro_official.py` - 主程序，包含完整GUI和下载功能
- `requirements.txt` - Python依赖包列表
- `setup_and_run.bat` - Windows一键安装运行脚本

### 打包脚本
- `build_complete_with_ffmpeg.py` - 完整版打包，包含所有工具
- `build_official.py` - 标准版打包脚本
- `quick_build.py` - 快速打包脚本

### 工具文件
- `ffmpeg.exe` - FFmpeg视频处理工具
- `ffprobe.exe` - FFmpeg媒体信息分析工具
- `yt-dlp.exe` - YouTube下载核心引擎

### 发布文件
- `VideoMaster_Pro_Complete.exe` - 单文件完整版可执行程序
- `VideoMaster_Pro_Complete_Portable/` - 便携版包，包含说明文档

## 🔧 使用方式

### 开发者
```bash
# 克隆仓库
git clone https://github.com/your-username/VideoMaster-Pro.git
cd VideoMaster-Pro

# 安装依赖
pip install -r requirements.txt

# 运行源码版本
python src/videomaster_pro_official.py

# 打包完整版
python build_scripts/build_complete_with_ffmpeg.py
```

### 普通用户
```bash
# 下载发布版本
# 方式1: 直接运行可执行文件
releases/dist/VideoMaster_Pro_Complete.exe

# 方式2: 使用便携版
releases/VideoMaster_Pro_Complete_Portable/启动程序.bat
```

## 📦 文件大小说明

| 文件 | 大小 | 说明 |
|------|------|------|
| videomaster_pro_official.py | ~50KB | 主程序源码 |
| VideoMaster_Pro_Complete.exe | 158.2MB | 完整版可执行文件 |
| ffmpeg.exe | 167.3MB | 视频处理工具 |
| ffprobe.exe | 167.1MB | 媒体分析工具 |
| yt-dlp.exe | 17.5MB | 下载引擎 |

## 🌐 Git LFS说明

由于包含大文件，项目使用Git LFS管理：
- 所有.exe文件通过Git LFS存储
- 克隆时需要安装Git LFS: `git lfs install`
- 大文件会在需要时下载

## 🔄 更新流程

1. 修改源代码
2. 更新版本号和文档
3. 运行打包脚本
4. 测试功能
5. 提交到Git
6. 创建GitHub Release

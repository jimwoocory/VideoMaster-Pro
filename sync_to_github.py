#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub同步脚本 - 上传VideoMaster Pro完整项目
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_git_command(cmd, description=""):
    """运行Git命令"""
    print(f"\n🔄 {description}")
    print(f"执行命令: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print("✅ 输出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 错误: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        return False

def create_gitignore():
    """创建.gitignore文件"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
temp_ffmpeg/
*.zip
download_history.json
.codebuddy/

# Large files (use Git LFS)
*.exe
ffmpeg.exe
ffprobe.exe
yt-dlp.exe
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore 文件创建完成")

def create_release_info():
    """创建发布信息"""
    release_info = {
        "version": "2.0",
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "title": "VideoMaster Pro v2.0 - YouTube Music完整支持版",
        "description": "完全解决YouTube Music链接问题，内置FFmpeg工具链",
        "features": [
            "🎵 YouTube Music链接完整支持",
            "📦 内置FFmpeg工具链 (ffmpeg.exe, ffprobe.exe)",
            "🎬 格式查询弹窗功能",
            "📋 批量下载支持",
            "📊 下载历史记录",
            "🎨 现代化界面设计",
            "🌐 智能代理配置",
            "🔧 完整错误诊断"
        ],
        "fixes": [
            "修复YouTube Music自动播放列表链接无法下载问题",
            "修复复杂URL参数处理问题",
            "优化网络连接稳定性",
            "改进错误提示和诊断功能"
        ],
        "files": {
            "source": [
                "videomaster_pro_official.py",
                "requirements.txt",
                "setup_and_run.bat"
            ],
            "executables": [
                "VideoMaster_Pro_Complete.exe (158.2 MB)",
                "VideoMaster_Pro_Complete_Portable/ (便携版)"
            ],
            "tools": [
                "ffmpeg.exe (167.3 MB)",
                "ffprobe.exe (167.1 MB)", 
                "yt-dlp.exe (17.5 MB)"
            ],
            "build_scripts": [
                "build_complete_with_ffmpeg.py",
                "build_official.py",
                "quick_build.py"
            ]
        },
        "test_links": [
            "https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1"
        ]
    }
    
    with open('RELEASE_INFO.json', 'w', encoding='utf-8') as f:
        json.dump(release_info, f, ensure_ascii=False, indent=2)
    
    print("✅ 发布信息文件创建完成")

def create_changelog():
    """创建更新日志"""
    changelog_content = """# 更新日志

## [2.0] - 2025-09-20

### 🎵 YouTube Music支持
- **新增** 完整支持YouTube Music自动播放列表链接
- **修复** RD前缀播放列表无法下载问题
- **优化** 智能提取单个视频ID功能
- **改进** 复杂URL参数处理逻辑

### 📦 完整工具链
- **内置** FFmpeg.exe (167.3 MB) - 视频处理核心
- **内置** FFprobe.exe (167.1 MB) - 媒体信息分析
- **内置** yt-dlp.exe (17.5 MB) - YouTube下载引擎
- **打包** 单文件可执行版本 (158.2 MB)

### 🎨 界面升级
- **重构** 现代化卡片式界面设计
- **新增** 启动画面和加载动画
- **优化** 响应式布局和滚动支持
- **改进** 用户操作体验

### 🌐 网络优化
- **简化** 代理设置 (固定端口7897)
- **增强** 连接稳定性和重试机制
- **新增** 智能错误诊断功能
- **优化** 超时和重试参数

### 🔧 功能完善
- **保留** 所有原有功能模块
- **优化** 格式查询弹窗体验
- **改进** 批量下载处理逻辑
- **完善** 下载历史记录功能

### 🛠️ 开发工具
- **新增** 完整版打包脚本
- **优化** 依赖管理和安装流程
- **改进** 错误处理和日志系统
- **完善** 项目文档和说明

## [1.0] - 2025-09-19

### 初始版本
- 基础YouTube视频下载功能
- 简单的GUI界面
- 基本的格式选择功能
"""
    
    with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
        f.write(changelog_content)
    
    print("✅ 更新日志创建完成")

def setup_git_lfs():
    """设置Git LFS处理大文件"""
    lfs_config = """*.exe filter=lfs diff=lfs merge=lfs -text
ffmpeg.exe filter=lfs diff=lfs merge=lfs -text
ffprobe.exe filter=lfs diff=lfs merge=lfs -text
yt-dlp.exe filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
"""
    
    with open('.gitattributes', 'w', encoding='utf-8') as f:
        f.write(lfs_config)
    
    print("✅ Git LFS配置创建完成")

def organize_files():
    """整理项目文件结构"""
    print("📁 整理项目文件结构...")
    
    # 创建目录结构
    directories = [
        'src',           # 源代码
        'build_scripts', # 打包脚本
        'tools',         # 工具文件
        'releases',      # 发布版本
        'docs',          # 文档
        'tests'          # 测试文件
    ]
    
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ 创建目录: {dir_name}/")
    
    # 移动源代码文件
    source_files = [
        'videomaster_pro_official.py',
        'requirements.txt',
        'setup_and_run.bat'
    ]
    
    for file in source_files:
        if os.path.exists(file):
            # 复制而不是移动，保持原位置
            import shutil
            shutil.copy2(file, f'src/{file}')
            print(f"✅ 复制到 src/: {file}")
    
    # 移动打包脚本
    build_files = [
        'build_complete_with_ffmpeg.py',
        'build_official.py', 
        'quick_build.py',
        'download_ffmpeg.py'
    ]
    
    for file in build_files:
        if os.path.exists(file):
            import shutil
            shutil.copy2(file, f'build_scripts/{file}')
            print(f"✅ 复制到 build_scripts/: {file}")
    
    # 移动工具文件
    tool_files = ['ffmpeg.exe', 'ffprobe.exe', 'yt-dlp.exe']
    for file in tool_files:
        if os.path.exists(file):
            import shutil
            shutil.copy2(file, f'tools/{file}')
            print(f"✅ 复制到 tools/: {file}")
    
    # 移动发布文件
    if os.path.exists('dist'):
        import shutil
        if os.path.exists('releases/dist'):
            shutil.rmtree('releases/dist')
        shutil.copytree('dist', 'releases/dist')
        print("✅ 复制到 releases/: dist/")
    
    if os.path.exists('VideoMaster_Pro_Complete_Portable'):
        import shutil
        if os.path.exists('releases/VideoMaster_Pro_Complete_Portable'):
            shutil.rmtree('releases/VideoMaster_Pro_Complete_Portable')
        shutil.copytree('VideoMaster_Pro_Complete_Portable', 'releases/VideoMaster_Pro_Complete_Portable')
        print("✅ 复制到 releases/: VideoMaster_Pro_Complete_Portable/")

def init_git_repo():
    """初始化Git仓库"""
    print("\n🔧 初始化Git仓库...")
    
    # 检查是否已经是Git仓库
    if os.path.exists('.git'):
        print("✅ Git仓库已存在")
    else:
        if not run_git_command("git init", "初始化Git仓库"):
            return False
    
    # 设置Git配置（如果需要）
    run_git_command("git config --global init.defaultBranch main", "设置默认分支为main")
    
    return True

def sync_to_github():
    """同步到GitHub"""
    print("\n🚀 开始同步到GitHub...")
    
    # 添加所有文件
    if not run_git_command("git add .", "添加所有文件"):
        return False
    
    # 检查状态
    run_git_command("git status", "检查Git状态")
    
    # 提交更改
    commit_message = f"🎵 VideoMaster Pro v2.0 - YouTube Music完整支持版\n\n✨ 主要更新:\n- 完全支持YouTube Music链接\n- 内置FFmpeg工具链\n- 现代化界面设计\n- 完整功能保留\n\n📦 发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    if not run_git_command(f'git commit -m "{commit_message}"', "提交更改"):
        print("⚠️ 可能没有新的更改需要提交")
    
    # 添加远程仓库（如果需要）
    print("\n📡 配置远程仓库...")
    print("请手动执行以下命令来添加GitHub远程仓库:")
    print("git remote add origin https://github.com/your-username/VideoMaster-Pro.git")
    print("git branch -M main")
    print("git push -u origin main")
    
    return True

def create_project_structure_doc():
    """创建项目结构文档"""
    structure_doc = """# 项目结构说明

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
"""
    
    with open('docs/PROJECT_STRUCTURE.md', 'w', encoding='utf-8') as f:
        f.write(structure_doc)
    
    print("✅ 项目结构文档创建完成")

def main():
    """主函数"""
    print("🚀 VideoMaster Pro GitHub同步工具")
    print("=" * 60)
    
    # 1. 创建必要文件
    print("\n📝 创建项目文件...")
    create_gitignore()
    create_release_info()
    create_changelog()
    setup_git_lfs()
    
    # 2. 整理文件结构
    organize_files()
    create_project_structure_doc()
    
    # 3. 初始化Git仓库
    if not init_git_repo():
        print("❌ Git仓库初始化失败")
        return
    
    # 4. 同步到GitHub
    if not sync_to_github():
        print("❌ GitHub同步失败")
        return
    
    print("\n" + "=" * 60)
    print("🎉 项目准备完成!")
    print("=" * 60)
    
    print("\n📋 下一步操作:")
    print("1. 在GitHub上创建新仓库 'VideoMaster-Pro'")
    print("2. 执行以下命令连接远程仓库:")
    print("   git remote add origin https://github.com/your-username/VideoMaster-Pro.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("\n3. 安装Git LFS (如果尚未安装):")
    print("   git lfs install")
    print("   git lfs track '*.exe'")
    print("   git add .gitattributes")
    print("   git commit -m 'Add Git LFS tracking'")
    print("   git push")
    
    print("\n✨ 项目特色:")
    print("   • 完整的README文档")
    print("   • 专业的项目结构")
    print("   • Git LFS大文件管理")
    print("   • 详细的发布信息")
    print("   • 完整的更新日志")
    
    print("\n🎵 YouTube Music链接测试:")
    print("   https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1")

if __name__ == "__main__":
    main()
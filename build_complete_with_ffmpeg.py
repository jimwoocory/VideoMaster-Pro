#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoMaster Pro 完整版打包脚本
包含 FFmpeg 和所有依赖的完整打包方案
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description=""):
    """运行命令并显示进度"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
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

def check_ffmpeg_files():
    """检查FFmpeg文件"""
    required_files = ['ffmpeg.exe', 'ffprobe.exe', 'yt-dlp.exe']
    missing_files = []
    
    print("\n🔍 检查FFmpeg和yt-dlp文件...")
    
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024 * 1024)
            print(f"✅ {file} ({size:.1f} MB)")
        else:
            print(f"❌ 缺少 {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ 缺少以下文件: {', '.join(missing_files)}")
        print("请确保以下文件在当前目录中:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    print("✅ 所有必需文件检查通过")
    return True

def install_dependencies():
    """安装依赖"""
    print("\n📦 安装依赖包...")
    
    # 升级pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "升级pip"):
        print("⚠️ pip升级失败，继续安装依赖...")
    
    # 安装基础依赖
    dependencies = [
        "yt-dlp>=2023.12.30",
        "requests>=2.31.0",
        "pyinstaller>=6.0.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"安装 {dep}"):
            print(f"❌ 安装 {dep} 失败")
            return False
    
    print("✅ 所有依赖安装完成")
    return True

def create_complete_spec_file():
    """创建包含FFmpeg的完整PyInstaller规格文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['videomaster_pro_official.py'],
    pathex=[],
    binaries=[
        ('ffmpeg.exe', '.'),
        ('ffprobe.exe', '.'),
        ('yt-dlp.exe', '.'),
    ],
    datas=[
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.downloader',
        'yt_dlp.postprocessor',
        'yt_dlp.utils',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'websockets',
        'brotli',
        'mutagen',
        'pycryptodomex',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'threading',
        'queue',
        'logging',
        'json',
        'datetime',
        'subprocess',
        'platform',
        'traceback',
        'urllib.parse',
        'pathlib'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoMaster_Pro_Complete',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None
)
'''
    
    with open('videomaster_pro_complete.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 完整版PyInstaller规格文件创建完成")

def build_complete_executable():
    """构建包含FFmpeg的完整可执行文件"""
    print("\n🔨 开始构建完整版可执行文件...")
    
    # 创建规格文件
    create_complete_spec_file()
    
    # 清理之前的构建
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"🗑️ 清理旧的 {folder} 文件夹")
            shutil.rmtree(folder)
    
    # 构建
    cmd = f"{sys.executable} -m PyInstaller videomaster_pro_complete.spec --clean --noconfirm"
    
    if not run_command(cmd, "构建完整版可执行文件"):
        print("❌ 构建失败")
        return False
    
    # 检查输出文件
    exe_path = Path("dist/VideoMaster_Pro_Complete.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ 完整版构建成功!")
        print(f"📁 输出文件: {exe_path.absolute()}")
        print(f"📏 文件大小: {size_mb:.1f} MB")
        return True
    else:
        print("❌ 未找到输出文件")
        return False

def create_complete_portable_package():
    """创建完整版便携包"""
    print("\n📦 创建完整版便携包...")
    
    package_dir = Path("VideoMaster_Pro_Complete_Portable")
    
    # 创建包目录
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # 复制可执行文件
    exe_source = Path("dist/VideoMaster_Pro_Complete.exe")
    if exe_source.exists():
        shutil.copy2(exe_source, package_dir / "VideoMaster_Pro_Complete.exe")
    
    # 复制FFmpeg文件（作为备份）
    ffmpeg_dir = package_dir / "ffmpeg"
    ffmpeg_dir.mkdir()
    
    for file in ['ffmpeg.exe', 'ffprobe.exe', 'yt-dlp.exe']:
        if os.path.exists(file):
            shutil.copy2(file, ffmpeg_dir / file)
    
    # 创建完整版说明文件
    readme_content = """# VideoMaster Pro 完整版 v2.0

## 🎬 完整功能版本

这是包含所有依赖的完整版本，内置了以下组件：
- ✅ FFmpeg.exe (视频处理核心)
- ✅ FFprobe.exe (媒体信息分析)
- ✅ yt-dlp.exe (YouTube下载引擎)
- ✅ 所有Python依赖库

## 🚀 使用方法

### 直接运行
双击 `VideoMaster_Pro_Complete.exe` 即可启动程序

### 功能特性
✅ **YouTube Music完整支持**
- 支持YouTube Music自动播放列表
- 智能提取单个视频ID
- 自动处理复杂链接参数

✅ **完整下载功能**
- 格式查询和选择弹窗
- 批量下载支持
- 字幕下载
- 多线程下载
- 视频转码功能

✅ **网络配置**
- 简化代理设置 (端口7897)
- 智能连接模式
- 详细错误诊断

✅ **用户体验**
- 现代化界面设计
- 下载历史记录
- 实时进度显示
- 启动画面

## 🔧 网络配置

### 代理设置
如果使用代理软件：
1. 确保代理软件正在运行
2. 勾选"使用代理"
3. 输入代理地址：`http://127.0.0.1:7897`

### 直连模式
如果可以直接访问YouTube：
- 取消勾选"使用代理"选项

## 🎵 YouTube Music链接支持

完全支持YouTube Music链接，包括：
```
https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1
```

程序会自动：
- 识别YouTube Music播放列表
- 提取单个视频进行处理
- 显示详细链接分析

## 📋 使用步骤

1. **启动程序**：双击可执行文件
2. **输入链接**：粘贴YouTube或YouTube Music链接
3. **分析链接**：点击"分析链接"查看结构（可选）
4. **获取信息**：点击"获取信息"查看视频详情
5. **选择格式**：点击"查询格式"选择下载质量
6. **配置设置**：设置保存路径和其他选项
7. **开始下载**：点击"开始下载"

## 🛠️ 故障排除

### 网络问题
- 检查代理软件状态
- 尝试切换直连/代理模式
- 查看程序日志获取详细错误信息

### 下载问题
- 确保保存路径有写入权限
- 检查磁盘空间是否充足
- 尝试不同的格式ID

## 📦 文件说明

- `VideoMaster_Pro_Complete.exe` - 主程序（包含所有依赖）
- `ffmpeg/` - FFmpeg工具备份文件夹
  - `ffmpeg.exe` - 视频处理工具
  - `ffprobe.exe` - 媒体信息工具
  - `yt-dlp.exe` - YouTube下载工具

## 🔒 安全说明

本程序完全开源，不包含任何恶意代码：
- 仅用于合法的视频下载
- 不收集用户隐私信息
- 所有网络请求均为YouTube API调用

---
VideoMaster Pro 完整版 v2.0
包含FFmpeg和所有依赖的完整解决方案
"""
    
    with open(package_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 创建启动脚本
    batch_content = """@echo off
chcp 65001 >nul
title VideoMaster Pro 完整版 v2.0

echo.
echo ==========================================
echo   VideoMaster Pro 完整版 v2.0
echo ==========================================
echo.
echo 🎵 完整支持YouTube Music链接
echo 📦 内置FFmpeg和所有依赖
echo 🚀 开箱即用，无需安装
echo.
echo 正在启动程序...
echo.

start "" "VideoMaster_Pro_Complete.exe"

echo.
echo 程序已启动！
echo 如遇问题请查看程序内的日志信息
echo.
pause
"""
    
    with open(package_dir / "启动程序.bat", 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    # 创建版本信息文件
    version_info = {
        "name": "VideoMaster Pro 完整版",
        "version": "2.0",
        "build_date": "2025-09-20",
        "features": [
            "YouTube Music链接完整支持",
            "内置FFmpeg工具链",
            "格式查询弹窗功能",
            "批量下载支持",
            "下载历史记录",
            "现代化界面设计"
        ],
        "included_tools": [
            "ffmpeg.exe",
            "ffprobe.exe", 
            "yt-dlp.exe"
        ],
        "dependencies": [
            "yt-dlp>=2023.12.30",
            "requests>=2.31.0",
            "tkinter (内置)"
        ]
    }
    
    import json
    with open(package_dir / "version_info.json", 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 完整版便携包创建完成: {package_dir.absolute()}")
    return True

def main():
    """主函数"""
    print("🚀 VideoMaster Pro 完整版打包工具")
    print("包含 FFmpeg + yt-dlp + 所有依赖")
    print("=" * 60)
    
    # 检查Python版本
    version = sys.version_info
    print(f"🐍 Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        input("按回车键退出...")
        return
    
    print("✅ Python版本符合要求")
    
    # 检查源文件
    if not os.path.exists('videomaster_pro_official.py'):
        print("❌ 未找到源文件 videomaster_pro_official.py")
        input("按回车键退出...")
        return
    
    print("✅ 源文件检查通过")
    
    # 检查FFmpeg文件
    if not check_ffmpeg_files():
        print("\n❌ FFmpeg文件检查失败")
        print("请确保以下文件在当前目录中:")
        print("   • ffmpeg.exe")
        print("   • ffprobe.exe") 
        print("   • yt-dlp.exe")
        input("按回车键退出...")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败")
        input("按回车键退出...")
        return
    
    # 构建完整版可执行文件
    if not build_complete_executable():
        print("❌ 完整版构建失败")
        input("按回车键退出...")
        return
    
    # 创建完整版便携包
    if not create_complete_portable_package():
        print("❌ 完整版便携包创建失败")
        input("按回车键退出...")
        return
    
    print("\n" + "=" * 60)
    print("🎉 完整版打包完成!")
    print("=" * 60)
    
    # 显示文件大小信息
    exe_path = Path("dist/VideoMaster_Pro_Complete.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"📁 主程序: VideoMaster_Pro_Complete.exe ({size_mb:.1f} MB)")
    
    print("📦 输出文件:")
    print("   • dist/VideoMaster_Pro_Complete.exe (完整版单文件)")
    print("   • VideoMaster_Pro_Complete_Portable/ (完整版便携包)")
    
    print("\n✨ 完整版特性:")
    print("   • 内置 FFmpeg.exe (视频处理)")
    print("   • 内置 FFprobe.exe (媒体分析)")
    print("   • 内置 yt-dlp.exe (下载引擎)")
    print("   • 完整支持YouTube Music链接")
    print("   • 所有功能开箱即用")
    
    print("\n🚀 使用方法:")
    print("   • 单文件版: 直接运行 VideoMaster_Pro_Complete.exe")
    print("   • 便携版: 解压后运行 启动程序.bat")
    
    print("\n💡 测试建议:")
    print("   • 测试链接: https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1")
    print("   • 代理设置: http://127.0.0.1:7897")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoMaster Pro 快速打包脚本
"""

import os
import sys
import subprocess

def quick_build():
    """快速打包"""
    print("🚀 VideoMaster Pro 快速打包")
    print("=" * 50)
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("📦 安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 快速打包命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "VideoMaster_Pro_Official_v2",
        "--add-data", "requirements.txt;.",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "requests",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.scrolledtext",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        "videomaster_pro_official.py"
    ]
    
    print("🔨 开始快速打包...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 快速打包完成!")
        print("📁 输出文件: dist/VideoMaster_Pro_Official_v2.exe")
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")

if __name__ == "__main__":
    quick_build()
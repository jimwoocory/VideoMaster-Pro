#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动下载FFmpeg工具
"""

import os
import sys
import requests
import zipfile
import shutil
from pathlib import Path

def download_file(url, filename):
    """下载文件并显示进度"""
    print(f"📥 下载 {filename}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print(f"\n✅ {filename} 下载完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False

def download_ffmpeg():
    """下载FFmpeg工具"""
    print("🔽 开始下载FFmpeg工具...")
    
    # FFmpeg下载链接（Windows版本）
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    # 下载FFmpeg
    if not download_file(ffmpeg_url, "ffmpeg.zip"):
        return False
    
    # 解压FFmpeg
    print("📦 解压FFmpeg...")
    try:
        with zipfile.ZipFile("ffmpeg.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_ffmpeg")
        
        # 查找ffmpeg.exe和ffprobe.exe
        for root, dirs, files in os.walk("temp_ffmpeg"):
            for file in files:
                if file in ['ffmpeg.exe', 'ffprobe.exe']:
                    src = os.path.join(root, file)
                    dst = file
                    shutil.copy2(src, dst)
                    print(f"✅ 提取 {file}")
        
        # 清理临时文件
        shutil.rmtree("temp_ffmpeg")
        os.remove("ffmpeg.zip")
        
        print("✅ FFmpeg工具下载完成")
        return True
        
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 FFmpeg自动下载工具")
    print("=" * 40)
    
    # 检查是否已存在
    existing_files = []
    for file in ['ffmpeg.exe', 'ffprobe.exe']:
        if os.path.exists(file):
            existing_files.append(file)
    
    if existing_files:
        print(f"✅ 已存在文件: {', '.join(existing_files)}")
    
    missing_files = [f for f in ['ffmpeg.exe', 'ffprobe.exe'] if not os.path.exists(f)]
    
    if not missing_files:
        print("✅ 所有FFmpeg文件已存在")
        return
    
    print(f"📋 需要下载: {', '.join(missing_files)}")
    
    # 下载FFmpeg
    if download_ffmpeg():
        print("\n🎉 FFmpeg下载完成!")
        print("现在可以运行完整版打包脚本了")
    else:
        print("\n❌ FFmpeg下载失败")
        print("请手动下载FFmpeg并将ffmpeg.exe和ffprobe.exe放在当前目录")

if __name__ == "__main__":
    main()
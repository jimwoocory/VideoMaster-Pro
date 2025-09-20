import PyInstaller.__main__
import os
import sys
import shutil
import subprocess

def download_dependencies():
    """下载必要的依赖文件"""
    print("正在准备依赖文件...")
    
    # 创建依赖文件夹
    deps_dir = "dependencies"
    if not os.path.exists(deps_dir):
        os.makedirs(deps_dir)
    
    # 检查并下载 yt-dlp
    yt_dlp_path = os.path.join(deps_dir, "yt-dlp.exe")
    if not os.path.exists(yt_dlp_path):
        print("下载 yt-dlp.exe...")
        try:
            import urllib.request
            urllib.request.urlretrieve(
                "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
                yt_dlp_path
            )
            print("✓ yt-dlp.exe 下载完成")
        except Exception as e:
            print(f"✗ yt-dlp.exe 下载失败: {e}")
            print("请手动下载 yt-dlp.exe 到 dependencies 文件夹")
    
    # 检查并下载 ffmpeg
    ffmpeg_path = os.path.join(deps_dir, "ffmpeg.exe")
    ffprobe_path = os.path.join(deps_dir, "ffprobe.exe")
    
    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
        print("请手动下载 ffmpeg.exe 和 ffprobe.exe 到 dependencies 文件夹")
        print("下载地址: https://www.gyan.dev/ffmpeg/builds/")
    
    return deps_dir

def build_with_dependencies():
    """构建包含依赖的可执行文件"""
    deps_dir = download_dependencies()
    
    # PyInstaller 参数
    args = [
        '--onefile',
        '--windowed',
        '--name=VideoMaster Pro',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build',
        '--clean',
        '--noconfirm',
        '--icon=NONE',  # 可以后续添加图标
    ]
    
    # 添加依赖文件
    if os.path.exists(os.path.join(deps_dir, "yt-dlp.exe")):
        args.append(f'--add-binary={os.path.join(deps_dir, "yt-dlp.exe")};.')
    
    if os.path.exists(os.path.join(deps_dir, "ffmpeg.exe")):
        args.append(f'--add-binary={os.path.join(deps_dir, "ffmpeg.exe")};.')
    
    if os.path.exists(os.path.join(deps_dir, "ffprobe.exe")):
        args.append(f'--add-binary={os.path.join(deps_dir, "ffprobe.exe")};.')
    
    # 添加主程序文件
    args.append('videomaster_pro.py')
    
    print("开始构建 VideoMaster Pro...")
    print(f"构建参数: {' '.join(args)}")
    
    # 运行 PyInstaller
    PyInstaller.__main__.run(args)
    
    print("构建完成！")
    print("可执行文件位置: dist/VideoMaster Pro.exe")

if __name__ == "__main__":
    build_with_dependencies()
import PyInstaller.__main__
import os
import shutil
import zipfile

def main():
    print("🎬 VideoMaster Pro 最终打包")
    print("=" * 50)
    
    # 1. 准备 FFmpeg
    print("📦 准备 FFmpeg...")
    if os.path.exists("ffmpeg.zip"):
        # 解压 ffmpeg
        with zipfile.ZipFile("ffmpeg.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_ffmpeg")
        
        # 查找并复制 ffmpeg.exe 和 ffprobe.exe
        for root, dirs, files in os.walk("temp_ffmpeg"):
            for file in files:
                if file in ["ffmpeg.exe", "ffprobe.exe"]:
                    src = os.path.join(root, file)
                    dst = file
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        print(f"✓ 复制 {file}")
        
        # 清理临时文件
        shutil.rmtree("temp_ffmpeg")
    
    # 2. 检查文件
    required_files = ["videomaster_pro_compact_fixed.py", "yt-dlp.exe", "ffmpeg.exe"]
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} 缺失")
            return
    
    # 3. 构建
    print("\n🚀 开始打包...")
    
    args = [
        '--onefile',
        '--windowed',
        '--name=VideoMaster Pro Complete',
        '--distpath=dist',
        '--clean',
        '--noconfirm',
        '--add-binary=yt-dlp.exe;.',
        '--add-binary=ffmpeg.exe;.',
        '--hidden-import=yt_dlp',
        '--hidden-import=urllib3',
        '--hidden-import=certifi',
        'videomaster_pro_compact_fixed.py'
    ]
    
    # 添加 ffprobe.exe 如果存在
    if os.path.exists("ffprobe.exe"):
        args.insert(-1, '--add-binary=ffprobe.exe;.')
    
    try:
        PyInstaller.__main__.run(args)
        
        exe_path = "dist/VideoMaster Pro Complete.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n🎉 打包成功！")
            print(f"📁 文件: {exe_path}")
            print(f"📦 大小: {size_mb:.1f} MB")
            
            # 清理临时文件
            for temp_file in ["ffmpeg.exe", "ffprobe.exe"]:
                if os.path.exists(temp_file) and temp_file != "yt-dlp.exe":
                    os.remove(temp_file)
            
            return True
        else:
            print("❌ 打包失败")
            return False
            
    except Exception as e:
        print(f"❌ 打包错误: {e}")
        return False

if __name__ == "__main__":
    main()
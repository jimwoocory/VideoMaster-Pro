import os
import subprocess
import sys

def build_videomaster():
    """灵活的构建脚本 - 支持部分依赖"""
    
    # 检查依赖文件
    deps_dir = "dependencies"
    available_files = []
    missing_files = []
    
    files_to_check = {
        "yt-dlp.exe": "YouTube下载核心",
        "ffmpeg.exe": "视频处理（可选）", 
        "ffprobe.exe": "视频信息（可选）"
    }
    
    print("检查依赖文件...")
    for file, description in files_to_check.items():
        file_path = os.path.join(deps_dir, file)
        if os.path.exists(file_path):
            print(f"✓ 找到 {file} - {description}")
            available_files.append(file)
        else:
            print(f"✗ 缺少 {file} - {description}")
            missing_files.append(file)
    
    # 检查是否有核心文件
    if "yt-dlp.exe" not in available_files:
        print("\n❌ 缺少核心文件 yt-dlp.exe，无法构建")
        return False
    
    # 显示构建信息
    print(f"\n📦 准备构建 VideoMaster Pro")
    print(f"✅ 包含文件: {', '.join(available_files)}")
    if missing_files:
        print(f"⚠️  缺少文件: {', '.join(missing_files)}")
        print("   (这些功能将在运行时检查系统PATH中的对应程序)")
    
    # 构建 PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed", 
        "--name=VideoMaster Pro",
        "--distpath=dist",
        "--workpath=build", 
        "--specpath=build",
        "--clean",
        "--noconfirm"
    ]
    
    # 添加可用的依赖文件
    for file in available_files:
        file_path = os.path.abspath(os.path.join(deps_dir, file))
        cmd.extend(["--add-binary", f"{file_path};."])
    
    # 添加主程序
    cmd.append("videomaster_pro.py")
    
    print(f"\n🔨 执行构建命令:")
    print(" ".join(cmd))
    
    # 执行构建
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n🎉 构建成功！")
        print("📁 可执行文件位置: dist/VideoMaster Pro.exe")
        
        # 显示功能说明
        print(f"\n📋 功能说明:")
        print(f"✅ YouTube视频下载 - 已包含")
        if "ffmpeg.exe" in available_files:
            print(f"✅ 视频格式转换 - 已包含")
        else:
            print(f"⚠️  视频格式转换 - 需要系统安装ffmpeg")
        
        if missing_files:
            print(f"\n💡 提示: 如需完整功能，请:")
            print(f"   1. 将缺少的文件放入 dependencies 文件夹")
            print(f"   2. 重新运行构建脚本")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败: {e}")
        if e.stderr:
            print(f"错误详情: {e.stderr}")
        return False

if __name__ == "__main__":
    build_videomaster()
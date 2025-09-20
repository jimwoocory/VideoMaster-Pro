import os
import subprocess
import sys

def build_videomaster():
    """简单的构建脚本"""
    
    # 检查依赖文件
    deps_dir = "dependencies"
    required_files = ["yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe"]
    
    print("检查依赖文件...")
    missing_files = []
    for file in required_files:
        file_path = os.path.join(deps_dir, file)
        if os.path.exists(file_path):
            print(f"✓ 找到 {file}")
        else:
            print(f"✗ 缺少 {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n缺少以下文件: {', '.join(missing_files)}")
        print("请将这些文件放入 dependencies 文件夹后重新运行构建")
        return False
    
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
    
    # 添加依赖文件
    for file in required_files:
        file_path = os.path.join(deps_dir, file)
        cmd.extend([f"--add-binary={file_path};."])
    
    # 添加主程序
    cmd.append("videomaster_pro.py")
    
    print(f"\n执行构建命令:")
    print(" ".join(cmd))
    
    # 执行构建
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print("可执行文件位置: dist/VideoMaster Pro.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

if __name__ == "__main__":
    build_videomaster()
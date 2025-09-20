import PyInstaller.__main__
import os
import sys
import shutil
import zipfile
import subprocess

def prepare_dependencies():
    """准备所有依赖文件"""
    print("🔧 正在准备依赖文件...")
    
    # 创建临时依赖文件夹
    deps_dir = "temp_dependencies"
    if os.path.exists(deps_dir):
        shutil.rmtree(deps_dir)
    os.makedirs(deps_dir)
    
    # 1. 复制 yt-dlp.exe
    if os.path.exists("yt-dlp.exe"):
        shutil.copy2("yt-dlp.exe", os.path.join(deps_dir, "yt-dlp.exe"))
        print("✓ yt-dlp.exe 已准备")
    else:
        print("✗ 未找到 yt-dlp.exe")
        return False
    
    # 2. 解压 ffmpeg.zip
    if os.path.exists("ffmpeg.zip"):
        print("📦 正在解压 ffmpeg.zip...")
        with zipfile.ZipFile("ffmpeg.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_ffmpeg")
        
        # 查找 ffmpeg.exe 和 ffprobe.exe
        ffmpeg_found = False
        ffprobe_found = False
        
        for root, dirs, files in os.walk("temp_ffmpeg"):
            for file in files:
                if file == "ffmpeg.exe":
                    shutil.copy2(os.path.join(root, file), os.path.join(deps_dir, "ffmpeg.exe"))
                    ffmpeg_found = True
                    print("✓ ffmpeg.exe 已准备")
                elif file == "ffprobe.exe":
                    shutil.copy2(os.path.join(root, file), os.path.join(deps_dir, "ffprobe.exe"))
                    ffprobe_found = True
                    print("✓ ffprobe.exe 已准备")
        
        # 清理临时文件
        if os.path.exists("temp_ffmpeg"):
            shutil.rmtree("temp_ffmpeg")
        
        if not ffmpeg_found or not ffprobe_found:
            print("✗ ffmpeg 文件不完整")
            return False
    else:
        print("✗ 未找到 ffmpeg.zip")
        return False
    
    return deps_dir

def create_resource_script():
    """创建资源路径处理脚本"""
    resource_script = '''
import os
import sys
import tempfile
import shutil

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_tool_path(tool_name):
    """获取工具的路径，如果是打包版本则复制到临时目录"""
    if hasattr(sys, '_MEIPASS'):
        # 打包版本
        tool_path = resource_path(tool_name)
        if os.path.exists(tool_path):
            # 复制到临时目录以便执行
            temp_dir = tempfile.gettempdir()
            temp_tool_path = os.path.join(temp_dir, tool_name)
            if not os.path.exists(temp_tool_path):
                shutil.copy2(tool_path, temp_tool_path)
            return temp_tool_path
    else:
        # 开发版本
        if os.path.exists(tool_name):
            return os.path.abspath(tool_name)
    
    return tool_name  # 回退到系统PATH
'''
    
    with open("resource_utils.py", "w", encoding="utf-8") as f:
        f.write(resource_script)
    
    print("✓ 资源处理脚本已创建")

def modify_main_script():
    """修改主脚本以支持打包"""
    print("🔧 正在修改主脚本...")
    
    # 读取原始脚本
    with open("videomaster_pro_compact_fixed.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 添加资源处理导入
    import_addition = '''import os
import sys
import tempfile
import shutil

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_tool_path(tool_name):
    """获取工具的路径"""
    if hasattr(sys, '_MEIPASS'):
        tool_path = resource_path(tool_name)
        if os.path.exists(tool_path):
            temp_dir = tempfile.gettempdir()
            temp_tool_path = os.path.join(temp_dir, tool_name)
            if not os.path.exists(temp_tool_path):
                shutil.copy2(tool_path, temp_tool_path)
            return temp_tool_path
    else:
        if os.path.exists(tool_name):
            return os.path.abspath(tool_name)
    return tool_name

'''
    
    # 在第一个import之前插入
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('import '):
            insert_pos = i
            break
    
    lines.insert(insert_pos, import_addition)
    
    # 修改 yt_dlp 的使用方式，使用外部 yt-dlp.exe
    modified_content = '\n'.join(lines)
    
    # 替换 yt_dlp 调用为外部工具调用
    modified_content = modified_content.replace(
        'with yt_dlp.YoutubeDL(ydl_opts) as ydl:',
        '''# 使用外部 yt-dlp.exe
        yt_dlp_path = get_tool_path("yt-dlp.exe")
        
        # 构建命令行参数
        cmd = [yt_dlp_path]
        if proxy:
            cmd.extend(["--proxy", proxy])
        cmd.extend(["--quiet", "--no-warnings"])
        
        # 临时使用 yt_dlp 库进行信息获取
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:'''
    )
    
    # 保存修改后的脚本
    with open("videomaster_pro_packaged.py", "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    print("✓ 主脚本已修改并保存为 videomaster_pro_packaged.py")

def build_executable():
    """构建可执行文件"""
    deps_dir = prepare_dependencies()
    if not deps_dir:
        print("❌ 依赖文件准备失败")
        return False
    
    create_resource_script()
    modify_main_script()
    
    print("🚀 开始构建可执行文件...")
    
    # PyInstaller 参数
    args = [
        '--onefile',
        '--windowed',
        '--name=VideoMaster Pro Complete',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build',
        '--clean',
        '--noconfirm',
        '--console',  # 暂时保留控制台以便调试
    ]
    
    # 添加依赖文件
    yt_dlp_path = os.path.join(deps_dir, "yt-dlp.exe")
    ffmpeg_path = os.path.join(deps_dir, "ffmpeg.exe")
    ffprobe_path = os.path.join(deps_dir, "ffprobe.exe")
    
    if os.path.exists(yt_dlp_path):
        args.append(f'--add-binary={yt_dlp_path};.')
        print(f"✓ 添加 yt-dlp.exe")
    
    if os.path.exists(ffmpeg_path):
        args.append(f'--add-binary={ffmpeg_path};.')
        print(f"✓ 添加 ffmpeg.exe")
    
    if os.path.exists(ffprobe_path):
        args.append(f'--add-binary={ffprobe_path};.')
        print(f"✓ 添加 ffprobe.exe")
    
    # 添加隐藏导入
    args.extend([
        '--hidden-import=yt_dlp',
        '--hidden-import=yt_dlp.extractor',
        '--hidden-import=yt_dlp.downloader',
        '--hidden-import=urllib3',
        '--hidden-import=certifi',
        '--hidden-import=charset_normalizer',
    ])
    
    # 主程序文件
    args.append('videomaster_pro_compact_fixed.py')
    
    print(f"构建命令: {' '.join(args)}")
    
    try:
        # 运行 PyInstaller
        PyInstaller.__main__.run(args)
        
        # 清理临时文件
        if os.path.exists(deps_dir):
            shutil.rmtree(deps_dir)
        if os.path.exists("resource_utils.py"):
            os.remove("resource_utils.py")
        if os.path.exists("videomaster_pro_packaged.py"):
            os.remove("videomaster_pro_packaged.py")
        
        print("🎉 构建完成！")
        print("📁 可执行文件位置: dist/VideoMaster Pro Complete.exe")
        print("📦 文件大小:", end=" ")
        
        exe_path = "dist/VideoMaster Pro Complete.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"{size_mb:.1f} MB")
            
            print("\n✅ 打包成功！包含以下组件:")
            print("   • VideoMaster Pro 主程序")
            print("   • yt-dlp.exe (YouTube下载器)")
            print("   • ffmpeg.exe (视频处理)")
            print("   • ffprobe.exe (媒体信息)")
            print("   • 所有Python依赖库")
            
            return True
        else:
            print("❌ 可执行文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🎬 VideoMaster Pro 完整打包工具")
    print("=" * 60)
    
    # 检查必要文件
    required_files = [
        "videomaster_pro_compact_fixed.py",
        "yt-dlp.exe", 
        "ffmpeg.zip"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   • {file}")
        print("\n请确保所有文件都在当前目录中")
        return False
    
    print("✓ 所有必要文件已就绪")
    
    # 开始构建
    success = build_executable()
    
    if success:
        print("\n🎉 打包完成！您现在可以:")
        print("   1. 运行 dist/VideoMaster Pro Complete.exe")
        print("   2. 将 .exe 文件分发给其他用户")
        print("   3. 无需安装Python或其他依赖")
    else:
        print("\n❌ 打包失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    main()
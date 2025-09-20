#!/usr/bin/env python3
"""
简化的GitHub发布脚本
帮助用户快速将VideoMaster Pro发布到GitHub
"""

import os
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    """运行命令"""
    print(f"执行: {cmd}")
    result = os.system(cmd)
    return result == 0

def main():
    print("🚀 VideoMaster Pro - GitHub发布助手")
    print("=" * 50)
    
    # 检查Git
    if not run_cmd("git --version"):
        print("❌ 请先安装Git: https://git-scm.com/")
        return
    
    print("✅ Git已安装")
    
    # 初始化仓库
    if not os.path.exists(".git"):
        print("📁 初始化Git仓库...")
        run_cmd("git init")
        run_cmd("git branch -M main")
    
    # 添加文件
    print("📝 添加项目文件...")
    files_to_add = [
        "README.md",
        "LICENSE", 
        "requirements.txt",
        ".gitignore",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "RELEASE_NOTES.md",
        "videomaster_pro_compact_fixed.py",
        "build_final.py",
        ".github/",
        "setup_github.py"
    ]
    
    for file in files_to_add:
        if os.path.exists(file):
            run_cmd(f"git add {file}")
    
    # 提交
    print("💾 提交更改...")
    run_cmd('git commit -m "feat: VideoMaster Pro v1.0.0 - 专业YouTube下载器"')
    
    print("\n🎯 下一步操作:")
    print("1. 在GitHub上创建新仓库 'videomaster-pro'")
    print("2. 复制仓库URL")
    print("3. 运行以下命令:")
    print("   git remote add origin <你的仓库URL>")
    print("   git push -u origin main")
    print("\n📦 可执行文件位置:")
    print(f"   {os.path.abspath('dist/VideoMaster Pro Complete.exe')}")
    print("\n✨ 项目已准备就绪！")

if __name__ == "__main__":
    main()
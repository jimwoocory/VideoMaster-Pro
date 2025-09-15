#!/usr/bin/env python3
"""
GitHub仓库设置脚本
自动化创建GitHub仓库并推送代码
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令并返回结果"""
    print(f"执行命令: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return None

def check_git():
    """检查Git是否安装"""
    result = run_command("git --version", check=False)
    if result and result.returncode == 0:
        print("✓ Git已安装")
        return True
    else:
        print("✗ Git未安装，请先安装Git")
        return False

def check_gh_cli():
    """检查GitHub CLI是否安装"""
    result = run_command("gh --version", check=False)
    if result and result.returncode == 0:
        print("✓ GitHub CLI已安装")
        return True
    else:
        print("✗ GitHub CLI未安装")
        print("请访问 https://cli.github.com/ 安装GitHub CLI")
        return False

def init_git_repo():
    """初始化Git仓库"""
    if not os.path.exists(".git"):
        print("初始化Git仓库...")
        run_command("git init")
        run_command("git branch -M main")
    else:
        print("✓ Git仓库已存在")

def create_gitignore_if_needed():
    """确保.gitignore文件存在且包含必要内容"""
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        print("✓ .gitignore文件已存在")
    else:
        print("创建.gitignore文件...")
        # .gitignore内容已经在前面创建了

def add_and_commit():
    """添加文件并提交"""
    print("添加文件到Git...")
    
    # 添加主要文件
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
        ".github/"
    ]
    
    for file in files_to_add:
        if os.path.exists(file):
            run_command(f"git add {file}")
            print(f"✓ 已添加 {file}")
    
    # 检查是否有文件需要提交
    result = run_command("git status --porcelain", check=False)
    if result and result.stdout.strip():
        print("提交更改...")
        run_command('git commit -m "Initial commit: VideoMaster Pro v1.0.0"')
        print("✓ 文件已提交")
    else:
        print("✓ 没有新的更改需要提交")

def create_github_repo(repo_name, description):
    """创建GitHub仓库"""
    print(f"创建GitHub仓库: {repo_name}")
    
    # 检查仓库是否已存在
    result = run_command(f"gh repo view {repo_name}", check=False)
    if result and result.returncode == 0:
        print(f"✓ 仓库 {repo_name} 已存在")
        return True
    
    # 创建新仓库
    cmd = f'gh repo create {repo_name} --public --description "{description}" --source=.'
    result = run_command(cmd, check=False)
    
    if result and result.returncode == 0:
        print(f"✓ 成功创建仓库 {repo_name}")
        return True
    else:
        print(f"✗ 创建仓库失败")
        return False

def push_to_github():
    """推送代码到GitHub"""
    print("推送代码到GitHub...")
    
    # 添加远程仓库（如果不存在）
    result = run_command("git remote get-url origin", check=False)
    if result and result.returncode != 0:
        # 需要用户手动添加远程仓库URL
        print("请手动添加远程仓库URL:")
        print("git remote add origin https://github.com/yourusername/videomaster-pro.git")
        return False
    
    # 推送代码
    result = run_command("git push -u origin main", check=False)
    if result and result.returncode == 0:
        print("✓ 代码已推送到GitHub")
        return True
    else:
        print("✗ 推送失败，请检查网络连接和权限")
        return False

def create_release():
    """创建GitHub Release"""
    print("创建GitHub Release...")
    
    # 创建标签
    run_command("git tag v1.0.0")
    run_command("git push origin v1.0.0")
    
    # 创建Release
    cmd = 'gh release create v1.0.0 --title "VideoMaster Pro v1.0.0" --notes-file RELEASE_NOTES.md'
    result = run_command(cmd, check=False)
    
    if result and result.returncode == 0:
        print("✓ Release创建成功")
        return True
    else:
        print("✗ Release创建失败")
        return False

def main():
    """主函数"""
    print("🚀 VideoMaster Pro GitHub设置脚本")
    print("=" * 50)
    
    # 检查必要工具
    if not check_git():
        sys.exit(1)
    
    # GitHub CLI是可选的，但推荐使用
    has_gh_cli = check_gh_cli()
    
    # 设置Git仓库
    init_git_repo()
    create_gitignore_if_needed()
    add_and_commit()
    
    if has_gh_cli:
        # 使用GitHub CLI创建仓库
        repo_name = input("请输入仓库名称 (默认: videomaster-pro): ").strip()
        if not repo_name:
            repo_name = "videomaster-pro"
        
        description = "VideoMaster Pro - 专业YouTube视频下载工具"
        
        if create_github_repo(repo_name, description):
            push_to_github()
            
            # 询问是否创建Release
            create_rel = input("是否创建Release? (y/N): ").strip().lower()
            if create_rel in ['y', 'yes']:
                create_release()
    else:
        print("\n手动设置步骤:")
        print("1. 在GitHub上创建新仓库")
        print("2. 添加远程仓库: git remote add origin <仓库URL>")
        print("3. 推送代码: git push -u origin main")
    
    print("\n✅ 设置完成！")
    print("📁 项目文件已准备就绪")
    print("🌐 可以访问GitHub仓库查看项目")

if __name__ == "__main__":
    main()

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

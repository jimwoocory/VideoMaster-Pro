@echo off
chcp 65001 >nul
title VideoMaster Pro 正式版安装和运行

echo.
echo ========================================
echo   VideoMaster Pro 正式版 v2.0
echo ========================================
echo.

echo 📦 检查和安装依赖...
python -m pip install --upgrade pip
python -m pip install yt-dlp>=2023.12.30
python -m pip install requests>=2.31.0

echo.
echo 🚀 启动 VideoMaster Pro 正式版...
echo.
python videomaster_pro_official.py

pause
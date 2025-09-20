# VideoMaster Pro v2.0 🎬

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![YouTube Music](https://img.shields.io/badge/YouTube%20Music-Supported-red.svg)](https://music.youtube.com/)

> 🎵 **完美支持YouTube Music链接的专业视频下载工具**  
> 完整解决YouTube Music播放列表链接问题，内置FFmpeg工具链

## 🌟 项目亮点

### 🎯 核心修复
- ✅ **YouTube Music链接完全支持** - 智能处理自动播放列表
- ✅ **播放列表智能解析** - 自动提取单个视频ID
- ✅ **复杂参数处理** - 支持所有YouTube链接格式
- ✅ **网络连接优化** - 简化代理设置，增强稳定性

### 🚀 完整功能
- 🎬 **格式查询弹窗** - 可视化选择下载质量
- 📦 **批量下载支持** - 多链接并行处理
- 📋 **下载历史记录** - 完整的下载管理
- 🎨 **现代化界面** - 卡片式设计，用户体验优秀
- 🔧 **内置FFmpeg** - 无需额外安装依赖

## 📥 快速开始

### 方法1：下载可执行文件（推荐）
```bash
# 下载完整版（包含所有依赖）
# 文件大小：158.2 MB
# 直接运行，无需安装Python
```

### 方法2：从源码运行
```bash
# 克隆仓库
git clone https://github.com/your-username/VideoMaster-Pro.git
cd VideoMaster-Pro

# 安装依赖
pip install -r requirements.txt

# 运行程序
python videomaster_pro_official.py
```

### 方法3：一键安装脚本
```bash
# Windows用户
双击运行 setup_and_run.bat
```

## 🎵 YouTube Music支持

### 问题解决
本项目完美解决了YouTube Music链接无法下载的问题：

**支持的链接格式**：
```
# YouTube Music自动播放列表
https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1

# 普通YouTube视频
https://www.youtube.com/watch?v=dQw4w9WgXcQ

# YouTube播放列表
https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMt9xaJGA6H_VjlrBk
```

### 智能处理流程
1. 🔍 **链接分析** - 自动识别链接类型
2. 🎯 **参数提取** - 智能提取视频ID
3. 🔄 **URL清理** - 生成标准下载链接
4. ✅ **信息获取** - 完整的视频元数据

## 🖥️ 界面预览

### 主界面
- 🎬 **视频链接输入** - 支持单个和批量链接
- 🌐 **网络设置** - 简化的代理配置
- 📺 **视频信息显示** - 实时显示视频详情
- ⚙️ **下载设置** - 完整的参数配置

### 格式选择弹窗
- 📋 **格式列表** - 所有可用格式一览
- 💡 **推荐格式** - 智能推荐最佳质量
- 🎯 **双击选择** - 便捷的操作体验

## 🔧 功能特性

### 📥 下载功能
| 功能 | 描述 | 状态 |
|------|------|------|
| 视频下载 | 支持所有YouTube视频格式 | ✅ |
| 音频提取 | 高质量音频下载 | ✅ |
| 字幕下载 | 自动和手动字幕 | ✅ |
| 批量下载 | 多链接并行处理 | ✅ |
| 断点续传 | 网络中断自动恢复 | ✅ |

### 🎨 用户体验
| 功能 | 描述 | 状态 |
|------|------|------|
| 现代化界面 | 卡片式设计 | ✅ |
| 实时进度 | 下载进度实时显示 | ✅ |
| 错误诊断 | 智能错误分析和建议 | ✅ |
| 历史记录 | 完整的下载历史 | ✅ |
| 启动画面 | 专业的启动体验 | ✅ |

### 🌐 网络支持
| 功能 | 描述 | 状态 |
|------|------|------|
| 代理支持 | HTTP/HTTPS代理 | ✅ |
| 直连模式 | 无代理直接连接 | ✅ |
| 智能重试 | 网络失败自动重试 | ✅ |
| 超时控制 | 可配置的连接超时 | ✅ |

## 📦 版本说明

### v2.0 完整版特性
- 🎵 **YouTube Music修复** - 完全解决播放列表问题
- 📦 **内置FFmpeg** - 包含完整工具链
- 🚀 **性能优化** - 增强网络连接稳定性
- 🎨 **界面升级** - 现代化用户体验

### 文件结构
```
VideoMaster-Pro/
├── 📁 源码版本/
│   ├── videomaster_pro_official.py     # 主程序
│   ├── requirements.txt                # 依赖列表
│   └── setup_and_run.bat              # 一键运行脚本
├── 📁 可执行版本/
│   ├── VideoMaster_Pro_Complete.exe   # 完整版(158.2MB)
│   └── VideoMaster_Pro_Complete_Portable/ # 便携版
├── 📁 工具链/
│   ├── ffmpeg.exe                      # 视频处理(167.3MB)
│   ├── ffprobe.exe                     # 媒体分析(167.1MB)
│   └── yt-dlp.exe                      # 下载引擎(17.5MB)
└── 📁 打包脚本/
    ├── build_complete_with_ffmpeg.py   # 完整打包
    ├── build_official.py               # 标准打包
    └── quick_build.py                  # 快速打包
```

## 🛠️ 安装指南

### 系统要求
- **操作系统**: Windows 10/11 (32位/64位)
- **Python版本**: 3.8+ (源码运行)
- **磁盘空间**: 至少 1GB 可用空间
- **网络**: 支持HTTP/HTTPS连接

### 依赖安装
```bash
# 核心依赖
pip install yt-dlp>=2023.12.30
pip install requests>=2.31.0

# 打包依赖（可选）
pip install pyinstaller>=6.0.0
```

### 网络配置
```python
# 代理设置示例
proxy_url = "http://127.0.0.1:7897"  # Clash默认端口
proxy_url = "http://127.0.0.1:7890"  # V2Ray默认端口
proxy_url = "http://127.0.0.1:1080"  # Shadowsocks默认端口
```

## 📖 使用教程

### 基础使用
1. **启动程序**
   ```bash
   # 可执行版本
   双击 VideoMaster_Pro_Complete.exe
   
   # 源码版本
   python videomaster_pro_official.py
   ```

2. **输入链接**
   - 单个链接：粘贴到顶部输入框
   - 批量链接：每行一个链接到批量输入框

3. **网络配置**
   - 有代理：勾选"使用代理"，输入代理地址
   - 无代理：取消勾选"使用代理"

4. **获取信息**
   ```
   点击"获取信息" → 查看视频详情
   点击"查询格式" → 选择下载质量
   点击"分析链接" → 查看链接结构（可选）
   ```

5. **开始下载**
   - 设置保存路径
   - 选择格式ID
   - 配置其他选项
   - 点击"开始下载"

### 高级功能

#### YouTube Music链接处理
```python
# 自动播放列表链接
input_url = "https://www.youtube.com/watch?v=VIDEO_ID&list=RD...&start_radio=1"

# 程序自动处理流程：
# 1. 识别播放列表类型 (RD前缀 = YouTube Music)
# 2. 提取视频ID (VIDEO_ID)
# 3. 生成清理后的链接
# 4. 正常下载处理
```

#### 格式选择策略
```python
# 推荐格式
"bv*+ba/b"      # 最佳视频+最佳音频
"best"          # 最高质量单文件
"worst"         # 最低质量（节省空间）

# 自定义格式
"137+140"       # 1080p视频 + 128k音频
"22"            # 720p MP4格式
"18"            # 360p MP4格式
```

#### 批量下载配置
```python
# 线程数设置
threads = 4     # 推荐设置
threads = 8     # 高性能设置
threads = 1     # 保守设置

# 转码选项
transcode = True
format = "mp4"  # 输出格式
```

## 🔍 故障排除

### 常见问题

#### 1. 网络连接问题
```
❌ 错误：Connection refused
💡 解决方案：
   1. 检查代理软件是否运行
   2. 尝试切换直连/代理模式
   3. 检查防火墙设置
```

#### 2. YouTube Music链接无法下载
```
❌ 错误：Unable to extract video info
💡 解决方案：
   1. 使用"分析链接"功能检查链接结构
   2. 确保链接完整且有效
   3. 程序会自动处理播放列表参数
```

#### 3. 格式选择问题
```
❌ 错误：Requested format not available
💡 解决方案：
   1. 点击"查询格式"查看可用格式
   2. 使用推荐格式 "bv*+ba/b"
   3. 尝试其他格式ID
```

#### 4. 下载速度慢
```
❌ 问题：下载速度过慢
💡 解决方案：
   1. 增加线程数（4-8个）
   2. 检查网络连接质量
   3. 尝试不同的代理服务器
```

### 错误代码对照表

| 错误代码 | 描述 | 解决方案 |
|----------|------|----------|
| 10061 | 代理连接被拒绝 | 检查代理软件状态 |
| 10060 | 连接超时 | 检查网络连接 |
| 403 | 访问被拒绝 | 尝试使用代理 |
| 404 | 视频不存在 | 检查链接有效性 |

## 🤝 贡献指南

### 开发环境设置
```bash
# 1. 克隆仓库
git clone https://github.com/your-username/VideoMaster-Pro.git
cd VideoMaster-Pro

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 运行测试
python -m pytest tests/
```

### 代码规范
- 使用 Python 3.8+ 语法
- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写单元测试
- 更新文档

### 提交流程
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的YouTube下载库
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理框架
- [tkinter](https://docs.python.org/3/library/tkinter.html) - Python GUI框架
- [requests](https://requests.readthedocs.io/) - HTTP库

## 📞 联系方式

- 📧 **邮箱**: your-email@example.com
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/your-username/VideoMaster-Pro/issues)
- 💬 **讨论**: [GitHub Discussions](https://github.com/your-username/VideoMaster-Pro/discussions)

## 📊 项目统计

![GitHub stars](https://img.shields.io/github/stars/your-username/VideoMaster-Pro?style=social)
![GitHub forks](https://img.shields.io/github/forks/your-username/VideoMaster-Pro?style=social)
![GitHub issues](https://img.shields.io/github/issues/your-username/VideoMaster-Pro)
![GitHub pull requests](https://img.shields.io/github/issues-pr/your-username/VideoMaster-Pro)

---

<div align="center">

**🎵 VideoMaster Pro v2.0 - 让YouTube Music下载变得简单！**

[⬆ 回到顶部](#videomaster-pro-v20-)

</div>
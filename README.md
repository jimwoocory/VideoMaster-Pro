# VideoMaster Pro - 专业YouTube下载器

<div align="center">

![VideoMaster Pro](https://img.shields.io/badge/VideoMaster-Pro-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows)

**功能强大的YouTube视频下载工具，支持多种格式和高质量下载**

[📥 下载最新版本](https://github.com/yourusername/videomaster-pro/releases) | [📖 使用指南](#使用指南) | [🐛 问题反馈](https://github.com/yourusername/videomaster-pro/issues)

</div>

## ✨ 主要特性

### 🎯 核心功能
- **🎬 视频下载** - 支持YouTube视频/音频下载
- **📋 批量下载** - 支持多个URL同时下载
- **🎵 音频提取** - 高质量音频格式转换
- **📝 字幕下载** - 多语言字幕支持
- **🔄 格式转换** - 内置FFmpeg转码功能

### 🎨 界面特色
- **🚀 启动动画** - 优雅的启动体验
- **📱 现代UI** - 简洁美观的界面设计
- **🎛️ 格式选择** - 智能格式推荐和自定义选择
- **📊 实时进度** - 详细的下载进度显示
- **📜 历史记录** - 完整的下载历史管理

### ⚡ 技术优势
- **🔧 独立运行** - 无需安装Python环境
- **🌐 代理支持** - 支持网络代理配置
- **🧵 多线程** - 高效并发下载
- **💾 轻量级** - 单文件可执行程序

## 📥 快速开始

### 方式一：直接下载（推荐）
1. 前往 [Releases页面](https://github.com/yourusername/videomaster-pro/releases)
2. 下载最新版本的 `VideoMaster Pro Complete.exe`
3. 双击运行即可使用

### 方式二：从源码运行
```bash
# 克隆仓库
git clone https://github.com/yourusername/videomaster-pro.git
cd videomaster-pro

# 安装依赖
pip install -r requirements.txt

# 运行程序
python videomaster_pro_compact_fixed.py
```

## 🎮 使用指南

### 基本使用
1. **输入链接** - 在URL输入框中粘贴YouTube链接
2. **获取信息** - 点击"获取信息"按钮预览视频详情
3. **选择格式** - 点击"查询格式"选择下载质量
4. **开始下载** - 设置保存路径后点击"开始下载"

### 高级功能
- **批量下载**: 在多行文本框中输入多个URL
- **代理设置**: 配置网络代理以突破地域限制
- **格式自定义**: 使用yt-dlp格式ID进行精确控制
- **转码功能**: 下载后自动转换为指定格式

### 格式说明
| 格式ID | 说明 | 推荐用途 |
|--------|------|----------|
| `bv*+ba/b` | 最佳视频+音频 | 通用下载 |
| `bestvideo+bestaudio` | 最高质量 | 高质量收藏 |
| `worst` | 最低质量 | 节省空间 |
| `bestaudio` | 仅音频 | 音乐下载 |

## 🛠️ 开发说明

### 项目结构
```
videomaster-pro/
├── videomaster_pro_compact_fixed.py  # 主程序文件
├── build_final.py                    # 打包脚本
├── requirements.txt                  # Python依赖
├── yt-dlp.exe                       # YouTube下载工具
├── ffmpeg.zip                       # 视频处理工具
├── dist/                            # 编译输出目录
│   └── VideoMaster Pro Complete.exe # 可执行文件
└── docs/                            # 文档目录
```

### 技术栈
- **GUI框架**: Tkinter + TTK
- **下载引擎**: yt-dlp
- **视频处理**: FFmpeg
- **打包工具**: PyInstaller
- **编程语言**: Python 3.8+

### 构建说明
```bash
# 安装构建依赖
pip install pyinstaller

# 执行构建
python build_final.py
```

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10/11 (64位)
- **内存**: 4GB RAM
- **存储空间**: 200MB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Windows 11 (64位)
- **内存**: 8GB+ RAM
- **存储空间**: 1GB+ 可用空间
- **网络**: 高速宽带连接

## 🔧 常见问题

### Q: 下载失败怎么办？
A: 请检查网络连接，必要时配置代理服务器。

### Q: 支持哪些视频网站？
A: 主要支持YouTube，基于yt-dlp引擎支持1000+网站。

### Q: 如何提高下载速度？
A: 增加线程数量，使用稳定的网络连接。

### Q: 程序无法启动？
A: 确保系统满足最低要求，关闭杀毒软件重试。

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 如何贡献
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献类型
- 🐛 Bug修复
- ✨ 新功能开发
- 📝 文档改进
- 🎨 界面优化
- 🔧 性能提升

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载引擎
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理框架
- [PyInstaller](https://pyinstaller.org/) - Python打包工具

## 📞 联系我们

- 📧 邮箱: jimwoo.cory@gmail.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/yourusername/videomaster-pro/issues)
- 💬 讨论: [GitHub Discussions](https://github.com/yourusername/videomaster-pro/discussions)

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐ Star！**

Made with ❤️ by VideoMaster Pro Team

</div>

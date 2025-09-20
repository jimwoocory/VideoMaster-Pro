# VideoMaster Pro 完整版 v2.0

## 🎬 完整功能版本

这是包含所有依赖的完整版本，内置了以下组件：
- ✅ FFmpeg.exe (167.3 MB) - 视频处理核心
- ✅ FFprobe.exe (167.1 MB) - 媒体信息分析
- ✅ yt-dlp.exe (17.5 MB) - YouTube下载引擎
- ✅ 所有Python依赖库

## 🚀 使用方法

### 直接运行
双击 `VideoMaster_Pro_Complete.exe` 即可启动程序

### 功能特性
✅ **YouTube Music完整支持**
- 支持YouTube Music自动播放列表
- 智能提取单个视频ID
- 自动处理复杂链接参数

✅ **完整下载功能**
- 格式查询和选择弹窗
- 批量下载支持
- 字幕下载
- 多线程下载
- 视频转码功能

✅ **网络配置**
- 简化代理设置 (端口7897)
- 智能连接模式
- 详细错误诊断

✅ **用户体验**
- 现代化界面设计
- 下载历史记录
- 实时进度显示
- 启动画面

## 🔧 网络配置

### 代理设置
如果使用代理软件：
1. 确保代理软件正在运行
2. 勾选"使用代理"
3. 输入代理地址：`http://127.0.0.1:7897`

### 直连模式
如果可以直接访问YouTube：
- 取消勾选"使用代理"选项

## 🎵 YouTube Music链接支持

完全支持YouTube Music链接，包括：
```
https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1
```

程序会自动：
- 识别YouTube Music播放列表
- 提取单个视频进行处理
- 显示详细链接分析

## 📋 使用步骤

1. **启动程序**：双击 VideoMaster_Pro_Complete.exe
2. **输入链接**：粘贴YouTube或YouTube Music链接
3. **分析链接**：点击"分析链接"查看结构（可选）
4. **获取信息**：点击"获取信息"查看视频详情
5. **选择格式**：点击"查询格式"选择下载质量
6. **配置设置**：设置保存路径和其他选项
7. **开始下载**：点击"开始下载"

## 🛠️ 故障排除

### 网络问题
- 检查代理软件状态
- 尝试切换直连/代理模式
- 查看程序日志获取详细错误信息

### 下载问题
- 确保保存路径有写入权限
- 检查磁盘空间是否充足
- 尝试不同的格式ID

## 📦 文件说明

- `VideoMaster_Pro_Complete.exe` - 主程序（158.2 MB，包含所有依赖）
- `ffmpeg/` - FFmpeg工具备份文件夹
  - `ffmpeg.exe` - 视频处理工具 (167.3 MB)
  - `ffprobe.exe` - 媒体信息工具 (167.1 MB)
  - `yt-dlp.exe` - YouTube下载工具 (17.5 MB)

## 🔒 安全说明

本程序完全开源，不包含任何恶意代码：
- 仅用于合法的视频下载
- 不收集用户隐私信息
- 所有网络请求均为YouTube API调用

## 📊 版本信息

- **版本**: 2.0 完整版
- **构建日期**: 2025-09-20
- **文件大小**: 158.2 MB (主程序)
- **总包大小**: 约 510 MB (包含所有工具)

## 🎯 测试建议

推荐使用以下链接测试功能：
```
https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1
```

这是一个YouTube Music自动播放列表链接，完美展示了程序的修复效果。

---
VideoMaster Pro 完整版 v2.0
包含FFmpeg和所有依赖的完整解决方案
# 贡献指南

感谢您对 VideoMaster Pro 项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题
如果您发现了bug或有功能建议：

1. 检查 [Issues](https://github.com/yourusername/videomaster-pro/issues) 确保问题未被报告
2. 使用适当的issue模板创建新issue
3. 提供详细的描述和复现步骤
4. 如果可能，请附上截图或错误日志

### 提交代码
1. **Fork** 本仓库到您的GitHub账户
2. **Clone** 您的fork到本地
   ```bash
   git clone https://github.com/yourusername/videomaster-pro.git
   cd videomaster-pro
   ```
3. 创建新的功能分支
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. 进行您的更改
5. 测试您的更改
6. 提交更改
   ```bash
   git add .
   git commit -m "Add: 简短描述您的更改"
   ```
7. 推送到您的fork
   ```bash
   git push origin feature/your-feature-name
   ```
8. 创建 **Pull Request**

## 📝 代码规范

### Python代码风格
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用4个空格进行缩进
- 行长度不超过88字符
- 使用有意义的变量和函数名

### 提交信息格式
使用以下格式编写提交信息：
```
类型: 简短描述

详细描述（可选）

相关issue: #123
```

**提交类型**：
- `Add`: 新增功能
- `Fix`: 修复bug
- `Update`: 更新现有功能
- `Remove`: 删除功能
- `Refactor`: 重构代码
- `Docs`: 文档更新
- `Style`: 代码格式调整
- `Test`: 测试相关

### 示例
```
Add: 支持批量URL下载功能

- 添加多行文本输入框
- 实现URL解析和验证
- 支持并发下载队列

相关issue: #15
```

## 🧪 测试

### 运行测试
```bash
# 安装测试依赖
pip install -r requirements-dev.txt

# 运行单元测试
python -m pytest tests/

# 运行集成测试
python test_integration.py
```

### 测试要求
- 新功能必须包含相应的测试
- 确保所有现有测试通过
- 测试覆盖率应保持在80%以上

## 📋 开发环境设置

### 环境要求
- Python 3.8+
- Git
- 推荐使用虚拟环境

### 设置步骤
```bash
# 克隆仓库
git clone https://github.com/yourusername/videomaster-pro.git
cd videomaster-pro

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行程序
python videomaster_pro_compact_fixed.py
```

## 🎯 贡献领域

我们特别欢迎以下方面的贡献：

### 🐛 Bug修复
- 下载失败问题
- 界面显示异常
- 性能问题
- 兼容性问题

### ✨ 新功能
- 支持更多视频网站
- 高级下载选项
- 界面主题定制
- 下载管理功能

### 📚 文档改进
- 使用教程
- API文档
- 代码注释
- 翻译工作

### 🎨 界面优化
- UI/UX改进
- 响应式设计
- 无障碍功能
- 主题支持

## 🔍 代码审查

所有的Pull Request都会经过代码审查：

### 审查标准
- 代码质量和可读性
- 功能正确性
- 测试覆盖率
- 文档完整性
- 性能影响

### 审查流程
1. 自动化测试检查
2. 代码质量分析
3. 人工代码审查
4. 功能测试验证
5. 合并到主分支

## 📞 获取帮助

如果您在贡献过程中遇到问题：

- 📧 发送邮件: your.email@example.com
- 💬 GitHub Discussions: [讨论区](https://github.com/yourusername/videomaster-pro/discussions)
- 🐛 创建Issue: [问题反馈](https://github.com/yourusername/videomaster-pro/issues)

## 🏆 贡献者

感谢所有为项目做出贡献的开发者！

<!-- 贡献者列表将自动更新 -->

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT许可证](LICENSE) 下发布。

---

再次感谢您的贡献！每一个贡献都让 VideoMaster Pro 变得更好。 🎉
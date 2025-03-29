# 🐱 Discord 黑猫语音管理机器人

一个功能强大的 Discord 语音频道管理机器人，使用斜杠命令来管理语音频道中用户的静音状态。

## ✨ 特性

- 🎯 使用现代的斜杠命令（Slash Commands）
- 🔒 安全的权限控制
- 🚀 快速响应和错误处理
- 🛠 简单易用的命令系统

## 📋 可用命令

| 命令 | 描述 | 所需权限 |
|------|------|---------|
| `/mute` | 将指定语音频道中的所有用户静音 | 静音成员 |
| `/unmute` | 取消指定语音频道中所有用户的静音 | 静音成员 |
| `/quit` | 让机器人离开当前所在的语音频道 | 无 |

## 🚀 部署指南

### 前置要求

- Python 3.8 或更高版本
- pip（Python 包管理器）
- Discord 机器人令牌

### 📥 安装步骤

1. 克隆仓库：
   ```bash
   git clone https://github.com/你的用户名/DiscordBot_BlackCatManager.git
   cd DiscordBot_BlackCatManager
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 创建并配置环境变量文件：
   ```bash
   # 创建 .env 文件并添加以下内容
   DISCORD_TOKEN=你的机器人令牌
   TEST_GUILD_ID=你的测试服务器ID（可选）
   ```

### ⚙️ Discord 开发者门户设置

1. 访问 [Discord 开发者门户](https://discord.com/developers/applications)
2. 点击 "New Application"
3. 进入 "Bot" 部分，启用以下特权网关意图：
   - Server Members Intent
   - Voice State Intent
4. 复制令牌并粘贴到 `.env` 文件中

## 🎮 运行机器人

```bash
python bot.py
```

## 🛡️ 所需权限

确保在将机器人添加到服务器时授予以下权限：

- 查看频道
- 连接语音频道
- 静音成员
- 使用斜杠命令

## ⚠️ 注意事项

- 确保机器人具有适当的服务器权限
- 斜杠命令可能需要几分钟到一小时才能在所有服务器中同步
- 建议在测试服务器中先测试机器人功能

## 🤝 贡献

欢迎贡献代码和提出建议！请随时提交 Pull Request 或创建 Issue。

## 📄 许可证

此项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
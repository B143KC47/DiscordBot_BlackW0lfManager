# 🎭 Discord 黑猫语音管理机器人

一个专注于语音频道管理的 Discord 机器人，提供精确的用户静音控制和定时解除功能。

## ⚡ 核心功能

### 频道静音管理
- `/mutechannel` - 一键静音整个语音频道的所有成员
- `/unmutechannel` - 一键解除频道内所有成员的静音状态

### 个人静音管理
- `/mute` - 对指定用户进行定时静音，支持多种时间单位
- `/unmute` - 手动解除指定用户的静音状态

## 🌟 特色功能

- 🔄 支持定时自动解除静音
- 🎯 智能的状态检测和错误处理
- 🔒 完善的权限管理系统
- 💬 详细的操作反馈
- 📝 完整的日志记录功能

## 🛠️ 部署指南

### 环境要求
- Python 3.8+
- Discord.py 2.0.0+
- python-dotenv

### 快速开始

1. **克隆仓库**
```bash
git clone https://github.com/你的用户名/DiscordBot_BlackCatManager.git
cd DiscordBot_BlackCatManager
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
创建 `.env` 文件并填写以下内容：
```env
DISCORD_TOKEN=你的机器人Token
TEST_GUILD_ID=测试服务器ID（可选）
```

4. **启动机器人**
```bash
python bot.py
```

## 📖 命令使用说明

### 定时静音指令
| 命令 | 参数 | 描述 | 示例 |
|------|------|------|------|
| `/mute` | member: 目标用户<br>duration: 静音时长 | 临时静音指定用户 | `/mute @用户 5m` |

### 时长格式说明
支持的时间单位：
- `s`: 秒
- `m`: 分钟
- `h`: 小时
- `d`: 天

示例：`30s`、`5m`、`1h`、`1d`

### 频道管理指令
| 命令 | 参数 | 描述 |
|------|------|------|
| `/mutechannel` | channel: 目标频道 | 静音整个语音频道 |
| `/unmutechannel` | channel: 目标频道 | 解除频道静音 |

## ⚙️ 权限设置

### 机器人所需权限
- 查看频道
- 连接语音频道
- 静音成员
- 使用应用程序命令

### 命令执行权限
- 所有静音相关命令需要用户具有"静音成员"权限

## ⚠️ 注意事项

- 机器人需要较高的服务器角色以管理成员
- 需要在 Discord 开发者平台启用以下特权网关意图：
  - Server Members Intent
  - Voice States Intent
  - Message Content Intent（推荐）
- 静音命令仅对语音频道中的用户有效
- 定时静音在机器人重启后不会保留

## 🤝 参与贡献

欢迎提交问题和建议！请遵循以下步骤：

1. Fork 本项目
2. 创建您的特性分支
3. 提交您的更改
4. 推送到分支
5. 创建一个 Pull Request

## 📄 开源协议

本项目采用 MIT 许可证

---
Made with ❤️ by [你的名字]
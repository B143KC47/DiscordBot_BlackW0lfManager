# 静音管理模组

模块化的Discord机器人，用于管理语音频道，具有强大的静音管理功能。

## 功能特点

- **频道静音管理**：使用单个命令静音或取消静音语音频道中的所有用户
- **用户静音管理**：为特定用户设置指定时长的静音（例如：30秒，5分钟，1小时，1天）
- **自动解除静音**：用户在指定时间后自动解除静音
- **模块化架构**：易于扩展新功能

## 命令列表

### 频道管理
- `/mutechannel` - 静音指定语音频道中的所有用户
- `/unmutechannel` - 取消静音指定语音频道中的所有用户

### 用户管理
- `/mute <用户> <时长>` - 对特定用户进行指定时长的静音（格式：30s, 5m, 1h, 1d）
- `/unmute <用户>` - 立即取消特定用户的静音

## 安装方法

1. 克隆此仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 将 `.env.example` 复制为 `.env` 并添加你的Discord机器人令牌
4. 运行机器人：`python bot.py`

## 系统要求

- Python 3.8+
- discord.py 2.0+
- 必需的Discord机器人意图：VOICE_STATES（语音状态）, SERVER_MEMBERS（服务器成员）

## 配置选项

编辑 `.env` 文件以配置以下内容：
- `DISCORD_TOKEN`（必需）：你的Discord机器人令牌
- `TEST_GUILD_ID`（可选）：用于在特定服务器中测试斜杠命令

## 所需权限

机器人需要以下Discord权限：
- 管理频道（Manage Channels）
- 静音成员（Mute Members）
- 连接到语音频道（Connect to Voice Channels）

## 参与贡献

欢迎贡献！模块化架构使添加新功能变得容易。

## 许可证

本项目采用MIT许可证 - 详情请参阅LICENSE文件。

[English Documentation](README.md)
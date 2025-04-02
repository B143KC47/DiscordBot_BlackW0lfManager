# Mute Manager

A modular Discord bot for managing voice channels, with powerful mute management capabilities.

[中文文档](README.CN.md)

## Features

- **Channel Mute Management**: Mute or unmute all users in a voice channel with a single command
- **User Mute Management**: Mute specific users for a defined duration (e.g., 30s, 5m, 1h, 1d)
- **Automatic Unmute**: Users are automatically unmuted after the specified duration
- **Modular Architecture**: Easily extendable with new features

## Commands

### Channel Management
- `/mutechannel` - Mute all users in a specified voice channel
- `/unmutechannel` - Unmute all users in a specified voice channel

### User Management
- `/mute <user> <duration>` - Mute a specific user for a set duration (format: 30s, 5m, 1h, 1d)
- `/unmute <user>` - Immediately unmute a specific user

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your Discord bot token
4. Run the bot: `python bot.py`

## Requirements

- Python 3.8+
- discord.py 2.0+
- Required Discord Bot Intents: VOICE_STATES, SERVER_MEMBERS

## Configuration

Edit the `.env` file to configure the following:
- `DISCORD_TOKEN` (required): Your Discord bot token
- `TEST_GUILD_ID` (optional): For testing slash commands in a specific server

## Permissions

The bot requires the following Discord permissions:
- Manage Channels
- Mute Members
- Connect to Voice Channels

## Contributing

Contributions are welcome! The modular architecture makes it easy to add new features.

## License

This project is licensed under the MIT License - see the LICENSE file for details.


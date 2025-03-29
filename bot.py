import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import traceback # 用于打印更详细的错误堆栈

# 加载环境变量
load_dotenv()

# 设置机器人权限
intents = discord.Intents.default()
# intents.message_content = True # 斜杠命令通常不需要消息内容意图，除非你有其他基于消息的功能
intents.voice_states = True  # 必须，用于访问语音状态和频道成员
intents.members = True     # 推荐启用，确保能获取所有成员信息，特别是大型服务器

# 创建机器人实例
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} 已连接到Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    # 使用 bot 内置的 tree 进行同步
    try:
        # --- 测试时建议使用服务器同步 ---
        test_guild_id = os.getenv("TEST_GUILD_ID") # 尝试从环境变量读取测试服务器ID
        if test_guild_id:
            try:
                test_guild_id = int(test_guild_id)
                guild = discord.Object(id=test_guild_id)
                await bot.tree.sync(guild=guild)
                print(f'斜杠命令已同步到测试服务器 {test_guild_id}!')
            except ValueError:
                 print("警告: TEST_GUILD_ID 环境变量不是有效的数字ID，将尝试全局同步。")
                 synced = await bot.tree.sync()
                 print(f'已同步 {len(synced)} 个斜杠命令到全局 (可能需要时间生效)!')
            except discord.NotFound:
                 print(f"错误: 找不到 ID 为 {test_guild_id} 的测试服务器。请检查 TEST_GUILD_ID。将尝试全局同步。")
                 synced = await bot.tree.sync()
                 print(f'已同步 {len(synced)} 个斜杠命令到全局 (可能需要时间生效)!')
        else:
            # --- 全局同步 ---
            # 注意：全局同步可能需要长达一小时才能在所有服务器上完全生效。
            print("未找到 TEST_GUILD_ID 环境变量，正在进行全局同步...")
            synced = await bot.tree.sync()
            print(f'已同步 {len(synced)} 个斜杠命令到全局 (可能需要时间生效)!')

    except Exception as e:
        print(f"同步斜杠命令时出错: {e}")
        traceback.print_exc() # 打印详细的错误堆栈信息

# --- 斜杠命令实现 (使用 @bot.tree 装饰器) ---

@bot.tree.command(name="mute", description="将指定语音频道中的所有用户（除机器人外）静音")
@app_commands.describe(channel="选择要静音用户的语音频道")
@app_commands.checks.has_permissions(mute_members=True)
async def mute(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """将指定语音频道中的所有用户静音"""
    # !! 关键优化：立即响应交互，防止超时 !!
    # ephemeral=True 使 "机器人正在思考..." 的提示仅自己可见
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not isinstance(channel, discord.VoiceChannel):
        # 使用 followup 发送错误信息，因为已经 defer 了
        await interaction.followup.send("提供的参数必须是一个语音频道。", ephemeral=True)
        return

    muted_count = 0
    error_messages = []
    members_to_mute = [m for m in channel.members if m != interaction.guild.me and not m.voice.mute] # 预先筛选

    if not members_to_mute:
        await interaction.followup.send(f"频道 {channel.mention} 中没有需要静音的用户。", ephemeral=True)
        return

    for member in members_to_mute:
        try:
            await member.edit(mute=True, reason=f"由 {interaction.user} 执行 /mute 命令")
            muted_count += 1
        except discord.Forbidden:
            error_messages.append(f"❌ 没有权限静音 {member.display_name}")
        except Exception as e:
            error_messages.append(f"⚠️ 静音 {member.display_name} 时出错: {type(e).__name__}")
            print(f"静音 {member.display_name} ({member.id}) 时出错: {e}") # 打印详细错误到控制台

    response_message = f"✅ 在频道 {channel.mention} 中，成功将 {muted_count} 名用户静音。"
    if error_messages:
        response_message += "\n**未能静音的用户:**\n" + "\n".join(error_messages)

    # 使用 followup 发送最终结果
    await interaction.followup.send(response_message, ephemeral=True)

@bot.tree.command(name="unmute", description="取消指定语音频道中所有用户（除机器人外）的静音")
@app_commands.describe(channel="选择要取消静音用户的语音频道")
@app_commands.checks.has_permissions(mute_members=True)
async def unmute(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """取消指定语音频道中所有用户的静音"""
    # !! 关键优化：立即响应交互，防止超时 !!
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not isinstance(channel, discord.VoiceChannel):
        await interaction.followup.send("提供的参数必须是一个语音频道。", ephemeral=True)
        return

    unmuted_count = 0
    error_messages = []
    members_to_unmute = [m for m in channel.members if m != interaction.guild.me and m.voice.mute] # 预先筛选

    if not members_to_unmute:
        await interaction.followup.send(f"频道 {channel.mention} 中没有需要取消静音的用户。", ephemeral=True)
        return

    for member in members_to_unmute:
        try:
            await member.edit(mute=False, reason=f"由 {interaction.user} 执行 /unmute 命令")
            unmuted_count += 1
        except discord.Forbidden:
            error_messages.append(f"❌ 没有权限为 {member.display_name} 取消静音")
        except Exception as e:
            error_messages.append(f"⚠️ 为 {member.display_name} 取消静音时出错: {type(e).__name__}")
            print(f"取消静音 {member.display_name} ({member.id}) 时出错: {e}")

    response_message = f"✅ 在频道 {channel.mention} 中，成功为 {unmuted_count} 名用户取消静音。"
    if error_messages:
        response_message += "\n**未能取消静音的用户:**\n" + "\n".join(error_messages)

    # 使用 followup 发送最终结果
    await interaction.followup.send(response_message, ephemeral=True)

@bot.tree.command(name="quit", description="让机器人离开当前所在的语音频道")
async def quit_channel(interaction: discord.Interaction):
    """让机器人离开当前语音频道"""
    # 这个命令通常很快，不一定需要 defer，但加上也没坏处
    await interaction.response.defer(ephemeral=True)

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        channel_name = voice_client.channel.name # 记录频道名称以便回复
        await voice_client.disconnect(force=False) # force=False 优雅断开
        await interaction.followup.send(f"已离开语音频道: {channel_name}", ephemeral=True)
    else:
        await interaction.followup.send("我当前没有加入任何语音频道!", ephemeral=True)

# --- 斜杠命令的通用错误处理 (使用 @bot.tree.error 装饰器) ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """处理斜杠命令执行过程中发生的错误"""
    error_message = "执行命令时发生了一个未知错误。" # 默认错误消息
    log_error = True # 是否在控制台打印错误

    if isinstance(error, app_commands.errors.MissingPermissions):
        missing_perms = ", ".join(error.missing_permissions)
        error_message = f"❌ 你没有执行此命令所需的权限: `{missing_perms}`"
        log_error = False # 权限错误通常不需要记录完整堆栈
    elif isinstance(error, app_commands.errors.CommandNotFound):
         error_message = "🤔 未找到该命令。可能是命令尚未同步或已被移除。"
         log_error = False
    elif isinstance(error, app_commands.errors.CommandInvokeError):
        original = error.original
        print(f"命令 '{interaction.command.name if interaction.command else '未知'}' 执行失败:")
        traceback.print_exception(type(original), original, original.__traceback__) # 打印原始错误的完整堆栈
        if isinstance(original, discord.Forbidden):
             error_message = f"❌ 机器人缺少执行此操作所需的权限。请检查机器人的角色权限 ({type(original).__name__})。"
        elif isinstance(original, discord.HTTPException):
             error_message = f"网络错误：与 Discord API 通信时出现问题 ({original.status} - {original.code})。请稍后再试。"
        else:
             error_message = f"⚙️ 执行命令时发生内部错误: {type(original).__name__}。管理员请查看控制台日志。"
    elif isinstance(error, app_commands.errors.CheckFailure):
         # 包括 has_permissions 失败（虽然上面已经有 MissingPermissions 处理了）和其他自定义检查失败
         error_message = "🚫 你不满足执行此命令的条件。"
         log_error = False
    elif isinstance(error, app_commands.errors.TransformerError):
         # 参数转换错误，例如用户提供了无效的频道
         error_message = f"参数错误：无法处理你提供的 '{error.value}' 作为 '{error.param.name}' 参数。请确保输入有效。"
    else:
        # 其他未明确处理的 app_commands 错误
        error_message = f"命令处理出错: {type(error).__name__}"

    if log_error:
        print(f"未处理的斜杠命令错误 ({type(error).__name__}): {error}")
        # 可以考虑在这里加入更详细的日志记录

    # 尝试发送错误消息给用户
    try:
        if interaction.response.is_done():
            # 如果已经 defer 或响应过，使用 followup
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            # 否则，直接响应
            await interaction.response.send_message(error_message, ephemeral=True)
    except discord.InteractionResponded:
         # 极其罕见的情况：在检查 is_done() 和发送之间，交互已被响应
         try:
             await interaction.followup.send(error_message, ephemeral=True) # 再次尝试 followup
         except Exception as e:
             print(f"尝试发送错误消息时再次失败: {e}")
    except Exception as e:
        print(f"发送错误消息给用户时发生异常: {e}")


# 运行机器人
if __name__ == "__main__": # 好的实践：将运行代码放在 main guard 下
    try:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("错误: 未在 .env 文件或环境变量中找到 DISCORD_TOKEN")
        else:
            print("正在启动机器人...")
            bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n" + "="*60)
        print("错误: 缺少必要的特权网关意图 (Privileged Gateway Intents)!")
        print("请访问 Discord 开发者门户 (https://discord.com/developers/applications/)")
        print("1. 选择你的应用程序 (Bot)")
        print("2. 点击侧边栏的 'Bot' 选项卡")
        print("3. 向下滚动到 'Privileged Gateway Intents' 部分")
        print("4. 确保 'SERVER MEMBERS INTENT' 和 'VOICE STATE INTENT' 已启用 (开关是蓝色的)")
        print("   (如果你的机器人需要读取消息内容，也请启用 'MESSAGE CONTENT INTENT')")
        print("5. 点击页面底部的 'Save Changes' 按钮")
        print("6. 重启机器人。")
        print("="*60 + "\n")
    except discord.errors.LoginFailure:
         print("\n" + "="*60)
         print("错误: 无法登录 - 无效的 Token!")
         print("请检查你的 .env 文件或环境变量中的 DISCORD_TOKEN 是否正确。")
         print("Token 通常是一长串字母、数字和符号的组合。")
         print("确保没有多余的空格或字符。")
         print("="*60 + "\n")
    except Exception as e:
        print(f"\n启动机器人时发生未预料的错误: {e}")
        traceback.print_exc()
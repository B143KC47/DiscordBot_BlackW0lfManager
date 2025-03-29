import discord
from discord.ext import commands, tasks # tasks might be useful later, but asyncio is key
from discord import app_commands
import os
from dotenv import load_dotenv
import traceback # 用于打印更详细的错误堆栈
import re # For parsing duration
import asyncio # For timed unmute
from datetime import timedelta, datetime # For calculating time

# 加载环境变量
load_dotenv()

# 设置机器人权限
intents = discord.Intents.default()
intents.voice_states = True  # 必须，用于访问语音状态和频道成员
intents.members = True     # 推荐启用，确保能获取所有成员信息

# 创建机器人实例
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Helper Function to Parse Duration ---
def parse_duration(duration_str: str) -> timedelta | None:
    """
    Parses a duration string like "30s", "5m", "1h", "1d".
    Returns a timedelta object or None if parsing fails.
    """
    match = re.fullmatch(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    
    value, unit = int(match.group(1)), match.group(2)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    return None # Should not be reached with the regex, but good practice

# Dictionary to keep track of timed mutes (simple in-memory version)
# Key: (guild_id, member_id), Value: asyncio.Task
timed_mute_tasks = {}

async def unmute_after_delay(member: discord.Member, delay: float, interaction: discord.Interaction):
    """Coroutine to unmute a member after a delay."""
    await asyncio.sleep(delay)
    
    # --- Important: Re-fetch member object as the state might have changed ---
    # Check if the task is still relevant (e.g., wasn't manually unmuted/cancelled)
    task_key = (member.guild.id, member.id)
    if task_key not in timed_mute_tasks:
        # Task was likely cancelled by a manual unmute or another command
        print(f"Timed unmute task for {member.display_name} ({member.id}) cancelled or already completed.")
        return
        
    # Attempt to fetch the member again from the guild
    guild = interaction.guild # Use the guild from the original interaction context
    if not guild: # Should ideally not happen if interaction is valid
         print(f"Error: Could not find guild for timed unmute of {member.id}")
         del timed_mute_tasks[task_key]
         return
         
    fresh_member = guild.get_member(member.id)

    if fresh_member and fresh_member.voice and fresh_member.voice.mute:
        try:
            await fresh_member.edit(mute=False, reason="自动解除临时静音")
            print(f"自动为 {fresh_member.display_name} ({fresh_member.id}) 解除静音。")
            # Optionally send a DM or log it
            # await interaction.followup.send(f"已自动为 {fresh_member.mention} 解除静音。", ephemeral=True) # Followup might fail if interaction token expired
        except discord.Forbidden:
            print(f"权限不足，无法自动为 {fresh_member.display_name} ({fresh_member.id}) 解除静音。")
            # Optionally notify an admin
        except discord.HTTPException as e:
             print(f"网络错误，无法自动为 {fresh_member.display_name} ({fresh_member.id}) 解除静音: {e}")
        except Exception as e:
            print(f"自动解除静音时发生未知错误 for {fresh_member.display_name} ({fresh_member.id}): {e}")
            traceback.print_exc()
    elif fresh_member and fresh_member.voice and not fresh_member.voice.mute:
        print(f"{fresh_member.display_name} ({fresh_member.id}) 已被手动解除静音。")
    elif not fresh_member:
         print(f"用户 {member.id} 在自动解除静音前已离开服务器。")
    else: # Not in voice channel
        print(f"{fresh_member.display_name} ({fresh_member.id}) 在自动解除静音前已离开语音频道。")
        
    # Clean up the task entry regardless of outcome
    if task_key in timed_mute_tasks:
        del timed_mute_tasks[task_key]


@bot.event
async def on_ready():
    print(f'{bot.user.name} 已连接到Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    try:
        test_guild_id = os.getenv("TEST_GUILD_ID")
        if test_guild_id:
            try:
                test_guild_id = int(test_guild_id)
                guild = discord.Object(id=test_guild_id)
                await bot.tree.sync(guild=guild)
                print(f'斜杠命令已同步到测试服务器 {test_guild_id}!')
            except (ValueError, discord.NotFound):
                 print("警告/错误: TEST_GUILD_ID 无效或找不到服务器，将尝试全局同步。")
                 synced = await bot.tree.sync()
                 print(f'已同步 {len(synced)} 个斜杠命令到全局 (可能需要时间生效)!')
        else:
            print("未找到 TEST_GUILD_ID 环境变量，正在进行全局同步...")
            synced = await bot.tree.sync()
            print(f'已同步 {len(synced)} 个斜杠命令到全局 (可能需要时间生效)!')

    except Exception as e:
        print(f"同步斜杠命令时出错: {e}")
        traceback.print_exc()

# --- 斜杠命令实现 ---

# --- Channel Mute/Unmute (Renamed) ---

@bot.tree.command(name="mutechannel", description="将指定语音频道中的所有用户（除机器人外）静音")
@app_commands.describe(channel="选择要静音用户的语音频道")
@app_commands.checks.has_permissions(mute_members=True)
async def mutechannel(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """将指定语音频道中的所有用户静音"""
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not isinstance(channel, discord.VoiceChannel):
        await interaction.followup.send("提供的参数必须是一个语音频道。", ephemeral=True)
        return

    muted_count = 0
    error_messages = []
    # Filter out members already muted or the bot itself
    members_to_mute = [m for m in channel.members if m != interaction.guild.me and (not m.voice or not m.voice.mute)]

    if not members_to_mute:
        await interaction.followup.send(f"频道 {channel.mention} 中没有需要静音的用户。", ephemeral=True)
        return

    for member in members_to_mute:
        # Double check if they are still in a voice state before muting
        if member.voice:
            try:
                await member.edit(mute=True, reason=f"由 {interaction.user} 执行 /mutechannel 命令")
                muted_count += 1
            except discord.Forbidden:
                error_messages.append(f"❌ 没有权限静音 {member.display_name}")
            except Exception as e:
                error_messages.append(f"⚠️ 静音 {member.display_name} 时出错: {type(e).__name__}")
                print(f"静音 {member.display_name} ({member.id}) 时出错: {e}")
        else:
             error_messages.append(f"ℹ️ {member.display_name} 在尝试静音前离开了语音频道。")


    response_message = f"✅ 在频道 {channel.mention} 中，尝试为 {len(members_to_mute)} 名用户静音，成功 {muted_count} 名。"
    if error_messages:
        response_message += "\n**详情:**\n" + "\n".join(error_messages)

    await interaction.followup.send(response_message, ephemeral=True)

@bot.tree.command(name="unmutechannel", description="取消指定语音频道中所有用户（除机器人外）的静音")
@app_commands.describe(channel="选择要取消静音用户的语音频道")
@app_commands.checks.has_permissions(mute_members=True)
async def unmutechannel(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """取消指定语音频道中所有用户的静音"""
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not isinstance(channel, discord.VoiceChannel):
        await interaction.followup.send("提供的参数必须是一个语音频道。", ephemeral=True)
        return

    unmuted_count = 0
    error_messages = []
    # Filter members who are actually muted and not the bot
    members_to_unmute = [m for m in channel.members if m != interaction.guild.me and m.voice and m.voice.mute]

    if not members_to_unmute:
        await interaction.followup.send(f"频道 {channel.mention} 中没有需要取消静音的用户。", ephemeral=True)
        return

    for member in members_to_unmute:
         # Double check if they are still in a voice state and muted
        if member.voice and member.voice.mute:
            try:
                await member.edit(mute=False, reason=f"由 {interaction.user} 执行 /unmutechannel 命令")
                unmuted_count += 1
                # If there was a timed mute task for this user, cancel it
                task_key = (member.guild.id, member.id)
                if task_key in timed_mute_tasks:
                    timed_mute_tasks[task_key].cancel()
                    del timed_mute_tasks[task_key]
                    print(f"取消了 {member.display_name} 的定时解除静音任务 (手动解除)。")
            except discord.Forbidden:
                error_messages.append(f"❌ 没有权限为 {member.display_name} 取消静音")
            except Exception as e:
                error_messages.append(f"⚠️ 为 {member.display_name} 取消静音时出错: {type(e).__name__}")
                print(f"取消静音 {member.display_name} ({member.id}) 时出错: {e}")
        else:
             error_messages.append(f"ℹ️ {member.display_name} 在尝试解除静音前已离开语音或已被解除静音。")


    response_message = f"✅ 在频道 {channel.mention} 中，尝试为 {len(members_to_unmute)} 名用户取消静音，成功 {unmuted_count} 名。"
    if error_messages:
        response_message += "\n**详情:**\n" + "\n".join(error_messages)

    await interaction.followup.send(response_message, ephemeral=True)


# --- User Mute/Unmute (New) ---

@bot.tree.command(name="mute", description="静音指定用户一段时间 (例如: 30s, 5m, 1h, 1d)")
@app_commands.describe(
    member="要静音的用户",
    duration="静音时长 (格式: 数字 + 单位 s/m/h/d, 例如 10m)"
)
@app_commands.checks.has_permissions(mute_members=True)
async def mute_user(interaction: discord.Interaction, member: discord.Member, duration: str):
    """Mutes a specific user for a specified duration."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    # 1. Check if target is the bot itself or the command issuer
    if member == interaction.guild.me:
        await interaction.followup.send("😅 我不能静音我自己。", ephemeral=True)
        return
    # Optional: Prevent self-muting?
    # if member == interaction.user:
    #     await interaction.followup.send("🤔 你确定要静音你自己吗？请使用服务器的静音功能。", ephemeral=True)
    #     return

    # 2. Check if member is in a voice channel
    if not member.voice or not member.voice.channel:
        await interaction.followup.send(f"{member.mention} 当前不在任何语音频道中。", ephemeral=True)
        return

    # 3. Check if member is already muted
    if member.voice.mute:
        await interaction.followup.send(f"{member.mention} 已经被静音了。", ephemeral=True)
        return

    # 4. Parse Duration
    delta = parse_duration(duration)
    if delta is None:
        await interaction.followup.send("无效的时长格式。请使用例如 `30s`, `5m`, `1h`, `1d` 的格式。", ephemeral=True)
        return
        
    total_seconds = delta.total_seconds()
    if total_seconds <= 0:
        await interaction.followup.send("时长必须是正数。", ephemeral=True)
        return
        
    # Limit duration? (e.g., max 1 day)
    # max_duration = timedelta(days=1).total_seconds()
    # if total_seconds > max_duration:
    #     await interaction.followup.send("最大静音时长为 1 天。", ephemeral=True)
    #     return

    # 5. Perform Mute and Schedule Unmute
    task_key = (interaction.guild.id, member.id)
    
    # Cancel any existing timed unmute task for this user before creating a new one
    if task_key in timed_mute_tasks:
        timed_mute_tasks[task_key].cancel()
        del timed_mute_tasks[task_key]
        print(f"取消了 {member.display_name} 的旧定时解除静音任务 (新静音命令)。")

    try:
        reason = f"由 {interaction.user} 执行 /mute 命令，时长: {duration}"
        await member.edit(mute=True, reason=reason)

        # Schedule the unmute task
        unmute_task = asyncio.create_task(unmute_after_delay(member, total_seconds, interaction))
        timed_mute_tasks[task_key] = unmute_task

        await interaction.followup.send(f"✅ 已将 {member.mention} 静音，持续时间: {duration}。", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send(f"❌ 权限不足，无法静音 {member.mention}。", ephemeral=True)
    except discord.HTTPException as e:
         await interaction.followup.send(f"网络错误，无法静音 {member.mention}: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 静音 {member.mention} 时发生未知错误。", ephemeral=True)
        print(f"静音用户 {member.display_name} ({member.id}) 时出错: {e}")
        traceback.print_exc()
        # Clean up task if mute failed but task was potentially created
        if task_key in timed_mute_tasks:
             timed_mute_tasks[task_key].cancel() # Attempt to cancel
             del timed_mute_tasks[task_key]


@bot.tree.command(name="unmute", description="立即取消指定用户的语音静音")
@app_commands.describe(member="要取消静音的用户")
@app_commands.checks.has_permissions(mute_members=True)
async def unmute_user(interaction: discord.Interaction, member: discord.Member):
    """Unmutes a specific user immediately."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    # 1. Check if target is the bot itself
    if member == interaction.guild.me:
        await interaction.followup.send("我没有被静音。", ephemeral=True)
        return

    # 2. Check if member is in a voice channel
    if not member.voice or not member.voice.channel:
        await interaction.followup.send(f"{member.mention} 当前不在任何语音频道中。", ephemeral=True)
        return

    # 3. Check if member is actually muted
    if not member.voice.mute:
        await interaction.followup.send(f"{member.mention} 没有被静音。", ephemeral=True)
        return

    # 4. Perform Unmute
    task_key = (interaction.guild.id, member.id)
    try:
        reason = f"由 {interaction.user} 执行 /unmute 命令"
        await member.edit(mute=False, reason=reason)

        # If there was a timed mute task, cancel it as we are manually unmuting
        if task_key in timed_mute_tasks:
            timed_mute_tasks[task_key].cancel()
            del timed_mute_tasks[task_key]
            print(f"取消了 {member.display_name} 的定时解除静音任务 (手动解除)。")

        await interaction.followup.send(f"✅ 已为 {member.mention} 取消静音。", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send(f"❌ 权限不足，无法为 {member.mention} 取消静音。", ephemeral=True)
    except discord.HTTPException as e:
         await interaction.followup.send(f"网络错误，无法为 {member.mention} 取消静音: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 为 {member.mention} 取消静音时发生未知错误。", ephemeral=True)
        print(f"取消静音用户 {member.display_name} ({member.id}) 时出错: {e}")
        traceback.print_exc()


# --- REMOVED quit command ---
# @bot.tree.command(name="quit", description="让机器人离开当前所在的语音频道")
# async def quit_channel(interaction: discord.Interaction):
#     """让机器人离开当前语音频道"""
#     await interaction.response.defer(ephemeral=True)
#     voice_client = interaction.guild.voice_client
#     if voice_client and voice_client.is_connected():
#         channel_name = voice_client.channel.name
#         await voice_client.disconnect(force=False)
#         await interaction.followup.send(f"已离开语音频道: {channel_name}", ephemeral=True)
#     else:
#         await interaction.followup.send("我当前没有加入任何语音频道!", ephemeral=True)


# --- 斜杠命令的通用错误处理 ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """处理斜杠命令执行过程中发生的错误"""
    error_message = "执行命令时发生了一个未知错误。"
    log_error = True

    if isinstance(error, app_commands.errors.MissingPermissions):
        missing_perms = ", ".join(error.missing_permissions)
        error_message = f"❌ 你没有执行此命令所需的权限: `{missing_perms}`"
        log_error = False
    elif isinstance(error, app_commands.errors.CommandNotFound):
         error_message = "🤔 未找到该命令。可能是命令尚未同步或已被移除。"
         log_error = False
    elif isinstance(error, app_commands.errors.CommandInvokeError):
        original = error.original
        print(f"命令 '{interaction.command.name if interaction.command else '未知'}' 执行失败:")
        traceback.print_exception(type(original), original, original.__traceback__)
        if isinstance(original, discord.Forbidden):
             error_message = f"❌ 机器人缺少执行此操作所需的权限。请检查机器人的角色权限 ({type(original).__name__})。"
        elif isinstance(original, discord.HTTPException):
             error_message = f"网络错误：与 Discord API 通信时出现问题 ({original.status} - {original.code})。请稍后再试。"
        else:
             error_message = f"⚙️ 执行命令时发生内部错误: {type(original).__name__}。管理员请查看控制台日志。"
    elif isinstance(error, app_commands.errors.CheckFailure):
         error_message = "🚫 你不满足执行此命令的条件。"
         log_error = False
    elif isinstance(error, app_commands.errors.TransformerError):
         # Specific handling for MemberNotFound might be useful if needed
         if isinstance(error.original, commands.MemberNotFound):
              error_message = f"参数错误：找不到名为 '{error.value}' 的用户。"
         else:
              error_message = f"参数错误：无法处理你提供的 '{error.value}' 作为 '{error.param.name}' 参数 ({type(error.original).__name__})。请确保输入有效。"
    elif isinstance(error, app_commands.errors.CommandOnCooldown):
         error_message = f"⏳ 命令冷却中，请在 {error.retry_after:.2f} 秒后重试。"
         log_error = False
    else:
        error_message = f"命令处理出错: {type(error).__name__}"

    if log_error:
        print(f"未处理的斜杠命令错误 ({type(error).__name__}): {error}")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
    except discord.InteractionResponded:
         try:
             await interaction.followup.send(error_message, ephemeral=True)
         except Exception as e_inner:
             print(f"尝试发送错误消息时再次失败: {e_inner}")
    except Exception as e:
        print(f"发送错误消息给用户时发生异常: {e}")


# 运行机器人
if __name__ == "__main__":
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
        print("请确保在 Discord 开发者门户中启用了 'SERVER MEMBERS INTENT' 和 'VOICE STATE INTENT'。")
        print("="*60 + "\n")
    except discord.errors.LoginFailure:
         print("\n" + "="*60)
         print("错误: 无法登录 - 无效的 Token!")
         print("请检查你的 DISCORD_TOKEN。")
         print("="*60 + "\n")
    except Exception as e:
        print(f"\n启动机器人时发生未预料的错误: {e}")
        traceback.print_exc()
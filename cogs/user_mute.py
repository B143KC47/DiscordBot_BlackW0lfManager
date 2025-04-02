import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import traceback
from utils.time_parser import parse_duration

class UserMuteCog(commands.Cog):
    """User mute related commands"""
    
    def __init__(self, bot):
        self.bot = bot

    async def unmute_after_delay(self, member: discord.Member, delay: float, interaction: discord.Interaction):
        """Unmute member after a delay"""
        await asyncio.sleep(delay)
        
        # Important: Re-fetch member as their state may have changed
        # Check if the task is still relevant (e.g., not manually unmuted/cancelled)
        task_key = (member.guild.id, member.id)
        if task_key not in self.bot.timed_mute_tasks:
            # Task might have been manually unmuted or cancelled by other commands
            print(f"Timed unmute task for {member.display_name} ({member.id}) was cancelled or completed.")
            return
            
        # Try to get member from guild
        guild = interaction.guild
        if not guild:
            print(f"Error: Could not find guild to timed unmute {member.id}")
            del self.bot.timed_mute_tasks[task_key]
            return
            
        fresh_member = guild.get_member(member.id)

        if fresh_member and fresh_member.voice and fresh_member.voice.mute:
            try:
                await fresh_member.edit(mute=False, reason="Automatic temporary unmute")
                print(f"Automatically unmuted {fresh_member.display_name} ({fresh_member.id}).")
            except discord.Forbidden:
                print(f"Insufficient permissions to automatically unmute {fresh_member.display_name} ({fresh_member.id}).")
            except discord.HTTPException as e:
                print(f"Network error unmuting {fresh_member.display_name} ({fresh_member.id}): {e}")
            except Exception as e:
                print(f"Unknown error during auto unmute for {fresh_member.display_name} ({fresh_member.id}): {e}")
                traceback.print_exc()
        elif fresh_member and fresh_member.voice and not fresh_member.voice.mute:
            print(f"{fresh_member.display_name} ({fresh_member.id}) was manually unmuted.")
        elif not fresh_member:
            print(f"User {member.id} left the server before auto unmute.")
        else:
            print(f"{fresh_member.display_name} ({fresh_member.id}) left voice channel before auto unmute.")
            
        # Clean up task entry regardless of outcome
        if task_key in self.bot.timed_mute_tasks:
            del self.bot.timed_mute_tasks[task_key]

    @app_commands.command(name="mute", description="Mute a user for a specified duration (e.g., 30s, 5m, 1h, 1d)")
    @app_commands.describe(
        member="User to mute",
        duration="Duration (format: number + unit s/m/h/d, e.g., 10m)"
    )
    @app_commands.checks.has_permissions(mute_members=True)
    async def mute_user(self, interaction: discord.Interaction, member: discord.Member, duration: str):
        """Mute a specific user for a set duration"""
        await interaction.response.defer(ephemeral=True, thinking=True)

        # 1. Check if target is bot itself
        if member == interaction.guild.me:
            await interaction.followup.send("😅 I can't mute myself.", ephemeral=True)
            return

        # 2. Check if member is in a voice channel
        if not member.voice or not member.voice.channel:
            await interaction.followup.send(f"{member.mention} is not in a voice channel.", ephemeral=True)
            return

        # 3. Check if member is already muted
        if member.voice.mute:
            await interaction.followup.send(f"{member.mention} is already muted.", ephemeral=True)
            return

        # 4. Parse duration
        delta = parse_duration(duration)
        if delta is None:
            await interaction.followup.send("Invalid duration format. Please use formats like `30s`, `5m`, `1h`, `1d`.", ephemeral=True)
            return
            
        total_seconds = delta.total_seconds()
        if total_seconds <= 0:
            await interaction.followup.send("Duration must be positive.", ephemeral=True)
            return

        # 5. Execute mute and schedule unmute
        task_key = (interaction.guild.id, member.id)
        
        # Cancel any existing timed unmute tasks for this user
        if task_key in self.bot.timed_mute_tasks:
            self.bot.timed_mute_tasks[task_key].cancel()
            del self.bot.timed_mute_tasks[task_key]
            print(f"Cancelled old timed unmute task for {member.display_name} (new mute command).")

        try:
            reason = f"Muted by {interaction.user} using /mute for {duration}"
            await member.edit(mute=True, reason=reason)

            # Schedule unmute task
            unmute_task = asyncio.create_task(self.unmute_after_delay(member, total_seconds, interaction))
            self.bot.timed_mute_tasks[task_key] = unmute_task

            await interaction.followup.send(f"✅ Muted {member.mention} for {duration}.", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send(f"❌ Insufficient permissions to mute {member.mention}.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"Network error muting {member.mention}: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Unknown error while muting {member.mention}.", ephemeral=True)
            print(f"Error muting user {member.display_name} ({member.id}): {e}")
            traceback.print_exc()
            # Clean up task if mute failed but task might have been created
            if task_key in self.bot.timed_mute_tasks:
                self.bot.timed_mute_tasks[task_key].cancel()
                del self.bot.timed_mute_tasks[task_key]

    @app_commands.command(name="unmute", description="Immediately unmute a specific user")
    @app_commands.describe(member="User to unmute")
    @app_commands.checks.has_permissions(mute_members=True)
    async def unmute_user(self, interaction: discord.Interaction, member: discord.Member):
        """Immediately unmute a specific user"""
        await interaction.response.defer(ephemeral=True, thinking=True)

        # 1. Check if target is bot itself
        if member == interaction.guild.me:
            await interaction.followup.send("I'm not muted.", ephemeral=True)
            return

        # 2. Check if member is in a voice channel
        if not member.voice or not member.voice.channel:
            await interaction.followup.send(f"{member.mention} is not in a voice channel.", ephemeral=True)
            return

        # 3. Check if member is actually muted
        if not member.voice.mute:
            await interaction.followup.send(f"{member.mention} is not muted.", ephemeral=True)
            return

        # 4. Execute unmute
        task_key = (interaction.guild.id, member.id)
        try:
            reason = f"Unmuted by {interaction.user} using /unmute"
            await member.edit(mute=False, reason=reason)

            # Cancel any timed unmute task if it exists
            if task_key in self.bot.timed_mute_tasks:
                self.bot.timed_mute_tasks[task_key].cancel()
                del self.bot.timed_mute_tasks[task_key]
                print(f"Cancelled timed unmute task for {member.display_name} (manual unmute).")

            await interaction.followup.send(f"✅ Unmuted {member.mention}.", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send(f"❌ Insufficient permissions to unmute {member.mention}.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"Network error unmuting {member.mention}: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Unknown error while unmuting {member.mention}.", ephemeral=True)
            print(f"Error unmuting user {member.display_name} ({member.id}): {e}")
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(UserMuteCog(bot))
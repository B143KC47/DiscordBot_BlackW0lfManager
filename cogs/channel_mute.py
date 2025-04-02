import discord
from discord.ext import commands
from discord import app_commands
import traceback

class ChannelMuteCog(commands.Cog):
    """Channel mute related commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mutechannel", description="Mute all users (except bots) in a specified voice channel")
    @app_commands.describe(channel="Select a voice channel to mute users in")
    @app_commands.checks.has_permissions(mute_members=True)
    async def mutechannel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Mute all users in a specified voice channel"""
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not isinstance(channel, discord.VoiceChannel):
            await interaction.followup.send("The provided argument must be a voice channel.", ephemeral=True)
            return

        muted_count = 0
        error_messages = []
        # Filter out already muted members and the bot itself
        members_to_mute = [m for m in channel.members if m != interaction.guild.me and (not m.voice or not m.voice.mute)]

        if not members_to_mute:
            await interaction.followup.send(f"No users need to be muted in {channel.mention}.", ephemeral=True)
            return

        for member in members_to_mute:
            # Check if they're still in voice before muting
            if member.voice:
                try:
                    await member.edit(mute=True, reason=f"Muted by {interaction.user} using /mutechannel")
                    muted_count += 1
                except discord.Forbidden:
                    error_messages.append(f"❌ No permission to mute {member.display_name}")
                except Exception as e:
                    error_messages.append(f"⚠️ Error muting {member.display_name}: {type(e).__name__}")
                    print(f"Error muting {member.display_name} ({member.id}): {e}")
            else:
                error_messages.append(f"ℹ️ {member.display_name} left the voice channel before being muted.")

        response_message = f"✅ In {channel.mention}, attempted to mute {len(members_to_mute)} users, {muted_count} successful."
        if error_messages:
            response_message += "\n**Details:**\n" + "\n".join(error_messages)

        await interaction.followup.send(response_message, ephemeral=True)

    @app_commands.command(name="unmutechannel", description="Unmute all users (except bots) in a specified voice channel")
    @app_commands.describe(channel="Select a voice channel to unmute users in")
    @app_commands.checks.has_permissions(mute_members=True)
    async def unmutechannel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Unmute all users in a specified voice channel"""
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not isinstance(channel, discord.VoiceChannel):
            await interaction.followup.send("The provided argument must be a voice channel.", ephemeral=True)
            return

        unmuted_count = 0
        error_messages = []
        # Filter for actually muted members, excluding the bot itself
        members_to_unmute = [m for m in channel.members if m != interaction.guild.me and m.voice and m.voice.mute]

        if not members_to_unmute:
            await interaction.followup.send(f"No users need to be unmuted in {channel.mention}.", ephemeral=True)
            return

        for member in members_to_unmute:
            # Check if they're still in voice and muted
            if member.voice and member.voice.mute:
                try:
                    await member.edit(mute=False, reason=f"Unmuted by {interaction.user} using /unmutechannel")
                    unmuted_count += 1
                    # Cancel any timed unmute task if it exists
                    task_key = (member.guild.id, member.id)
                    if task_key in self.bot.timed_mute_tasks:
                        self.bot.timed_mute_tasks[task_key].cancel()
                        del self.bot.timed_mute_tasks[task_key]
                        print(f"Cancelled timed unmute task for {member.display_name} (manual unmute).")
                except discord.Forbidden:
                    error_messages.append(f"❌ No permission to unmute {member.display_name}")
                except Exception as e:
                    error_messages.append(f"⚠️ Error unmuting {member.display_name}: {type(e).__name__}")
                    print(f"Error unmuting {member.display_name} ({member.id}): {e}")
            else:
                error_messages.append(f"ℹ️ {member.display_name} has already left voice or been unmuted.")

        response_message = f"✅ In {channel.mention}, attempted to unmute {len(members_to_unmute)} users, {unmuted_count} successful."
        if error_messages:
            response_message += "\n**Details:**\n" + "\n".join(error_messages)

        await interaction.followup.send(response_message, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChannelMuteCog(bot))
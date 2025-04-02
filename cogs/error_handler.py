import discord
from discord.ext import commands
from discord import app_commands
import traceback

class ErrorHandlerCog(commands.Cog):
    """Error handling module"""
    
    def __init__(self, bot):
        self.bot = bot
        bot.tree.error(self.on_app_command_error)
        
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors that occur during slash command execution"""
        error_message = "An unknown error occurred while executing the command."
        log_error = True

        if isinstance(error, app_commands.errors.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            error_message = f"❌ You don't have the required permissions: `{missing_perms}`"
            log_error = False
        elif isinstance(error, app_commands.errors.CommandNotFound):
            error_message = "🤔 Command not found. It may not be synced yet or has been removed."
            log_error = False
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            original = error.original
            print(f"Command '{interaction.command.name if interaction.command else 'Unknown'}' failed:")
            traceback.print_exception(type(original), original, original.__traceback__)
            if isinstance(original, discord.Forbidden):
                error_message = f"❌ Bot lacks required permissions. Please check bot role permissions."
            elif isinstance(original, discord.HTTPException):
                error_message = f"Network error: Issue communicating with Discord API ({original.status} - {original.code}). Please try again later."
            else:
                error_message = f"⚙️ Internal error: {type(original).__name__}. Please check console logs."
        elif isinstance(error, app_commands.errors.CheckFailure):
            error_message = "🚫 You don't meet the requirements to use this command."
            log_error = False
        elif isinstance(error, app_commands.errors.TransformerError):
            if isinstance(error.original, commands.MemberNotFound):
                error_message = f"Error: Could not find user '{error.value}'."
            else:
                error_message = f"Invalid parameter: Could not process '{error.value}' as '{error.param.name}'."
        elif isinstance(error, app_commands.errors.CommandOnCooldown):
            error_message = f"⏳ Command on cooldown. Try again in {error.retry_after:.2f} seconds."
            log_error = False
        else:
            error_message = f"Error: {type(error).__name__}"

        if log_error:
            print(f"Unhandled slash command error ({type(error).__name__}): {error}")

        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
        except discord.InteractionResponded:
            try:
                await interaction.followup.send(error_message, ephemeral=True)
            except Exception as e_inner:
                print(f"Failed to send error message (retry): {e_inner}")
        except Exception as e:
            print(f"Failed to send error message: {e}")

async def setup(bot):
    await bot.add_cog(ErrorHandlerCog(bot))
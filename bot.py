import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import traceback
import asyncio

# Load environment variables
load_dotenv()

# Set bot permissions
intents = discord.Intents.default()
intents.voice_states = True  # Required for accessing voice states and channel members
intents.members = True     # Recommended for accessing all member information

class BlackWolfManager(commands.Bot):
    """BlackWolf Manager Discord Bot"""
    
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        # For tracking timed mute tasks, key: (guild_id, member_id), value: asyncio.Task
        self.timed_mute_tasks = {}
        
    async def setup_hook(self):
        """Bot initialization hook for loading Cog modules"""
        # Load all Cog modules
        for cog_file in os.listdir("cogs"):
            if cog_file.endswith(".py"):
                cog_name = cog_file[:-3]  # Remove .py extension
                try:
                    await self.load_extension(f"cogs.{cog_name}")
                    print(f"Loaded module: {cog_name}")
                except Exception as e:
                    print(f"Error loading module {cog_name}: {e}")
                    traceback.print_exc()
    
    async def on_ready(self):
        """Event handler when bot is ready"""
        print(f'{self.user.name} has connected to Discord!')
        print(f'Bot ID: {self.user.id}')
        print('------')
        try:
            test_guild_id = os.getenv("TEST_GUILD_ID")
            if test_guild_id:
                try:
                    test_guild_id = int(test_guild_id)
                    guild = discord.Object(id=test_guild_id)
                    await self.tree.sync(guild=guild)
                    print(f'Slash commands synced to test server {test_guild_id}!')
                except (ValueError, discord.NotFound):
                    print("Warning/Error: TEST_GUILD_ID is invalid or server not found, attempting global sync.")
                    synced = await self.tree.sync()
                    print(f'Synced {len(synced)} slash commands globally (may take time to propagate)!')
            else:
                print("TEST_GUILD_ID environment variable not found, performing global sync...")
                synced = await self.tree.sync()
                print(f'Synced {len(synced)} slash commands globally (may take time to propagate)!')

        except Exception as e:
            print(f"Error syncing slash commands: {e}")
            traceback.print_exc()

# Run the bot
if __name__ == "__main__":
    bot = BlackWolfManager()
    try:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("Error: DISCORD_TOKEN not found in .env file or environment variables")
        else:
            print("Starting bot...")
            bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n" + "="*60)
        print("Error: Missing required Privileged Gateway Intents!")
        print("Please ensure 'SERVER MEMBERS INTENT' and 'VOICE STATE INTENT' are enabled in the Discord Developer Portal.")
        print("="*60 + "\n")
    except discord.errors.LoginFailure:
        print("\n" + "="*60)
        print("Error: Unable to login - Invalid Token!")
        print("Please check your DISCORD_TOKEN.")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\nUnexpected error occurred while starting the bot: {e}")
        traceback.print_exc()
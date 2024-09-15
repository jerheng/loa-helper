import discord
from discord.ext import commands
from cogs.schedule import Schedule
from cogs.gen import Gen
from cogs.remind import Remind
import settings

SYNC = False

class LoaHelperBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.reactions = True    
        intents.guilds = True
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        await self.add_cog(Schedule(self))
        await self.add_cog(Gen(self))
        await self.add_cog(Remind(self))
        print("Cogs Loaded")

    async def on_ready(self):
        print(f"Bot is ready! Logged in as {self.user}")
        print(f"Bot is in {len(self.guilds)} guilds")
        if SYNC:
            try:
                await self.tree.sync()
                print("Synced commands globally")
                
                # Print all registered commands
                commands = await self.tree.fetch_commands()
                print("Registered commands:")
                for command in commands:
                    print(f"- {command.name}")
            except Exception as e:
                print(f"Failed to sync commands globally: {e}")
        else:
            print("Skipping command sync")

def run():
    bot = LoaHelperBot()
    bot.run(settings.DISCORD_API_SECRET)

if __name__ == "__main__":
    run()
import discord
from discord.ext import commands
from cogs.schedule import Schedule
from cogs.gen import Gen
import settings

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

    async def on_ready(self):
        print(f"Bot is ready! Logged in as {self.user}")
        print(f"Bot is in {len(self.guilds)} guilds")
        await self.tree.sync()

def run():
    bot = LoaHelperBot()
    bot.run(settings.DISCORD_API_SECRET)

if __name__ == "__main__":
    run()
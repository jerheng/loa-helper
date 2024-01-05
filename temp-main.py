import settings
import discord
from discord.ext import commands
from datetime import datetime
import pandas as pd

class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents().default()
        intents.message_content = True
        super().__init__(command_prefix="/", intents = intents)
        self.cogslist = ["cogs.schedule"]

    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(ext)
    
    async def on_ready(self):
        print(self.user)
        print(self.user.id)
        print("-" * 8)
        synced = await self.tree.sync()
        print(f"Synced: {len(synced)} Commands")

if __name__ == "__main__":
    client = Client()
    client.run(settings.DISCORD_API_SECRET)

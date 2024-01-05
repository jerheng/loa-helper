import settings
import discord
from discord.ext import commands
from discord import app_commands

class schedule(commands.Cog):
    def __init__(self, client: commands.bot):
        self.client = client
    
    @app_commands.command(name="schedule", description="")
    async def schedule(self, ctx, interaction = discord.Interaction):
        print(
            f"Command /schedule has been called by {ctx.message.author}({ctx.message.author.id}) in {ctx.guild.name}({ctx.guild.id}), channel {ctx.channel}({ctx.channel.id}) at {datetime.now()}"
        )
        await ctx.message.delete()

        emojis = settings.emojis
        msg = await ctx.send("@everyone, please react with your available days!")
        for emoji in emojis:
            await msg.add_reaction(emoji)

async def setup(client:commands.Bot) -> None:
    await client.add_cog(schedule(client))
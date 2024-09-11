import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
from pymongo import MongoClient
import settings

class Gen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(settings.MONGO_URI)
        self.db = self.mongo_client["loa-helper"]
        self.collection = self.db["events"]

    @app_commands.command(name="gen", description="Generate a schedule based on reactions")
    async def gen(self, interaction: discord.Interaction):
        await interaction.response.defer()

        latest_schedule = self.collection.find_one(
            {"channel_id": interaction.channel.id, "status": "Active"},
            sort=[("timestamp", -1)]
        )

        if not latest_schedule:
            await interaction.followup.send("No active scheduling found in this channel.")
            return

        try:
            message = await interaction.channel.fetch_message(latest_schedule["message_id"])
        except discord.NotFound:
            await interaction.followup.send("The scheduled message was not found.")
            return

        user_set, react_dict = await self.collate_table(message)
        conv = self.conv_dict(user_set, react_dict)

        table = [settings.HEADERS]
        for item in conv.items():
            table.append([item[0]] + list(item[1]))

        df = pd.DataFrame(table[1:], columns=table[0])

        embed = discord.Embed(title=f"Schedule {message.jump_url}")
        embed.add_field(name=settings.HEADERS[0], value="\n".join(list(df[settings.HEADERS[0]])), inline=True)
        embed.add_field(name="\u2800".join(settings.EMOJIS), value="\n".join("\u2800".join(row[1:]) for row in table[1:]), inline=True)

        await interaction.followup.send(embed=embed)

    async def collate_table(self, msg):
        user_ids = []
        react_dict = {}
        for reaction in msg.reactions:
            reaction_str = str(reaction)
            if reaction_str in settings.EMOJIS:
                async for user in reaction.users():
                    if user != self.bot.user:
                        if user.id not in user_ids:
                            user_ids.append(user.id)
                        if reaction_str not in react_dict:
                            react_dict[reaction_str] = [user.name]
                        else:
                            react_dict[reaction_str].append(user.name)
        total_users = set(sum(react_dict.values(), []))
        return total_users, react_dict

    def conv_dict(self, user_set, react_dict):
        conv = {}
        for user in user_set:
            conv[user] = ["🟩" if user in react_dict.get(emoji, []) else "🟥" for emoji in settings.EMOJIS]
        return conv

async def setup(bot):
    await bot.add_cog(Gen(bot))
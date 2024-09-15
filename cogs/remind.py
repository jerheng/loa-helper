import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import settings

class Remind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(settings.MONGO_URI)
        self.db = self.mongo_client["loa-helper"]
        self.collection = self.db["events"]
        print("Remind cog has been loaded")

    @app_commands.command(name="remind", description="Remind everyone in the active thread to react")
    async def remind(self, interaction: discord.Interaction):
        print("Remind command called")
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

        reacted_user_ids = set()
        for reaction in message.reactions:
            async for user in reaction.users():
                if user != self.bot.user:
                    reacted_user_ids.add(user.id)

        role_name = latest_schedule.get("role", "@everyone")
        if role_name == "@everyone":
            if isinstance(interaction.channel, (discord.Thread, discord.TextChannel)):
                role_members = interaction.channel.members
            else:
                await interaction.followup.send("This command can only be used in text channels or threads.")
                return
        else:
            guild_role = discord.utils.get(interaction.guild.roles, name=role_name)
            role_members = guild_role.members if guild_role else []

        role_members = [member for member in role_members if not member.bot]

        non_reacted_users = [member.mention for member in role_members if member.id not in reacted_user_ids]
        
        if non_reacted_users:
            await interaction.followup.send(f"Reminder to react: {', '.join(non_reacted_users)}")
        else:
            await interaction.followup.send("Everyone has already reacted.")

async def setup(bot):
    await bot.add_cog(Remind(bot))
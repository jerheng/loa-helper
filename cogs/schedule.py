import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from pymongo import MongoClient
import settings
from typing import List

class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(settings.MONGO_URI)
        self.db = self.mongo_client["loa-helper"]
        self.collection = self.db["events"]

    @app_commands.command(name="schedule", description="Create a new schedule for raid attendance")
    @app_commands.describe(role="The role to mention (optional, defaults to @everyone)")
    async def schedule(self, interaction: discord.Interaction, role: str = "@everyone"):
        await interaction.response.defer()

        if role == "@everyone":
            mention = "@everyone"
        else:
            guild_role = discord.utils.get(interaction.guild.roles, name=role)
            mention = guild_role.mention if guild_role else "@everyone"

        # Determine the members to be tagged
        if role == "@everyone":
            if isinstance(interaction.channel, discord.Thread):
                role_members = interaction.channel.parent.members
            else:
                role_members = interaction.channel.members
        else:
            guild_role = discord.utils.get(interaction.guild.roles, name=role)
            role_members = guild_role.members if guild_role else []

        # Filter out bots from role_members
        role_members = [member for member in role_members if not member.bot]

        # Add members to the thread if the interaction is in a thread
        if isinstance(interaction.channel, discord.Thread):
            await add_to_thread(interaction.channel, role_members, self.bot.user.id)
        else:
            # Ping members in the channel and delete the message
            remind_members = [member.mention for member in role_members]
            if remind_members:
                add_msg = f"Pinging: {' '.join(remind_members)}"
                print(add_msg)  # Debugging: Log the members being pinged
                temp_msg = await interaction.channel.send(add_msg)
                await temp_msg.delete(delay=1)

        # Send the schedule message
        msg = await interaction.channel.send(f"{mention}, please react with your available days!")

        for emoji in settings.EMOJIS:
            await msg.add_reaction(emoji)

        await msg.pin()

        # Update prior scheduling messages to expired
        self.collection.update_many(
            {"channel_id": interaction.channel.id, "status": "Active"},
            {"$set": {"status": "Expired"}}
        )

        # Save new message details to MongoDB
        message_data = {
            "message_id": msg.id,
            "channel_id": interaction.channel.id,
            "guild_id": interaction.guild.id,
            "author_id": interaction.user.id,
            "timestamp": datetime.utcnow(),
            "status": "Active",
            "role": role  # Save the role mentioned
        }
        self.collection.insert_one(message_data)

        await interaction.followup.send("Schedule created successfully!", ephemeral=True)

    @schedule.autocomplete('role')
    async def role_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        roles = ["@everyone"] + [role.name for role in interaction.guild.roles if role.name != "@everyone"]
        return [
            app_commands.Choice(name=role, value=role)
            for role in roles if current.lower() in role.lower()
        ][:25]  # Discord limits to 25 choices

    @app_commands.command(name="remind", description="Remind everyone in the active thread to react")
    async def remind(self, interaction: discord.Interaction):
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

        # Collect users who have already reacted
        reacted_users = set()
        print(f"Original reacted userset: {reacted_users}")
        for reaction in message.reactions:
            async for user in reaction.users():
                if user != self.bot.user:
                    reacted_users.add(user)
        print(f"Reacted userset: {reacted_users}")

        # Get the role mentioned in the schedule
        role_name = latest_schedule.get("role", "@everyone")
        if role_name == "@everyone":
            if isinstance(interaction.channel, discord.Thread):
                role_members = interaction.channel.parent.members
            elif isinstance(interaction.channel, discord.TextChannel):
                role_members = interaction.channel.members
            else:
                await interaction.followup.send("This command can only be used in text channels or threads.")
                return
        else:
            guild_role = discord.utils.get(interaction.guild.roles, name=role_name)
            role_members = guild_role.members if guild_role else []

        # Filter out bots from role_members
        role_members = [member for member in role_members if not member.bot]
        print(f"Role members after bot filter: {role_members}")

        # Mention users who have not reacted yet and are part of the role
        non_reacted_users = [member.mention for member in role_members if member not in reacted_users]
        print(f"Non-reacted users: {non_reacted_users}")
        if non_reacted_users:
            await interaction.followup.send(f"Reminder to react: {', '.join(non_reacted_users)}")
        else:
            await interaction.followup.send("Everyone has already reacted.")

async def add_to_thread(thread: discord.Thread, role_members: List[discord.Member], bot_user_id: int):
    remind_members = [member.mention for member in role_members if member.id != bot_user_id]
    if remind_members:
        add_msg = f"Adding to thread: {' '.join(remind_members)}"
        print(add_msg)  # Debugging: Log the members being added to the thread
        await thread.send(add_msg, delete_after=1)

async def setup(bot):
    await bot.add_cog(Schedule(bot))